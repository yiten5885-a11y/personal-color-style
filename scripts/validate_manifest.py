#!/usr/bin/env python3
"""Validate a personal-color-style report manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
CONFIDENCE = {"高", "中", "低"}
AXES = ("temperature", "value", "chroma", "contrast")
MAKEUP_PARTS = ("base", "brow", "eye", "blush", "lip")
HAIR_GROUPS = ("safe", "brightening", "explore", "caution")


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


class Checker:
    def __init__(self, manifest_path: Path, mode: str) -> None:
        self.manifest_path = manifest_path.resolve()
        self.base = self.manifest_path.parent
        self.mode = mode
        self.errors: list[str] = []
        self.asset_paths: list[tuple[str, str]] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def obj(self, value: Any, path: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        return value

    def text(self, value: Any, path: str, *, max_len: int = 120, allow_empty: bool = False) -> str:
        if not isinstance(value, str):
            self.error(path, "must be a string")
            return ""
        cleaned = value.strip()
        if not cleaned and not allow_empty:
            self.error(path, "must not be empty")
        if len(cleaned) > max_len:
            self.error(path, f"must be at most {max_len} characters")
        if any(ch in cleaned for ch in ("\x00", "\r")):
            self.error(path, "contains an unsupported control character")
        return cleaned

    def enum(self, value: Any, path: str, choices: set[str]) -> str:
        result = self.text(value, path, max_len=20)
        if result and result not in choices:
            self.error(path, f"must be one of {sorted(choices)}")
        return result

    def list_of_text(
        self,
        value: Any,
        path: str,
        *,
        minimum: int,
        maximum: int,
        item_max: int = 80,
    ) -> list[str]:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        if not minimum <= len(value) <= maximum:
            self.error(path, f"must contain {minimum} to {maximum} items")
        out = [self.text(item, f"{path}[{index}]", max_len=item_max) for index, item in enumerate(value)]
        normalized = [item.casefold() for item in out if item]
        if len(normalized) != len(set(normalized)):
            self.error(path, "must not contain duplicate items")
        return out

    def color_list(self, value: Any, path: str, *, minimum: int, maximum: int) -> list[dict[str, str]]:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        if not minimum <= len(value) <= maximum:
            self.error(path, f"must contain {minimum} to {maximum} colors")
        out: list[dict[str, str]] = []
        local_names: set[str] = set()
        local_hexes: set[str] = set()
        for index, item in enumerate(value):
            entry = self.obj(item, f"{path}[{index}]")
            name = self.text(entry.get("name"), f"{path}[{index}].name", max_len=14)
            hex_value = self.text(entry.get("hex"), f"{path}[{index}].hex", max_len=7).upper()
            if hex_value and not HEX_RE.fullmatch(hex_value):
                self.error(f"{path}[{index}].hex", "must be a six-digit hex color such as #AABBCC")
            folded = name.casefold()
            if folded in local_names:
                self.error(path, f"duplicate color name: {name}")
            if hex_value in local_hexes:
                self.error(path, f"duplicate hex color: {hex_value}")
            local_names.add(folded)
            local_hexes.add(hex_value)
            out.append({"name": name, "hex": hex_value})
        return out

    def asset(self, value: Any, path: str) -> str:
        rel = self.text(value, path, max_len=180)
        if not rel:
            return rel
        rel_path = Path(rel)
        if rel_path.is_absolute():
            self.error(path, "must be relative to the manifest")
            return rel
        candidate = (self.base / rel_path).resolve()
        if candidate != self.base and self.base not in candidate.parents:
            self.error(path, "must stay inside the manifest directory")
            return rel
        self.asset_paths.append((path, rel))
        return rel

    def validate_assets(self) -> None:
        if self.mode != "final":
            return
        try:
            from PIL import Image
        except ImportError:
            self.error("assets", "Pillow is required for final asset validation")
            return
        seen: set[Path] = set()
        for field, rel in self.asset_paths:
            candidate = (self.base / rel).resolve()
            if candidate in seen:
                self.error(field, "each portrait or look asset must use a distinct path")
                continue
            seen.add(candidate)
            if not candidate.is_file():
                self.error(field, f"asset not found: {rel}")
                continue
            try:
                with Image.open(candidate) as image:
                    image.verify()
                with Image.open(candidate) as image:
                    width, height = image.size
                if min(width, height) < 360:
                    self.error(field, f"asset is too small: {width}x{height}; shortest side must be at least 360")
            except Exception as exc:  # Pillow raises several decoder-specific errors.
                self.error(field, f"asset is not a decodable image: {exc}")


def validate_manifest(data: dict[str, Any], manifest_path: Path, mode: str = "final") -> list[str]:
    check = Checker(manifest_path, mode)
    if data.get("schema_version") != 1:
        check.error("schema_version", "must equal 1")

    report = check.obj(data.get("report"), "report")
    check.text(report.get("title"), "report.title", max_len=28)
    check.text(report.get("subtitle"), "report.subtitle", max_len=60)
    photo_quality = check.enum(report.get("photo_quality"), "report.photo_quality", {"good", "limited"})
    limitations = check.list_of_text(report.get("limitations"), "report.limitations", minimum=0, maximum=4, item_max=56)

    analysis = check.obj(data.get("analysis"), "analysis")
    check.text(analysis.get("season_label"), "analysis.season_label", max_len=18)
    check.text(analysis.get("season_english"), "analysis.season_english", max_len=36)
    confidence = check.enum(analysis.get("confidence"), "analysis.confidence", CONFIDENCE)
    check.text(analysis.get("alternative"), "analysis.alternative", max_len=46, allow_empty=True)
    check.text(analysis.get("summary"), "analysis.summary", max_len=120)
    check.list_of_text(analysis.get("evidence"), "analysis.evidence", minimum=3, maximum=6, item_max=72)
    check.list_of_text(analysis.get("keywords"), "analysis.keywords", minimum=5, maximum=8, item_max=12)
    if photo_quality == "limited" and confidence == "高":
        check.error("analysis.confidence", "a limited photo cannot support high confidence")
    if photo_quality == "limited" and not limitations:
        check.error("report.limitations", "must name at least one limitation for a limited photo")

    axes = check.obj(analysis.get("axes"), "analysis.axes")
    if set(axes) != set(AXES):
        check.error("analysis.axes", f"must contain exactly {list(AXES)}")
    for key in AXES:
        axis = check.obj(axes.get(key), f"analysis.axes.{key}")
        check.text(axis.get("label"), f"analysis.axes.{key}.label", max_len=12)
        value = axis.get("value")
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            check.error(f"analysis.axes.{key}.value", "must be an integer from 0 to 100")

    style_direction = check.obj(analysis.get("style_direction"), "analysis.style_direction")
    for key in ("primary", "explore", "caution"):
        check.text(style_direction.get(key), f"analysis.style_direction.{key}", max_len=72)

    palette = check.obj(data.get("palette"), "palette")
    all_names: set[str] = set()
    all_hexes: set[str] = set()
    for key in ("core", "extend", "caution"):
        colors = check.color_list(palette.get(key), f"palette.{key}", minimum=5, maximum=8)
        for color in colors:
            folded = color["name"].casefold()
            if folded in all_names:
                check.error(f"palette.{key}", f"color name also appears in another palette group: {color['name']}")
            if color["hex"] in all_hexes:
                check.error(f"palette.{key}", f"hex also appears in another palette group: {color['hex']}")
            all_names.add(folded)
            all_hexes.add(color["hex"])

    draping = check.obj(data.get("draping"), "draping")
    for key in ("core_note", "extend_note", "caution_note"):
        check.text(draping.get(key), f"draping.{key}", max_len=82)
    looks = draping.get("looks")
    if not isinstance(looks, list):
        check.error("draping.looks", "must be an array")
        looks = []
    elif not 3 <= len(looks) <= 4:
        check.error("draping.looks", "must contain 3 to 4 looks")
    for index, item in enumerate(looks):
        look = check.obj(item, f"draping.looks[{index}]")
        check.text(look.get("title"), f"draping.looks[{index}].title", max_len=18)
        check.text(look.get("scene"), f"draping.looks[{index}].scene", max_len=16)
        check.text(look.get("description"), f"draping.looks[{index}].description", max_len=64)
        check.asset(look.get("image"), f"draping.looks[{index}].image")
    check.list_of_text(draping.get("formulas"), "draping.formulas", minimum=6, maximum=10, item_max=44)
    check.list_of_text(draping.get("items"), "draping.items", minimum=4, maximum=8, item_max=44)
    check.list_of_text(draping.get("avoid"), "draping.avoid", minimum=4, maximum=6, item_max=56)
    check.text(draping.get("summary"), "draping.summary", max_len=120)

    beauty = check.obj(data.get("beauty"), "beauty")
    makeup = check.obj(beauty.get("makeup"), "beauty.makeup")
    if set(makeup) != set(MAKEUP_PARTS):
        check.error("beauty.makeup", f"must contain exactly {list(MAKEUP_PARTS)}")
    for key in MAKEUP_PARTS:
        part = check.obj(makeup.get(key), f"beauty.makeup.{key}")
        check.text(part.get("direction"), f"beauty.makeup.{key}.direction", max_len=58)
        check.color_list(part.get("colors"), f"beauty.makeup.{key}.colors", minimum=2, maximum=4)

    beauty_looks = beauty.get("looks")
    if not isinstance(beauty_looks, list):
        check.error("beauty.looks", "must be an array")
        beauty_looks = []
    elif not 3 <= len(beauty_looks) <= 4:
        check.error("beauty.looks", "must contain 3 to 4 looks")
    for index, item in enumerate(beauty_looks):
        look = check.obj(item, f"beauty.looks[{index}]")
        check.text(look.get("title"), f"beauty.looks[{index}].title", max_len=18)
        check.text(look.get("scene"), f"beauty.looks[{index}].scene", max_len=16)
        check.text(look.get("description"), f"beauty.looks[{index}].description", max_len=64)
        check.asset(look.get("image"), f"beauty.looks[{index}].image")

    hair = check.obj(beauty.get("hair"), "beauty.hair")
    if set(hair) != set(HAIR_GROUPS):
        check.error("beauty.hair", f"must contain exactly {list(HAIR_GROUPS)}")
    for key in HAIR_GROUPS:
        check.color_list(hair.get(key), f"beauty.hair.{key}", minimum=2, maximum=4)
    check.list_of_text(beauty.get("accessories"), "beauty.accessories", minimum=4, maximum=8, item_max=46)
    check.list_of_text(beauty.get("avoid"), "beauty.avoid", minimum=6, maximum=10, item_max=54)
    check.text(beauty.get("summary"), "beauty.summary", max_len=120)

    assets = check.obj(data.get("assets"), "assets")
    check.asset(assets.get("portrait"), "assets.portrait")
    check.validate_assets()
    return check.errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--mode", choices=("draft", "final"), default="final")
    parser.add_argument("--json", action="store_true", help="emit a JSON validation result")
    args = parser.parse_args()

    try:
        data = load_manifest(args.manifest)
        errors = validate_manifest(data, args.manifest, args.mode)
    except ValueError as exc:
        errors = [str(exc)]

    result = {"valid": not errors, "mode": args.mode, "error_count": len(errors), "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print(f"Manifest valid ({args.mode}).")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
