# Tool adapters

ForensiDrive orchestrates tools that already exist. It does not ship new recovery or wipe algorithms.

## Detection

Every adapter calls `command_exists()` before offering a method. Missing tools are shown as unavailable with a plain-language explanation.

## Recovery

| Method | Tool | Role |
| --- | --- | --- |
| Recover common files | `photorec` | Primary file carving when present |
| Alternate common files | `foremost` | Fallback when present |
| Drive structure repair | `testdisk` | Detected but not wired; interactive and unsafe as a one-click GUI |

PhotoRec arguments follow the non-interactive `/cmd` form. Exact partition options can vary by PhotoRec version; if a SystemRescue build rejects the command, capture technical details in the UI and adjust only the adapter.

## Erasure

| Method | Tool | Honest limitation |
| --- | --- | --- |
| Remove drive labels | `wipefs` | Does not overwrite file contents |
| Discard storage | `blkdiscard` | Depends on the drive; not called "secure" |
| Overwrite | `shred` | Slow; not called a guaranteed secure erase |

The GUI never claims that a completed command made recovery impossible.

## Storage inspection

Inspection uses `lsblk -J -b` (JSON). Human-readable `lsblk` tables are not parsed.

## Filesystem close-before-erase

Erase attempts to close accessible files first (`umount` / `udisksctl unmount`) so the user is asked to "close the drive before continuing" instead of seeing mount errors raw.
