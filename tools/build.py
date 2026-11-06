"""Build the hardware screen archive using only the Python standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
NAME = "Denon SCLIVE4 Screen"
sys.path.insert(0, str(SRC))
from skin import build_xml  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(output: Path, tag: str | None = None) -> dict:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?", version):
        raise ValueError("VERSION must contain a version such as 2.5.3 or 2.6.0-rc.1")
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"Tag {tag!r} does not match VERSION; expected 'v{version}'")

    xml = build_xml(E.parse(SRC / "dialogs.xml").getroot())
    png = (SRC / f"{NAME}.png").read_bytes()
    root = E.fromstring(xml)
    expected = {"name": "denonsclive4", "width": "1280", "height": "800", "nbdecks": "4", "hidden": "true"}
    if root.tag != "skin" or any(root.get(k) != v for k, v in expected.items()):
        raise ValueError("Generated XML has an invalid hardware-screen identity")
    if not png.startswith(b"\x89PNG\r\n\x1a\n") or png[12:16] != b"IHDR":
        raise ValueError("The screen sprite sheet is not a PNG")
    width, height = struct.unpack(">II", png[16:24])

    output.mkdir(parents=True, exist_ok=True)
    unpacked = output / NAME
    unpacked.mkdir(exist_ok=True)
    payload = {f"{NAME}.xml": xml, f"{NAME}.png": png}
    archive = output / f"{NAME}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for filename, data in payload.items():
            # Fixed metadata removes differences caused by source file mtimes or OS.
            entry = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            (unpacked / filename).write_bytes(data)

    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or z.namelist() != list(payload):
            raise ValueError("Archive validation failed")
        if any(z.read(name) != data for name, data in payload.items()):
            raise ValueError("Archive payload differs from generated source")

    archive_hash = sha256(archive.read_bytes())
    (output / "SHA256SUMS").write_text(f"{archive_hash}  {archive.name}\n", encoding="utf-8")
    report = {
        "project": "Wendy",
        "version": version,
        "archive": archive.name,
        "sha256": archive_hash,
        "payload_sha256": {name: sha256(data) for name, data in payload.items()},
        "source_sha256": {
            name: sha256((ROOT / name).read_bytes())
            for name in ("VERSION", "src/skin.py", "src/dialogs.xml", f"src/{NAME}.png", "tools/build.py")
        },
        "screen_size": [1280, 800],
        "sprite_sheet_size": [width, height],
        "validation": "XML identity, PNG header, archive names, CRCs and payload checked. Not a hardware test.",
    }
    (output / "build-info.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Require the release tag to match VERSION, e.g. v2.5.3")
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="Output directory (default: project dist/)")
    args = parser.parse_args()
    try:
        report = build(args.output, args.tag)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
