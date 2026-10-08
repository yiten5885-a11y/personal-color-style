#!/usr/bin/env python3
"""Create a synthetic, non-personal manifest and image set for local testing."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw


def synthetic_person(path: Path, background: str, outfit: str, accent: str, *, makeup: str | None = None) -> None:
    width, height = 720, 900
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw.ellipse((230, 100, 490, 360), fill="#D8AA8C")
    draw.pieslice((195, 62, 525, 382), 180, 360, fill="#332A2D")
    draw.rounded_rectangle((135, 360, 585, 870), radius=120, fill=outfit)
    draw.polygon(((360, 360), (270, 505), (450, 505)), fill="#F4E7DF")
    draw.ellipse((292, 207, 320, 223), fill="#332A2D")
    draw.ellipse((400, 207, 428, 223), fill="#332A2D")
    lip = makeup or "#9A5E65"
    draw.arc((326, 265, 395, 312), 12, 168, fill=lip, width=6)
    draw.rounded_rectangle((96, 760, 624, 820), radius=30, fill=accent)
    image.save(path, format="PNG")
    os.chmod(path, 0o600)


def create_demo(root: Path) -> Path:
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    assets = root / "assets"
    assets.mkdir(mode=0o700)
    synthetic_person(assets / "portrait.png", "#ECE7E5", "#4F485A", "#9A7187")
    synthetic_person(assets / "outfit-daily.png", "#EEEAF0", "#6D7287", "#C49AAF")
    synthetic_person(assets / "outfit-work.png", "#EBEEF2", "#485367", "#8FA2B7")
    synthetic_person(assets / "outfit-social.png", "#F1EBEC", "#805D6E", "#B27A90")
    synthetic_person(assets / "makeup-clear.png", "#F2EBE8", "#8B7481", "#B88696", makeup="#A35F76")
    synthetic_person(assets / "makeup-soft.png", "#EFEAEE", "#6D6878", "#A18DA2", makeup="#946878")
    synthetic_person(assets / "makeup-defined.png", "#E9EBF0", "#4D5361", "#7A8396", makeup="#8C4F65")

    manifest = {
        "schema_version": 1,
        "report": {
            "title": "个人色彩与形象指南",
            "subtitle": "Personal Color & Style Guide",
            "photo_quality": "good",
            "limitations": [],
        },
        "analysis": {
            "season_label": "柔夏倾向",
            "season_english": "Soft Summer Direction",
            "confidence": "中",
            "alternative": "冷柔中性色方向",
            "summary": "用冷柔中性色建立稳定主轴，再以灰粉与雾蓝增加变化；实际选购仍需结合面料和现场光线。",
            "evidence": [
                "整体明暗反差较柔和，深浅过渡自然",
                "偏灰的冷色与当前视觉关系更协调",
                "中等明度比极亮或极深色更平衡",
                "低至中彩度更容易突出人物本身",
            ],
            "axes": {
                "temperature": {"label": "偏冷中性", "value": 38},
                "value": {"label": "中等偏浅", "value": 62},
                "chroma": {"label": "柔和", "value": 34},
                "contrast": {"label": "中低对比", "value": 40},
            },
            "keywords": ["清透", "克制", "柔和", "知性", "轻盈", "自然"],
            "style_direction": {
                "primary": "雾感冷色与柔和材质，保持中低对比",
                "explore": "用小面积莓果色或深海蓝增加视觉重点",
                "caution": "高饱和暖色贴近面部时先缩小面积并实穿比较",
            },
        },
        "palette": {
            "core": [
                {"name": "雾霾蓝", "hex": "#7F94A8"},
                {"name": "灰紫", "hex": "#8E8198"},
                {"name": "柔粉", "hex": "#C49AAA"},
                {"name": "冷灰", "hex": "#8A8D94"},
                {"name": "蓝灰", "hex": "#66798C"},
                {"name": "莓果红", "hex": "#985A70"},
            ],
            "extend": [
                {"name": "鼠尾草", "hex": "#8D9A8B"},
                {"name": "浅薰衣草", "hex": "#B5A8C1"},
                {"name": "珍珠白", "hex": "#E6E3E1"},
                {"name": "海盐绿", "hex": "#8EA7A1"},
                {"name": "灰粉棕", "hex": "#A88787"},
                {"name": "柔墨蓝", "hex": "#455568"},
            ],
            "caution": [
                {"name": "橘红", "hex": "#E55E35"},
                {"name": "荧光黄", "hex": "#E8F02A"},
                {"name": "亮暖金", "hex": "#F0B72D"},
                {"name": "焦糖橙", "hex": "#C66B32"},
                {"name": "电光绿", "hex": "#4DCF5B"},
                {"name": "鲜珊瑚", "hex": "#F16F68"},
            ],
        },
        "draping": {
            "core_note": "适合作为靠近面部的稳定主色，强调柔和与清晰。",
            "extend_note": "适合变化风格或作为第二主色，注意材质和面积。",
            "caution_note": "并非禁止；靠近面部时减少面积，或用核心色过渡。",
            "looks": [
                {"title": "雾蓝日常", "scene": "日常", "description": "雾蓝针织配冷灰下装，轻松并保持面部清晰。", "image": "assets/outfit-daily.png"},
                {"title": "蓝灰通勤", "scene": "通勤", "description": "蓝灰外套与珍珠白内搭形成克制的中等对比。", "image": "assets/outfit-work.png"},
                {"title": "莓果社交", "scene": "社交", "description": "莓果色作为视觉重点，以柔墨蓝稳定整体层次。", "image": "assets/outfit-social.png"},
            ],
            "formulas": [
                "雾霾蓝 + 冷灰 + 珍珠白",
                "灰紫 + 蓝灰 + 暗银",
                "柔粉 + 柔墨蓝 + 冷白",
                "海盐绿 + 冷灰 + 雾蓝",
                "莓果红 + 蓝灰 + 珍珠白",
                "浅薰衣草 + 柔墨蓝 + 冷灰",
            ],
            "items": ["柔软针织上衣", "垂顺蓝灰长裤", "雾面小体量包", "暗银细节配饰"],
            "avoid": ["高饱和暖色大面积贴脸", "全身极深色缺少过渡", "强金色高光抢占视觉", "过度甜腻的粉色堆叠"],
            "summary": "穿搭以柔和冷色做骨架，通过明度层次和小面积重点色增加变化，不必被单一路线限制。",
        },
        "beauty": {
            "makeup": {
                "base": {"direction": "轻薄中性底妆，保留真实皮肤质感", "colors": [{"name": "中性象牙", "hex": "#E0C2AD"}, {"name": "柔米调", "hex": "#D4B39E"}]},
                "brow": {"direction": "灰棕眉色，边界自然并保持适中存在感", "colors": [{"name": "灰棕", "hex": "#756A67"}, {"name": "冷深棕", "hex": "#584F50"}]},
                "eye": {"direction": "灰紫和蓝灰建立层次，减少高亮金色", "colors": [{"name": "灰紫影", "hex": "#8E7F91"}, {"name": "蓝灰影", "hex": "#6F7887"}, {"name": "柔墨线", "hex": "#44454F"}]},
                "blush": {"direction": "柔和玫瑰调少量晕染，避免鲜橘大面积", "colors": [{"name": "灰玫瑰", "hex": "#B77D88"}, {"name": "柔莓粉", "hex": "#A86E7F"}]},
                "lip": {"direction": "豆沙玫瑰到莓果色，按场景调整深浅", "colors": [{"name": "豆沙玫瑰", "hex": "#9D626B"}, {"name": "柔莓果", "hex": "#8D4F64"}, {"name": "冷红棕", "hex": "#7C4C53"}]},
            },
            "looks": [
                {"title": "清透日常", "scene": "日常", "description": "低彩度眼妆与轻薄底妆，突出自然清晰度。", "image": "assets/makeup-clear.png"},
                {"title": "柔雾通勤", "scene": "通勤", "description": "灰棕眉眼与柔玫瑰唇色，保持克制和专业感。", "image": "assets/makeup-soft.png"},
                {"title": "莓果重点", "scene": "社交", "description": "提高唇色存在感，其他部位维持柔和与干净。", "image": "assets/makeup-defined.png"},
            ],
            "hair": {
                "safe": [{"name": "自然黑", "hex": "#28252A"}, {"name": "冷深棕", "hex": "#4B3F42"}],
                "brightening": [{"name": "灰茶棕", "hex": "#756465"}, {"name": "柔冷棕", "hex": "#65565C"}],
                "explore": [{"name": "灰紫棕", "hex": "#6E586A"}, {"name": "蓝黑", "hex": "#273243"}],
                "caution": [{"name": "亮橘棕", "hex": "#A9572E"}, {"name": "金铜色", "hex": "#B77935"}],
            },
            "accessories": ["暗银或白金色金属", "雾面与细腻光泽结合", "柔方或细金属镜框", "蓝灰和莓果色小包"],
            "avoid": ["过黄底妆改变自然底色", "鲜橘腮红大面积晕染", "暖金高光过强", "眼妆对比突然过高", "发色过度漂浅", "全套颜色都偏灰而失去重点"],
            "summary": "妆发细节保持冷柔和中等明度，用局部清晰边界提升精神感，同时保留真实肤质与个人辨识度。",
        },
        "assets": {"portrait": "assets/portrait.png"},
    }
    manifest_path = root / "report.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new directory for the synthetic demo")
    args = parser.parse_args()
    path = create_demo(args.output.expanduser().resolve())
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
