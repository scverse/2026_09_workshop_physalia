# Before the course — about 10 minutes

The course runs entirely on a server we have prepared for you. **The only thing
you install is VS Code.** No Python, no conda, no R — if you already have them,
they are not used here and you can ignore them.

Please do this **before day 1** so we can fix anything in advance. Doing it on
Monday morning costs everyone teaching time.

---

## 1. Install two things

- [VS Code](https://code.visualstudio.com/download)
- In VS Code open Extensions (`Ctrl+Shift+X`, on macOS `Cmd+Shift+X`), search for
  **Remote - SSH**, and install it.

## 2. Save your key file

Your key was attached to the email from Physalia. It is personal to you.

In VS Code press `Ctrl+Shift+P` (macOS `Cmd+Shift+P`), run
**Remote-SSH: Open SSH Configuration File**, and choose the first option.

Note which folder that file is in, and save your key into **that same folder**
with the name `physalia.pem`.

## 3. Lock down the key's permissions

SSH refuses to use a key that other accounts on your computer could read. This
is the step people most often skip, and it produces a confusing error.

**macOS / Linux** — in a terminal:

```bash
chmod 600 ~/.ssh/physalia.pem
```

**Windows** — in PowerShell:

```powershell
icacls "$env:USERPROFILE\.ssh\physalia.pem" /inheritance:r /grant:r "$env:USERNAME:R"
```

## 4. Add the connection

Back in the SSH configuration file from step 2, paste this at the end and save.
Replace the two placeholders with the values from your email.

```
Host physalia
    HostName <SERVER_ADDRESS>
    User <YOUR_USERNAME>
    IdentityFile ~/.ssh/physalia.pem
    IdentitiesOnly yes
```

## 5. Connect

- `Ctrl+Shift+P` / `Cmd+Shift+P` → **Remote-SSH: Connect to Host** → `physalia`
- If asked whether to trust the host's fingerprint, choose **Continue**
- A new window opens. Wait until the bottom-left corner shows `SSH: physalia`
  (the first connection takes a minute while VS Code sets itself up)

## 6. Open the workshop and check your setup

- **File → Open Folder** → `2026_09_workshop_physalia` → **Open**
  (the folder is already in your home directory — nothing to download)
- Open `notebooks/00_setup_check.ipynb`
- Top right, click the kernel selector and choose **Physalia spatial omics**
- Click **Run All**

The last cell should print:

```
SETUP OK - you are ready for the course.
```

## 7. Tell us it worked

**Reply to the Physalia email with "works"** — or paste the whole status block if
something failed. We would much rather solve it this week than on Monday.

---

## If something goes wrong

**`UNPROTECTED PRIVATE KEY FILE` or `bad permissions`** — step 3 did not take
effect. Check that you ran it on the right path.

**`Permission denied (publickey)`** — the `User` in step 4 does not match the
username in your email, or `IdentityFile` points somewhere else than where you
saved the key.

**Connection times out** — some institutional networks block outgoing SSH
(port 22). Try a different network, such as a phone hotspot. If it only works on
one network, tell us now rather than on Monday.

**The kernel picker has no "Physalia spatial omics"** — you are probably not
connected to the server; check for `SSH: physalia` in the bottom-left corner.

**The notebook runs but imports fail** — the wrong kernel is selected. The setup
check tells you which interpreter it found.

---

## Good to know

- Your home directory on the server is **private to you**. Other participants
  cannot read it.
- The course data lives in `/opt/workshop/data` and is read-only. Write your own
  work inside the `2026_09_workshop_physalia` folder.
- We may push updates to the material. To get them, open a terminal in VS Code
  (`Terminal → New Terminal`) and run `git pull`.
- Everything is reproducible on your own machine afterwards — see the README.
