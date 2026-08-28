"""Magic-byte file classifier with confidence scoring for recovered files."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FileClassification:
    path: str
    detected_type: str          # e.g. "image/jpeg", "application/pdf", "unknown"
    confidence: str             # "HIGH" | "MEDIUM" | "LOW"
    size_bytes: int = 0
    valid_structure: bool = False
    extension_match: bool = False
    category: str = ""          # "images" | "documents" | "archives" | "executables" | "unknown"


@dataclass
class ClassificationReport:
    total_files: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    file_classifications: List[FileClassification] = field(default_factory=list)


# Magic bytes registry: (magic_bytes, offset) -> (mime_type, category, extension)
MAGIC_SIGNATURES: List[Tuple[bytes, int, str, str, str]] = [
    # Images
    (b"\xff\xd8\xff",           0, "image/jpeg",        "images",      ".jpg"),
    (b"\x89PNG\r\n\x1a\n",     0, "image/png",         "images",      ".png"),
    (b"GIF87a",                 0, "image/gif",         "images",      ".gif"),
    (b"GIF89a",                 0, "image/gif",         "images",      ".gif"),
    (b"BM",                     0, "image/bmp",         "images",      ".bmp"),
    (b"\x49\x49\x2a\x00",      0, "image/tiff",        "images",      ".tif"),
    (b"\x4d\x4d\x00\x2a",      0, "image/tiff",        "images",      ".tif"),
    (b"RIFF",                   0, "image/webp",        "images",      ".webp"),  # with WEBP at 8
    # Documents
    (b"%PDF-",                  0, "application/pdf",   "documents",   ".pdf"),
    (b"\xd0\xcf\x11\xe0",      0, "application/msword","documents",   ".doc"),
    (b"PK\x03\x04",            0, "application/zip",   "archives",    ".zip"),  # also docx/xlsx
    # Archives
    (b"\x1f\x8b",              0, "application/gzip",  "archives",    ".gz"),
    (b"BZh",                   0, "application/bzip2", "archives",    ".bz2"),
    (b"7z\xbc\xaf'\x1c",      0, "application/7zip",  "archives",    ".7z"),
    (b"Rar!\x1a\x07",          0, "application/rar",   "archives",    ".rar"),
    # Executables
    (b"MZ",                    0, "application/exe",   "executables", ".exe"),
    (b"\x7fELF",               0, "application/elf",   "executables", ""),
    # Video
    (b"\x00\x00\x00\x18ftyp", 0, "video/mp4",         "video",       ".mp4"),
    (b"FLV\x01",               0, "video/flv",         "video",       ".flv"),
    # Audio
    (b"ID3",                   0, "audio/mpeg",        "audio",       ".mp3"),
    (b"RIFF",                   0, "audio/wav",         "audio",       ".wav"),  # with WAVE at 8
]

DOCX_EXTENSIONS = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}


def classify_file(path: str) -> FileClassification:
    """
    Classify one file by reading its magic bytes.
    Returns a FileClassification with confidence and category.
    """
    size = 0
    try:
        size = os.path.getsize(path)
    except OSError:
        return FileClassification(path=path, detected_type="unknown",
                                  confidence="LOW", size_bytes=0, category="unknown")

    header = b""
    try:
        with open(path, "rb") as fh:
            header = fh.read(64)
    except OSError:
        return FileClassification(path=path, detected_type="unknown",
                                  confidence="LOW", size_bytes=size, category="unknown")

    ext = Path(path).suffix.lower()

    for magic, offset, mime, category, expected_ext in MAGIC_SIGNATURES:
        if header[offset:offset + len(magic)] == magic:
            # Refine ZIP: check if extension suggests Office format
            if mime == "application/zip" and ext in DOCX_EXTENSIONS:
                mime = "application/office"
                category = "documents"

            ext_ok = (expected_ext == "") or (ext == expected_ext) or (ext in DOCX_EXTENSIONS and mime == "application/office")
            struct_ok = _validate_structure(header, mime, path)
            confidence = "HIGH" if (ext_ok and struct_ok) else "MEDIUM"
            return FileClassification(
                path=path,
                detected_type=mime,
                confidence=confidence,
                size_bytes=size,
                valid_structure=struct_ok,
                extension_match=ext_ok,
                category=category,
            )

    return FileClassification(path=path, detected_type="unknown",
                              confidence="LOW", size_bytes=size, category="unknown")


def _validate_structure(header: bytes, mime: str, path: str) -> bool:
    """Quick structural check for common types."""
    try:
        if mime == "image/jpeg":
            return header[:2] == b"\xff\xd8" and header[2] == 0xff
        if mime == "image/png":
            return header[4:8] == b"\r\n\x1a\n"
        if mime == "application/pdf":
            return header.startswith(b"%PDF-")
        if mime == "application/zip" or mime == "application/office":
            # Check local file header
            return header[:4] == b"PK\x03\x04"
    except (IndexError, TypeError):
        pass
    return True  # Unknown — assume valid


def classify_directory(folder: str) -> ClassificationReport:
    """Walk folder and classify every file. Returns a ClassificationReport."""
    report = ClassificationReport()
    root = Path(folder)
    try:
        paths = list(root.rglob("*"))
    except OSError:
        return report

    for p in paths:
        if not p.is_file():
            continue
        classification = classify_file(str(p))
        report.total_files += 1
        report.file_classifications.append(classification)
        cat = classification.category or "unknown"
        report.by_category[cat] = report.by_category.get(cat, 0) + 1
        if classification.confidence == "HIGH":
            report.high_confidence += 1
        elif classification.confidence == "MEDIUM":
            report.medium_confidence += 1
        else:
            report.low_confidence += 1

    return report
