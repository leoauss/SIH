"""Chain-of-custody records for forensic recovery sessions."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from core.hashing import hash_device, hash_file


def create_case_id() -> str:
    return str(uuid.uuid4())


def hash_source(
    drive_path: str,
    on_progress=None,
) -> str:
    """SHA-256 of the source device before carving begins."""
    return hash_device(drive_path, algorithm="sha256", on_progress=on_progress)


def hash_destination_tree(folder: str) -> Dict[str, str]:
    """
    SHA-256 of every file under folder.
    Returns {relative_path: sha256_hex}.
    """
    hashes: Dict[str, str] = {}
    root = Path(folder)
    try:
        for path in root.rglob("*"):
            if path.is_file():
                rel = str(path.relative_to(root))
                hashes[rel] = hash_file(str(path))
    except OSError:
        pass
    return hashes


def write_chain_of_custody(
    case_id: str,
    source_path: str,
    source_hash: str,
    dest_hashes: Dict[str, str],
    folder: str,
    tool_used: str = "",
) -> Path:
    """
    Write a chain_of_custody.json to the recovery output folder.
    Returns the path to the written file.
    """
    record = {
        "case_id": case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_device": source_path,
        "source_sha256": source_hash,
        "tool_used": tool_used,
        "recovered_files": [
            {"path": rel, "sha256": digest}
            for rel, digest in sorted(dest_hashes.items())
        ],
        "total_files": len(dest_hashes),
    }
    out_path = Path(folder) / "chain_of_custody.json"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, ensure_ascii=False)
    except OSError:
        pass
    return out_path
