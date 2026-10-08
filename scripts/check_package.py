#!/usr/bin/env python3
"""Fail-closed checks for the publishable Skill source tree."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ".gitignore",
    "LICENSE",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/personal-color-style-cover.svg",
    "assets/personal-color-style-icon.svg",
    "references/analysis-contract.md",
    "references/quality-and-privacy.md",
    "references/report-contract.md",
    "scripts/check_package.py",
    "scripts/make_demo.py",
    "scripts/render_report.py",
    "scripts/validate_manifest.py",
    "tests/test_skill.py",
}
PRIVATE_SUFFIXES = {
    ".heic",
    ".jpeg",
    ".jpg",
    ".json",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", "dist", "output", "work"}


def package_files() -> list[Path]:
    if (ROOT / ".git").is_dir():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]

    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    )


def main() -> int:
    errors: list[str] = []
    files = package_files()
    relative = {path.relative_to(ROOT).as_posix() for path in files}

    missing = sorted(REQUIRED - relative)
    if missing:
        errors.append("missing required files: " + ", ".join(missing))

    private_files = sorted(
        path
        for path in relative
        if Path(path).suffix.lower() in PRIVATE_SUFFIXES
        and path not in {"assets/cover.png"}
    )
    if private_files:
        errors.append("private or generated asset types are packaged: " + ", ".join(private_files))

    local_prefix = "/" + "Users/"
    for path in files:
        if path.suffix.lower() not in {".md", ".py", ".yaml", ".yml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        if local_prefix in text:
            errors.append(f"absolute local path found in {path.relative_to(ROOT)}")

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill, re.DOTALL)
    if not frontmatter:
        errors.append("SKILL.md frontmatter is missing or malformed")
    else:
        header = frontmatter.group(1)
        if not re.search(r"(?m)^name:\s*personal-color-style\s*$", header):
            errors.append("SKILL.md name must be personal-color-style")
        description = re.search(r"(?m)^description:\s*(.+)$", header)
        if not description or not (80 <= len(description.group(1).strip()) <= 1024):
            errors.append("SKILL.md description must be 80 to 1024 characters")

    agent = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    for key in ("display_name:", "short_description:", "default_prompt:"):
        if key not in agent:
            errors.append(f"agents/openai.yaml is missing {key}")
    if "$personal-color-style" not in agent:
        errors.append("agents/openai.yaml default prompt must invoke $personal-color-style")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Package check passed ({len(files)} tracked or packaged files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
