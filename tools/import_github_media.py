#!/usr/bin/env python3
"""One-time exact transfer of the approved public lesson media."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "GITHUB_MEDIA_MANIFEST.json").read_text())
for item in manifest:
    request = urllib.request.Request(item["url"], headers={"User-Agent": "ListeningLibraryMigration/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    assert len(data) == item["size"], "Asset size mismatch"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], "Asset SHA256 mismatch"
    assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == item["git_blob_sha"], "Git blob mismatch"
    for destination in item["destinations"]:
        path = ROOT / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print("Verified " + item["destinations"][0], flush=True)
