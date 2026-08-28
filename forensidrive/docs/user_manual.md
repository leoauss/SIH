# ForensiDrive — User Manual & Operations Guide

ForensiDrive provides an intuitive, non-technical graphical interface for storage inspection, data recovery, secure sanitization, and audit reporting on SystemRescue.

---

## Navigation & Dashboard

Upon launching, the Home Dashboard presents six primary operations:
1. **Recover Files**: Scan for deleted, corrupted, or formatted files using signature carving.
2. **Erase Drive**: Wipe an entire storage device according to recognized standards (NIST 800-88, DoD 5220.22-M).
3. **Erase Files & Folders**: Selectively shred individual files/folders and scrub metadata traces.
4. **Inspect Drive**: Examine storage geometry, partitions, file systems, mount points, and device serials.
5. **System Information**: View operating system, kernel version, ForensiDrive release, and live tool availability.
6. **View Audit Log**: Browse all historical operations, inspect technical logs, and view/export HTML forensic reports.

---

## 1. Secure Drive Erasure Workflow

1. Click **Erase Drive** and select the target device.
2. Review the detected drive type (SSD vs. HDD) and choose a sanitization standard:
   - **SSD/NVMe**: Block Discard (TRIM)
   - **HDD**: DoD 5220.22-M (3-Pass) or NIST 800-88 Clear (1-Pass Zeroes)
3. Pass the **3-Gate Confirmation Lock**:
   - Verify drive name, serial, and size.
   - Check confirmation checkbox 1: *"I understand all data will be permanently erased."*
   - Check confirmation checkbox 2: *"I have confirmed this is the correct drive."*
   - Type the exact device path (e.g., /dev/sdb) into the verification box.
4. Monitor the **4-Step Execution Pipeline**:
   - Step 1: Source device fingerprinting (SHA-256).
   - Step 2: Live block overwrite stream.
   - Step 3: Post-erasure verification read-back check.
   - Step 4: Audit record committed to disk.

---

## 2. File & Folder Shredding Workflow

1. Click **Erase Files & Folders** and choose the parent drive.
2. Click **Add files** or **Add folder** to queue items for destruction.
3. Select an erase method (shred, srm, wipe, or built-in secure zeroing).
4. Review the target manifest, confirm intent, and begin batch processing.
5. ForensiDrive scrubs embedded metadata (mat2/exiftool), overwrites file data, unlinks inodes, and flushes hardware write caches.

---

## 3. Forensic File Carving & Recovery Workflow

1. Click **Recover Files** and choose the source drive.
2. Select a recovery engine (**PhotoRec** for deep carving or **Foremost** for signature recovery).
3. Choose a dedicated output destination folder (must be on a different drive).
4. Click **Start recovery** to execute the forensic pipeline:
   - Computes source device SHA-256 fingerprint.
   - Streams live carving output.
   - Classifies recovered artifacts by MIME type and computes confidence scores.
   - Exports chain_of_custody.json and updates the forensic audit log.
5. Review the recovery summary and click **Generate Forensic Report** or **Open Output Folder**.
