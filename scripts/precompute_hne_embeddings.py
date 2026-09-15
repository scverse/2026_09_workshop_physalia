"""Embed the H&E tissue behind every Visium spot with a pathology foundation model.

Instructor-only. Participants load the result from notebooks/day_3/checkpoints and never run
a vision transformer themselves: H-optimus-0 has 1.1B parameters and the teaching server has
no GPU.

    uv run --no-project --python 3.12 \
        --with timm --with torch --with torchvision --with huggingface_hub \
        --with zarr --with pyarrow --with shapely --with pandas --with pillow \
        python scripts/precompute_hne_embeddings.py

Each tile is the axis-aligned bounding box of one spot circle and nothing else: side = 2 x radius
= 76 px = 55 um, centred on the spot. Neighbouring tiles never overlap (Visium spots sit 100 um
apart, centre to centre), so every embedding describes only the tissue the spot measured.

The 76 px crop is resized to the 224 px H-optimus-0 (Bioptimus, Apache-2.0) takes as input. That
puts the tissue in front of the model at ~0.25 um/px, twice the magnification of the 0.5 um/px it
was pretrained at. This is a deliberate choice: spot-exact tiles over native scale. The image
itself is ~0.73 um/px, so no detail is created by the upsampling; the model sees larger, blurrier
nuclei than in training.

The Hugging Face repo is gated; accept the terms once and log in. If access fails, the script
falls back to Phikon-v2 (Owkin, ungated) and records that in the output.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
import torch
import zarr
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PHYSALIA_DATA", "/opt/workshop/data"))
ZARR = DATA / "visium_hne.zarr"
OUT = REPO / "notebooks" / "day_3" / "checkpoints"

SPOT_DIAMETER_UM = 55.0
TILE = 224
BATCH = int(os.environ.get("BATCH", "16"))


def load_spots() -> pd.DataFrame:
    table = pq.read_table(ZARR / "shapes" / "spots" / "shapes.parquet").to_pandas()
    xy = shapely.get_coordinates(shapely.from_wkb(table["geometry"].to_numpy()))
    spots = pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1], "radius": table["radius"].to_numpy()}, index=table.index)
    spots.index.name = "spot_id"
    return spots


def load_image() -> np.ndarray:
    attrs = json.loads((ZARR / "images" / "hne" / "zarr.json").read_text())["attributes"]
    s0 = attrs["ome"]["multiscales"][0]["datasets"][0]["coordinateTransformations"]
    assert s0[0]["scale"] == [1.0, 1.0, 1.0] and s0[1]["translation"] == [0.0, 0.0, 0.0], s0
    img = zarr.open_array(ZARR / "images" / "hne" / "s0", mode="r")[:]  # (c, y, x) uint8, ~400 MB
    return np.moveaxis(img, 0, -1)


def crop(img: np.ndarray, x: float, y: float, size: int) -> Image.Image:
    half = size // 2
    x0, y0 = int(round(x)) - half, int(round(y)) - half
    tile = np.full((size, size, 3), 255, dtype=np.uint8)  # pad with white, like empty slide
    ys, xs = slice(max(y0, 0), min(y0 + size, img.shape[0])), slice(max(x0, 0), min(x0 + size, img.shape[1]))
    tile[ys.start - y0 : ys.stop - y0, xs.start - x0 : xs.stop - x0] = img[ys, xs]
    return Image.fromarray(tile).resize((TILE, TILE), Image.Resampling.BILINEAR)


def load_model(device: str):
    import timm
    from torchvision import transforms

    try:
        model = timm.create_model(
            "hf-hub:bioptimus/H-optimus-0", pretrained=True, init_values=1e-5, dynamic_img_size=False
        )
        mean, std, name = (0.707223, 0.578729, 0.703617), (0.211883, 0.230117, 0.177517), "bioptimus/H-optimus-0"
        forward = model
    except Exception as err:  # gated repo, no token, no network
        print(f"H-optimus-0 unavailable ({type(err).__name__}: {err}); falling back to Phikon-v2", file=sys.stderr)
        from transformers import AutoModel

        model = AutoModel.from_pretrained("owkin/phikon-v2")
        mean, std, name = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), "owkin/phikon-v2"

        def forward(x):
            return model(pixel_values=x).last_hidden_state[:, 0, :]

    model = model.to(device).eval()
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean=mean, std=std)])
    return forward, tf, name


def main() -> None:
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    spots = load_spots()
    radius = spots["radius"].median()
    mpp = SPOT_DIAMETER_UM / (2 * radius)
    crop_px = int(round(2 * radius))  # bounding box of the spot circle
    tile_mpp = crop_px * mpp / TILE
    print(f"{len(spots)} spots, image {mpp:.3f} um/px, cropping {crop_px} px ({crop_px * mpp:.0f} um) -> {TILE} px "
          f"= {tile_mpp:.3f} um/px seen by the model, device {device}")

    img = load_image()
    assert spots["x"].between(0, img.shape[1]).all() and spots["y"].between(0, img.shape[0]).all()
    forward, tf, name = load_model(device)

    feats, t0 = [], time.time()
    with torch.inference_mode():
        for i in range(0, len(spots), BATCH):
            rows = spots.iloc[i : i + BATCH]
            x = torch.stack([tf(crop(img, r.x, r.y, crop_px)) for r in rows.itertuples()]).to(device)
            feats.append(forward(x).float().cpu().numpy())
            if i % (BATCH * 20) == 0:
                print(f"  {i + len(rows)}/{len(spots)} tiles, {time.time() - t0:.0f}s")
    emb = np.concatenate(feats).astype(np.float16)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = name.split("/")[-1].lower().replace("-", "")
    path = OUT / f"visium_hne_{stem}_embeddings.npz"
    np.savez_compressed(
        path,
        spot_id=spots.index.to_numpy().astype(str),
        embedding=emb,
        model=name,
        crop_px=crop_px,
        tile_px=TILE,
        um_per_px=mpp,
        tile_um_per_px=tile_mpp,
    )
    print(f"wrote {path} {emb.shape} in {time.time() - t0:.0f}s, {path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
