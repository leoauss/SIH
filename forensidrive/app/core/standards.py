"""Named erasure standards. Defines pass counts, patterns, and compliance references."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ErasureStandard:
    id: str
    name: str
    passes: int
    description: str
    reference: str
    verify: bool = True
    pattern_description: str = ""
    suitable_for_ssd: bool = False  # True only for discard/crypto-erase methods


STANDARDS: Dict[str, ErasureStandard] = {
    "single_random": ErasureStandard(
        id="single_random",
        name="Single random pass",
        passes=1,
        description=(
            "Writes one pass of random data over the drive. Fast but not compliant "
            "with any named government or industry standard."
        ),
        reference="None",
        verify=False,
        pattern_description="1x random",
    ),
    "nist_clear": ErasureStandard(
        id="nist_clear",
        name="NIST 800-88 Clear",
        passes=1,
        description=(
            "Overwrites all addressable storage with zeros. Appropriate for media "
            "that will remain within the organisation and not be reused externally."
        ),
        reference="NIST SP 800-88 Rev.1, Section 2.4",
        verify=True,
        pattern_description="1x zeros + verify",
    ),
    "dod_3pass": ErasureStandard(
        id="dod_3pass",
        name="DoD 5220.22-M (3-pass)",
        passes=3,
        description=(
            "Three overwrite passes: zeros, ones, random data, followed by a "
            "verification pass. Meets DoD 5220.22-M (E) sanitisation requirements."
        ),
        reference="DoD 5220.22-M, Section 8-306",
        verify=True,
        pattern_description="0x00 -> 0xFF -> random + verify",
    ),
    "dod_7pass": ErasureStandard(
        id="dod_7pass",
        name="DoD 5220.22-M ECE (7-pass)",
        passes=7,
        description=(
            "Seven overwrite passes as per the extended ECE variant of the DoD standard. "
            "Significantly slower than 3-pass; rarely required by current guidance."
        ),
        reference="DoD 5220.22-M (ECE), Section 8-306",
        verify=True,
        pattern_description="4 rounds of 0x00/0xFF/random + verify",
    ),
    "gutmann": ErasureStandard(
        id="gutmann",
        name="Gutmann (35-pass)",
        passes=35,
        description=(
            "35-pass method designed for older MFM/RLL encoding schemes. "
            "Largely unnecessary for drives manufactured after 2001."
        ),
        reference="Gutmann, P. (1996). Secure Deletion of Data from Magnetic and Solid-State Memory.",
        verify=True,
        pattern_description="35 passes (fixed + random pattern sequence)",
    ),
    "blkdiscard": ErasureStandard(
        id="blkdiscard",
        name="Block Discard (SSD/NVMe TRIM)",
        passes=1,
        description=(
            "Issues a DISCARD command asking the drive firmware to mark all blocks "
            "as unused. Effectiveness depends on the drive. Not a guarantee of erasure."
        ),
        reference="ATA ACS-2 TRIM, NVMe Dataset Management",
        verify=False,
        pattern_description="DISCARD command",
        suitable_for_ssd=True,
    ),
    "wipefs_labels": ErasureStandard(
        id="wipefs_labels",
        name="Remove filesystem signatures only",
        passes=1,
        description=(
            "Clears partition table signatures and filesystem labels. File contents "
            "are not overwritten. Data remains recoverable with carving tools."
        ),
        reference="None",
        verify=False,
        pattern_description="Signature bytes only",
        suitable_for_ssd=True,
    ),
}
