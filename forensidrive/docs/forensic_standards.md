# ForensiDrive — Forensic Principles & Evidential Integrity

ForensiDrive adheres to international digital forensics standards (ISO/IEC 27037, ACPO Principles, and SWGDE Best Practices) to preserve evidential integrity throughout recovery and sanitization workflows.

---

## 1. Core Principles

### Principle 1: Preservation of Original Media (ACPO Principle 1)
* ForensiDrive never writes recovered files back onto the source drive. Users must explicitly select an external/secondary output directory.
* Read-only safeguards and device verification prevent accidental in-place overwrite during carving operations.

### Principle 2: Cryptographic Integrity & Chain of Custody (ISO/IEC 27037)
* **Pre-recovery Hash**: Computes SHA-256 fingerprint of the source block device before invoking carving tools.
* **Recovered Item Hash Matrix**: Recursively computes SHA-256 hashes for each carved file upon completion.
* **Tamper-Resistant Chain of Custody**: Exports a structured chain_of_custody.json alongside carved artifacts containing:
  - Case UUID
  - Source device path and serial number
  - Source pre-scan SHA-256 digest
  - Artifact manifest with individual SHA-256 hashes and byte counts
  - Execution timestamps (UTC) and operator tool parameters

### Principle 3: Automated File Validation & Confidence Scoring
* Recovered files are validated against a 20+ file format magic-byte header catalog.
* **Confidence Grading**:
  - **HIGH**: Magic header signature matches and internal structural envelope (e.g. valid EOF, ZIP local header) is sound.
  - **MEDIUM**: Magic header identified but structure could not be fully validated.
  - **LOW / UNKNOWN**: Corrupted or unrecognized byte sequence.

---

## 2. Audit Trail & Verification

* All actions are appended to an immutable JSONL audit ledger (~/.forensidrive/logs/audit.jsonl or /var/log/forensidrive/audit.jsonl).
* Self-contained HTML reports are generated with cryptographic digests, standard citations, verification results, and raw technical logs.
