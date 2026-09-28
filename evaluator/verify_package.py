#!/usr/bin/env python3
"""Verify the released benchmark/platform hashes before evaluating a candidate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT / "evaluator/package_manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Package file missing or changed: {name}")
    print(f"Verified {len(manifest['sha256'])} package files.")


if __name__ == "__main__":
    verify()
