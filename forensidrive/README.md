# ForensiDrive

ForensiDrive is an integrated forensic recovery and secure data sanitization platform designed as a graphical control layer for [SystemRescue](https://www.system-rescue.org/) and forensic Linux environments.

---

## Key Capabilities

* **Secure Drive Eraser Module**:
  - Full drive sanitization compliant with **NIST SP 800-88 Rev. 1 (Clear)**, **DoD 5220.22-M (3-Pass & 7-Pass)**, and **Gutmann (35-Pass)**.
  - Automatic SSD/NVMe vs. HDD detection (ROTA awareness) with TRIM/discard recommendation.
  - 3-Gate safety confirmation lock (identity verification, dual checkboxes, manual device path input).
  - Pre-erasure SHA-256 fingerprinting and post-erasure random block verification.

* **Secure File & Folder Eraser Module**:
  - Selective file and directory targeting with batch processing.
  - Automated metadata scrubbing (mat2, exiftool).
  - Secure overwrite and unlinking via shred, srm, wipe, and zero-fallback.
  - Synchronous kernel write cache flushing (sync, drop caches).

* **Advanced File Carving & Recovery Module**:
  - Non-destructive carving from damaged, formatted, or corrupted media via PhotoRec and Foremost.
  - Pre-scan source device SHA-256 fingerprinting.
  - Post-recovery magic-byte file classification (20+ format signatures) and confidence scoring (HIGH / MEDIUM / LOW).
  - Cryptographic item hashing and automated chain_of_custody.json generation.

* **Forensic Reporting & Audit Management System**:
  - Immutable, append-only JSONL audit log (udit.jsonl).
  - Standalone, self-contained HTML forensic reports for erasures, recoveries, and file destructions.
  - Integrated UI Audit Viewer for log inspection and report opening.

---

## Running ForensiDrive

### On Linux / SystemRescue
`ash
python3 app/main.py
`

### On Windows / Development Demo Mode
`ash
set FORENSIDRIVE_DEMO=1
python app/main.py
`

### Running Automated Test Suite
`ash
python -m unittest discover -s tests -v
`
