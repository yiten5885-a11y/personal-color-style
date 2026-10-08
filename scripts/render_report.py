#!/usr/bin/env python3
"""Render three deterministic 3:4 personal-color report cards from a manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:  # pragma: no cover - dependency failure path
    raise SystemExit("Pillow is required. Run with the Codex bundled Python or install Pillow.") from exc

from validate_manifest import load_manifest, validate_manifest


WIDTH = 1800
HEIGHT = 2400
MARGIN = 88
TEXT = "#282429"
MUTED = "#706A70"
LINE = "#DED8DC"
WHITE = "#FFFFFF"
CANVAS = "#F7F4F2"
CARD = "#FFFCFA"

FONT_CANDIDATES = (
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)


def cjk_font_works(path: Path) -> bool:
    try:
        font = ImageFont.truetype(str(path), 42)
        signatures = set()
        for char in "个人色彩诊断":
            mask = font.getmask(char)
            signatures.add((mask.size, bytes(mask)))
        return len(signatures) >= 5
    except Exception:
        return False


def find_font(explicit: Path | None) -> Path:
    candidates = (str(explicit),) if explicit else FONT_CANDIDATES
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file() and cjk_font_works(path):
            return path
    if explicit:
        raise ValueError(f"font does not provide readable CJK glyphs: {explicit}")
    raise ValueError("no readable CJK font found; pass --font /path/to/cjk-font.ttf")


class Fonts:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._cache: dict[int, ImageFont.FreeTypeFont] = {}

    def get(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._cache:
            self._cache[size] = ImageFont.truetype(str(self.path), size)
        return self._cache[size]


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def mix(a: str, b: str, ratio: float) -> str:
    ar, ag, ab = hex_rgb(a)
    br, bg, bb = hex_rgb(b)
    rgb = tuple(round(left * (1 - ratio) + right * ratio) for left, right in zip((ar, ag, ab), (br, bg, bb)))
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def contrast_text(background: str) -> str:
    r, g, b = hex_rgb(background)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "#FFFFFF" if luminance < 0.55 else "#252126"


def open_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGB")


def cover(image: Image.Image, box: tuple[int, int, int, int], *, centering: tuple[float, float] = (0.5, 0.42)) -> Image.Image:
    left, top, right, bottom = box
    return ImageOps.fit(image, (right - left, bottom - top), method=Image.Resampling.LANCZOS, centering=centering)


def rounded_paste(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int], radius: int = 28) -> None:
    left, top, right, bottom = box
    fitted = cover(image, box)
    mask = Image.new("L", fitted.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fitted.width, fitted.height), radius=radius, fill=255)
    canvas.paste(fitted, (left, top), mask)


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    paragraphs = str(text).split("\n")
    lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and text_width(draw, candidate, font) > max_width:
                lines.append(current.rstrip())
                current = char.lstrip()
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    fonts: Fonts,
    *,
    max_size: int,
    min_size: int,
    fill: str = TEXT,
    spacing: float = 1.28,
    stroke_width: int = 0,
) -> int:
    left, top, right, bottom = box
    for size in range(max_size, min_size - 1, -1):
        font = fonts.get(size)
        lines = wrap_text(draw, text, font, right - left)
        line_height = round(size * spacing)
        if len(lines) * line_height <= bottom - top:
            y = top
            for line in lines:
                draw.text((left, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=fill)
                y += line_height
            return y
    raise ValueError(f"text cannot fit in box: {text[:48]!r}")


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: str = CARD, outline: str = LINE, radius: int = 30) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def section_label(draw: ImageDraw.ImageDraw, fonts: Fonts, x: int, y: int, text: str, accent: str) -> int:
    font = fonts.get(27)
    width = text_width(draw, text, font) + 34
    draw.rounded_rectangle((x, y, x + width, y + 46), radius=22, fill=mix(accent, WHITE, 0.78))
    draw.text((x + 17, y + 7), text, font=font, fill=TEXT)
    return x + width


def title_area(draw: ImageDraw.ImageDraw, fonts: Fonts, page: int, title: str, subtitle: str, accent: str) -> None:
    draw.text((MARGIN, 70), f"0{page} / 03", font=fonts.get(28), fill=accent)
    draw.text((MARGIN, 112), title, font=fonts.get(60), fill=TEXT, stroke_width=1, stroke_fill=TEXT)
    draw.text((MARGIN, 186), subtitle, font=fonts.get(25), fill=MUTED)
    draw.line((MARGIN, 235, WIDTH - MARGIN, 235), fill=accent, width=4)


def draw_palette_row(
    draw: ImageDraw.ImageDraw,
    fonts: Fonts,
    x: int,
    y: int,
    width: int,
    label: str,
    colors: list[dict[str, str]],
) -> None:
    draw.text((x, y), label, font=fonts.get(28), fill=TEXT)
    start = x + 175
    gap = 12
    swatch_width = (width - 175 - gap * (len(colors) - 1)) // len(colors)
    for index, color in enumerate(colors):
        left = start + index * (swatch_width + gap)
        draw.rounded_rectangle((left, y - 4, left + swatch_width, y + 70), radius=18, fill=color["hex"])
        name = color["name"]
        font = fonts.get(20)
        if text_width(draw, name, font) > swatch_width - 8:
            font = fonts.get(17)
        draw.text((left + 7, y + 76), name, font=font, fill=MUTED)


def draw_axis(draw: ImageDraw.ImageDraw, fonts: Fonts, box: tuple[int, int, int, int], label: str, axis: dict[str, Any], accent: str) -> None:
    left, top, right, bottom = box
    draw.text((left, top), label, font=fonts.get(24), fill=MUTED)
    draw.text((right - 150, top), axis["label"], font=fonts.get(22), fill=TEXT)
    bar_top = top + 42
    draw.rounded_rectangle((left, bar_top, right, bar_top + 18), radius=9, fill="#E7E1E4")
    value_x = left + round((right - left) * axis["value"] / 100)
    draw.ellipse((value_x - 13, bar_top - 4, value_x + 13, bar_top + 22), fill=accent, outline=WHITE, width=3)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    fonts: Fonts,
    box: tuple[int, int, int, int],
    items: Iterable[str],
    accent: str,
    *,
    size: int = 27,
    max_lines: int | None = None,
) -> None:
    left, top, right, bottom = box
    y = top
    used = 0
    for item in items:
        if max_lines is not None and used >= max_lines:
            break
        font = fonts.get(size)
        lines = wrap_text(draw, item, font, right - left - 42)
        height = max(1, len(lines)) * round(size * 1.26)
        if y + height > bottom:
            raise ValueError(f"bullet content overflows: {item[:40]!r}")
        draw.ellipse((left, y + 11, left + 13, y + 24), fill=accent)
        for line in lines:
            draw.text((left + 32, y), line, font=font, fill=TEXT)
            y += round(size * 1.26)
        y += 12
        used += 1


def render_overview(data: dict[str, Any], portrait: Image.Image, fonts: Fonts, accent: str) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), CANVAS)
    draw = ImageDraw.Draw(canvas)
    title_area(draw, fonts, 1, "个人色彩与风格总览", "Personal Color & Style Overview", accent)

    rounded_paste(canvas, portrait, (MARGIN, 300, 720, 1070), radius=36)
    section_label(draw, fonts, MARGIN + 28, 1010, "当前照片", accent)

    card(draw, (760, 300, WIDTH - MARGIN, 710))
    analysis = data["analysis"]
    draw.text((810, 340), "色彩方向", font=fonts.get(28), fill=MUTED)
    draw.text((810, 390), analysis["season_label"], font=fonts.get(58), fill=accent, stroke_width=1, stroke_fill=accent)
    draw.text((810, 465), analysis["season_english"], font=fonts.get(25), fill=MUTED)
    confidence = analysis["confidence"]
    badge = f"置信度 {confidence}"
    badge_width = text_width(draw, badge, fonts.get(24)) + 34
    draw.rounded_rectangle((810, 515, 810 + badge_width, 560), radius=22, fill=mix(accent, WHITE, 0.78))
    draw.text((827, 522), badge, font=fonts.get(24), fill=TEXT)
    if analysis.get("alternative"):
        draw_wrapped(draw, (810, 585, WIDTH - MARGIN - 36, 675), f"备选方向：{analysis['alternative']}", fonts, max_size=25, min_size=21, fill=TEXT)

    card(draw, (760, 740, WIDTH - MARGIN, 1070))
    draw.text((810, 775), "四色坐标", font=fonts.get(30), fill=TEXT)
    axis_labels = {"temperature": "冷暖", "value": "深浅", "chroma": "鲜柔", "contrast": "对比"}
    for index, key in enumerate(("temperature", "value", "chroma", "contrast")):
        top = 835 + index * 56
        draw_axis(draw, fonts, (810, top, WIDTH - MARGIN - 42, top + 54), axis_labels[key], analysis["axes"][key], accent)

    card(draw, (MARGIN, 1110, 920, 1640))
    draw.text((MARGIN + 38, 1148), "判断依据", font=fonts.get(32), fill=TEXT)
    draw_bullets(draw, fonts, (MARGIN + 38, 1210, 880, 1600), analysis["evidence"], accent, size=25)

    card(draw, (955, 1110, WIDTH - MARGIN, 1640))
    draw.text((995, 1148), "风格地图", font=fonts.get(32), fill=TEXT)
    x = 995
    y = 1210
    for keyword in analysis["keywords"]:
        end = section_label(draw, fonts, x, y, keyword, accent)
        x = end + 14
        if x > WIDTH - MARGIN - 180:
            x = 995
            y += 62
    directions = analysis["style_direction"]
    draw_wrapped(draw, (995, y + 78, WIDTH - MARGIN - 34, y + 158), f"主轴｜{directions['primary']}", fonts, max_size=25, min_size=21)
    draw_wrapped(draw, (995, y + 172, WIDTH - MARGIN - 34, y + 252), f"延展｜{directions['explore']}", fonts, max_size=25, min_size=21)
    draw_wrapped(draw, (995, y + 266, WIDTH - MARGIN - 34, 1602), f"慎用｜{directions['caution']}", fonts, max_size=25, min_size=19)

    card(draw, (MARGIN, 1680, WIDTH - MARGIN, 2180))
    draw.text((MARGIN + 38, 1715), "个人色彩地图", font=fonts.get(32), fill=TEXT)
    draw_palette_row(draw, fonts, MARGIN + 38, 1790, WIDTH - 2 * MARGIN - 76, "核心推荐", data["palette"]["core"])
    draw_palette_row(draw, fonts, MARGIN + 38, 1915, WIDTH - 2 * MARGIN - 76, "延展尝试", data["palette"]["extend"])
    draw_palette_row(draw, fonts, MARGIN + 38, 2040, WIDTH - 2 * MARGIN - 76, "搭配慎用", data["palette"]["caution"])

    summary_fill = mix(accent, WHITE, 0.86)
    card(draw, (MARGIN, 2210, WIDTH - MARGIN, 2320), fill=summary_fill, outline=summary_fill)
    draw_wrapped(draw, (MARGIN + 34, 2238, WIDTH - MARGIN - 34, 2302), analysis["summary"], fonts, max_size=28, min_size=22)
    return canvas


def draw_drape_preview(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: Fonts,
    portrait: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    colors: list[dict[str, str]],
    note: str,
) -> None:
    left, top, right, bottom = box
    card(draw, box)
    draw.text((left + 28, top + 22), label, font=fonts.get(28), fill=TEXT)
    image_box = (left + 28, top + 72, right - 28, top + 415)
    rounded_paste(canvas, portrait, image_box, radius=22)
    band_top = image_box[3] - 72
    swatch_width = (image_box[2] - image_box[0]) // min(4, len(colors))
    for index, color in enumerate(colors[:4]):
        x = image_box[0] + index * swatch_width
        draw.rectangle((x, band_top, x + swatch_width, image_box[3]), fill=color["hex"])
    draw_wrapped(draw, (left + 28, top + 438, right - 28, bottom - 22), note, fonts, max_size=23, min_size=19, fill=MUTED)


def draw_look_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: Fonts,
    base: Path,
    look: dict[str, str],
    box: tuple[int, int, int, int],
    accent: str,
) -> None:
    left, top, right, bottom = box
    card(draw, box)
    image = open_image((base / look["image"]).resolve())
    rounded_paste(canvas, image, (left + 22, top + 22, right - 22, top + 420), radius=22)
    draw.text((left + 26, top + 444), look["title"], font=fonts.get(28), fill=TEXT)
    section_label(draw, fonts, left + 26, top + 488, look["scene"], accent)
    draw_wrapped(draw, (left + 26, top + 552, right - 26, bottom - 20), look["description"], fonts, max_size=22, min_size=18, fill=MUTED)


def render_draping(data: dict[str, Any], portrait: Image.Image, fonts: Fonts, accent: str, base: Path) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), CANVAS)
    draw = ImageDraw.Draw(canvas)
    title_area(draw, fonts, 2, "色彩上身与穿搭应用", "Color Draping & Styling Application", accent)

    draping = data["draping"]
    box_width = 514
    gap = 28
    previews = (
        ("核心推荐", data["palette"]["core"], draping["core_note"]),
        ("延展尝试", data["palette"]["extend"], draping["extend_note"]),
        ("搭配慎用", data["palette"]["caution"], draping["caution_note"]),
    )
    for index, (label, colors, note) in enumerate(previews):
        left = MARGIN + index * (box_width + gap)
        draw_drape_preview(canvas, draw, fonts, portrait, (left, 290, left + box_width, 860), label, colors, note)

    draw.text((MARGIN, 910), "场景穿搭", font=fonts.get(34), fill=TEXT)
    looks = draping["looks"][:3]
    for index, look in enumerate(looks):
        left = MARGIN + index * (box_width + gap)
        draw_look_card(canvas, draw, fonts, base, look, (left, 970, left + box_width, 1610), accent)

    card(draw, (MARGIN, 1650, 1040, 2180))
    draw.text((MARGIN + 38, 1688), "配色公式", font=fonts.get(32), fill=TEXT)
    formulas = draping["formulas"]
    split = (len(formulas) + 1) // 2
    draw_bullets(draw, fonts, (MARGIN + 38, 1750, 540, 2140), formulas[:split], accent, size=23)
    draw_bullets(draw, fonts, (560, 1750, 1000, 2140), formulas[split:], accent, size=23)

    card(draw, (1075, 1650, WIDTH - MARGIN, 2180))
    draw.text((1115, 1688), "单品与边界", font=fonts.get(32), fill=TEXT)
    combined = [f"单品｜{item}" for item in draping["items"][:4]] + [f"慎用｜{item}" for item in draping["avoid"][:4]]
    draw_bullets(draw, fonts, (1115, 1750, WIDTH - MARGIN - 32, 2140), combined, accent, size=22)

    summary_fill = mix(accent, WHITE, 0.86)
    card(draw, (MARGIN, 2210, WIDTH - MARGIN, 2320), fill=summary_fill, outline=summary_fill)
    draw_wrapped(draw, (MARGIN + 34, 2238, WIDTH - MARGIN - 34, 2302), draping["summary"], fonts, max_size=28, min_size=22)
    return canvas


def draw_color_chips(
    draw: ImageDraw.ImageDraw,
    fonts: Fonts,
    colors: list[dict[str, str]],
    x: int,
    y: int,
    *,
    chip_width: int = 102,
    show_name: bool = False,
) -> None:
    for index, color in enumerate(colors):
        left = x + index * (chip_width + 10)
        draw.rounded_rectangle((left, y, left + chip_width, y + 42), radius=18, fill=color["hex"])
        if show_name:
            label = color["name"]
            font = fonts.get(17)
            draw.text((left + 4, y + 49), label, font=font, fill=MUTED)


def render_beauty(data: dict[str, Any], portrait: Image.Image, fonts: Fonts, accent: str, base: Path) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), CANVAS)
    draw = ImageDraw.Draw(canvas)
    title_area(draw, fonts, 3, "妆容 发色与细节指南", "Makeup, Hair & Beauty Detail Guide", accent)
    beauty = data["beauty"]

    rounded_paste(canvas, portrait, (MARGIN, 300, 650, 1005), radius=36)
    section_label(draw, fonts, MARGIN + 26, 946, "原始参考", accent)

    card(draw, (690, 300, WIDTH - MARGIN, 1005))
    draw.text((730, 338), "妆容方向", font=fonts.get(34), fill=TEXT)
    labels = {"base": "底妆", "brow": "眉毛", "eye": "眼妆", "blush": "腮红", "lip": "唇妆"}
    for index, key in enumerate(("base", "brow", "eye", "blush", "lip")):
        top = 410 + index * 112
        part = beauty["makeup"][key]
        draw.text((730, top), labels[key], font=fonts.get(25), fill=accent)
        draw_wrapped(draw, (830, top - 3, 1295, top + 70), part["direction"], fonts, max_size=23, min_size=19)
        draw_color_chips(draw, fonts, part["colors"], 1320, top + 5, chip_width=92)

    draw.text((MARGIN, 1050), "妆感示范", font=fonts.get(34), fill=TEXT)
    box_width = 514
    gap = 28
    for index, look in enumerate(beauty["looks"][:3]):
        left = MARGIN + index * (box_width + gap)
        draw_look_card(canvas, draw, fonts, base, look, (left, 1110, left + box_width, 1715), accent)

    card(draw, (MARGIN, 1755, 1080, 2180))
    draw.text((MARGIN + 38, 1790), "发色区间", font=fonts.get(32), fill=TEXT)
    hair_labels = {"safe": "稳妥", "brightening": "提气色", "explore": "进阶", "caution": "慎选"}
    for index, key in enumerate(("safe", "brightening", "explore", "caution")):
        top = 1850 + index * 76
        draw.text((MARGIN + 38, top + 8), hair_labels[key], font=fonts.get(24), fill=TEXT)
        draw_color_chips(draw, fonts, beauty["hair"][key], MARGIN + 170, top, chip_width=118, show_name=True)

    card(draw, (1115, 1755, WIDTH - MARGIN, 2180))
    draw.text((1155, 1790), "配饰与避雷", font=fonts.get(32), fill=TEXT)
    draw.text((1155, 1846), "配饰", font=fonts.get(21), fill=accent)
    draw.text((1442, 1846), "慎用", font=fonts.get(21), fill=accent)
    draw_bullets(draw, fonts, (1155, 1884, 1424, 2148), beauty["accessories"][:4], accent, size=17)
    draw_bullets(draw, fonts, (1442, 1884, WIDTH - MARGIN - 24, 2148), beauty["avoid"][:5], accent, size=17)

    summary_fill = mix(accent, WHITE, 0.86)
    card(draw, (MARGIN, 2210, WIDTH - MARGIN, 2320), fill=summary_fill, outline=summary_fill)
    draw_wrapped(draw, (MARGIN + 34, 2238, WIDTH - MARGIN - 34, 2302), beauty["summary"], fonts, max_size=28, min_size=22)
    return canvas


def save_png(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=True)
    os.chmod(path, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--font", type=Path, help="CJK-capable TTF, OTF, or TTC font")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    try:
        data = load_manifest(manifest_path)
        errors = validate_manifest(data, manifest_path, "final")
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        font_path = find_font(args.font)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_dir.mkdir(mode=0o700)
    except FileExistsError:
        print(f"ERROR: output directory already exists: {output_dir}", file=sys.stderr)
        return 1

    fonts = Fonts(font_path)
    base = manifest_path.parent
    portrait = open_image((base / data["assets"]["portrait"]).resolve())
    accent = data["palette"]["core"][0]["hex"]
    if contrast_text(accent) == "#FFFFFF":
        accent = mix(accent, WHITE, 0.18)

    try:
        outputs = (
            ("01-color-style-overview.png", render_overview(data, portrait, fonts, accent)),
            ("02-draping-and-outfits.png", render_draping(data, portrait, fonts, accent, base)),
            ("03-makeup-hair-details.png", render_beauty(data, portrait, fonts, accent, base)),
        )
        for name, image in outputs:
            save_png(image, output_dir / name)
        report = {
            "schema_version": 1,
            "font": font_path.name,
            "files": [{"name": name, "width": WIDTH, "height": HEIGHT, "format": "PNG"} for name, _ in outputs],
            "metadata_policy": "new PNG files contain no inherited source metadata",
        }
        report_path = output_dir / "render-report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(report_path, 0o600)
    except Exception:
        for child in output_dir.iterdir():
            if child.is_file():
                child.unlink()
        output_dir.rmdir()
        raise

    print(f"Rendered 3 cards to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
