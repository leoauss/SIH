# SystemRescue integration

ForensiDrive is meant to run after SystemRescue has already started its graphical environment (XFCE on Xorg). It does not replace that environment.

## Intended boot path

1. Power on
2. SystemRescue boots from USB/ISO
3. Graphical environment starts (`global.dostartx: true` in `sysrescue.d` YAML)
4. `gui_autostart` launches ForensiDrive
5. The dashboard is the primary user-facing screen

## Files in this repository

- `systemrescue/config/forensidrive.yaml` — documented `global` and `gui_autostart` fragment to copy into `sysrescue.d/` on the boot device
- `systemrescue/autostart/forensidrive.desktop` — XDG desktop entry used if you copy it into autostart yourself

`gui_autostart` is documented here:

https://www.system-rescue.org/manual/gui_autostart_Start_programs_on_graphical_desktop/

YAML configuration overview:

https://www.system-rescue.org/manual/Configuring_SystemRescue/

## TODO (do not invent extra keys)

- Confirm `python3` path inside your SystemRescue build
- Confirm ForensiDrive is copied to `/usr/local/forensidrive/` in the live filesystem (customize ISO / SRM later)
- Merge `forensidrive.yaml` with any existing `sysrescue.d` files instead of replacing them
- Prefer `gui_autostart.exec` or `gui_autostart.desktop`, not undocumented keys

## Live environment notes

SystemRescue is a live system. The app avoids internet, pip, Docker, databases, systemd services, and home-directory assumptions.
