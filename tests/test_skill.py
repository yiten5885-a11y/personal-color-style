from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from make_demo import create_demo  # noqa: E402
from validate_manifest import load_manifest, validate_manifest  # noqa: E402


class PersonalColorSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.demo = self.root / "demo"
        self.manifest = create_demo(self.demo)
        self.data = load_manifest(self.manifest)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_manifest(self, data: dict, name: str = "changed.json") -> Path:
        path = self.demo / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_final_demo_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(self.data, self.manifest, "final"), [])

    def test_limited_photo_cannot_claim_high_confidence(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["report"]["photo_quality"] = "limited"
        changed["report"]["limitations"] = ["暖色室内灯"]
        changed["analysis"]["confidence"] = "高"
        errors = validate_manifest(changed, self.write_manifest(changed), "draft")
        self.assertTrue(any("limited photo" in error for error in errors))

    def test_palette_groups_must_be_distinct(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["palette"]["extend"][0] = changed["palette"]["core"][0]
        errors = validate_manifest(changed, self.write_manifest(changed), "draft")
        self.assertTrue(any("another palette group" in error for error in errors))

    def test_asset_path_cannot_escape_manifest_directory(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["assets"]["portrait"] = "../portrait.png"
        errors = validate_manifest(changed, self.write_manifest(changed), "draft")
        self.assertTrue(any("must stay inside" in error for error in errors))

    def test_draft_allows_missing_asset_but_final_rejects_it(self) -> None:
        changed = copy.deepcopy(self.data)
        changed["draping"]["looks"][0]["image"] = "assets/missing.png"
        path = self.write_manifest(changed)
        self.assertFalse(any("asset not found" in error for error in validate_manifest(changed, path, "draft")))
        self.assertTrue(any("asset not found" in error for error in validate_manifest(changed, path, "final")))

    def test_renderer_outputs_three_clean_pngs_and_refuses_clobber(self) -> None:
        output = self.root / "rendered"
        command = [
            sys.executable,
            str(SCRIPTS / "render_report.py"),
            str(self.manifest),
            "--output-dir",
            str(output),
        ]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        names = [
            "01-color-style-overview.png",
            "02-draping-and-outfits.png",
            "03-makeup-hair-details.png",
        ]
        self.assertEqual(sorted(path.name for path in output.glob("*.png")), names)
        for name in names:
            with Image.open(output / name) as image:
                self.assertEqual(image.size, (1800, 2400))
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.info, {})
        second = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already exists", second.stderr)


if __name__ == "__main__":
    unittest.main()
