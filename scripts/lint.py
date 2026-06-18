#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "pyproject.toml",
    "README.md",
    "LICENSE",
    "src/cloud_egress_ip_ranges/__init__.py",
    "src/cloud_egress_ip_ranges/__main__.py",
    "src/cloud_egress_ip_ranges/cli.py",
    "scripts/build.py",
    "scripts/lint.py",
    "tests/test_smoke.py",
    "docs/schema.md",
    "docs/sources.md",
    "docs/confidence.md",
    "docs/outputs.md",
    "docs/operations.md",
    ".github/workflows/ci.yml",
    ".github/workflows/daily-release.yml",
]
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json"}
MARKER_PATTERN = r"\b" + r"\b|\b".join(["TO" + "DO", "FIX" + "ME", "X" * 3]) + r"\b"
FORBIDDEN = [
    re.compile(MARKER_PATTERN),
    re.compile(r"\bprint\([^)]*(debug|trace|here|" + "TO" + "DO" + ")", re.IGNORECASE),
]


def iter_project_files() -> list[Path]:
    scan_roots = [
        ROOT / "src",
        ROOT / "scripts",
        ROOT / "tests",
        ROOT / "docs",
        ROOT / ".github",
    ]
    files: list[Path] = []
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in TEXT_SUFFIXES:
                files.append(path)
    for rel in ["README.md", "pyproject.toml", "LICENSE"]:
        path = ROOT / rel
        if path.exists():
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    for path in iter_project_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: malformed JSON: {exc}")
        for pattern in FORBIDDEN:
            if pattern.search(text):
                errors.append(f"{rel}: forbidden session marker or debug print")

    if errors:
        for error in errors:
            print(error)
        return 1
    print("lint ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
