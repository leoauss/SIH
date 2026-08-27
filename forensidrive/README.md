# ForensiDrive

ForensiDrive is a graphical control layer for [SystemRescue](https://www.system-rescue.org/). It helps a non-technical person inspect drives, recover files using tools already on the live system, and erase a selected drive with repeated confirmation.

It is not a custom Linux desktop, kernel, or display server. SystemRescue still owns drivers, storage access, and low-level utilities.

## Run (SystemRescue or any Linux with Python 3 + Tkinter)

From the project root:

```bash
python3 app/main.py
```

On a Windows PC you can open the dashboard for layout checks. Drive listing needs Linux `lsblk`, or demo data:

```bash
set FORENSIDRIVE_DEMO=1
python app/main.py
```

Press Escape to leave full-screen.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Install later on a live image

Copy the project to `/usr/local/forensidrive/` and use `systemrescue/config/forensidrive.yaml` plus `systemrescue/autostart/forensidrive.desktop` as described in `docs/systemrescue.md`.

## Scope of this prototype

Included: dashboard, inspection, recovery orchestration, erasure with confirmation, SystemRescue placeholders, basic errors.

Deferred: audit, passwords, encrypted audit storage, evidence databases, user accounts.
