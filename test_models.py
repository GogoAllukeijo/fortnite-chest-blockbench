"""Structural and regression checks for the downloadable Blockbench projects."""

import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import unittest
import zipfile

from PIL import Image, ImageChops

import gen


ROOT = Path(__file__).resolve().parent


class ChestModelsTest(unittest.TestCase):
    epic = False
    prefix = "Regular_chest"
    texture_name = "chest_atlas.png"
    preview_name = "preview.png"

    @classmethod
    def setUpClass(cls):
        cls.models = [json.loads((ROOT / f"{name}.bbmodel").read_text())
                      for name in (cls.prefix, cls.prefix + "_open")]

    def test_project_names(self):
        self.assertEqual([model["name"] for model in self.models],
                         [self.prefix, self.prefix + "_open"])

    def test_both_poses_are_the_same_chest(self):
        closed, opened = copy.deepcopy(self.models)
        closed.pop("name")
        opened.pop("name")
        a = next(g for g in closed["outliner"] if g["name"] == "lid")
        b = next(g for g in opened["outliner"] if g["name"] == "lid")
        self.assertEqual(a["origin"], gen.HINGE)
        self.assertEqual(b["origin"], gen.HINGE)
        self.assertEqual(a["rotation"], [0, 0, 0])
        self.assertEqual(b["rotation"], [-105, 0, 0])
        b["rotation"] = a["rotation"]
        self.assertEqual(closed, opened)

    def test_no_beam_or_glow_geometry(self):
        for model in self.models:
            for element in model["elements"]:
                self.assertNotRegex(element["name"].lower(), r"beam|glow")

    def test_every_element_has_exactly_one_parent(self):
        for model in self.models:
            ids = [e["uuid"] for e in model["elements"]]
            grouped = [child for g in model["outliner"] for child in g["children"]]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(sorted(ids), sorted(grouped))
            self.assertEqual(len(grouped), len(set(grouped)))

    def test_embedded_texture_matches_atlas(self):
        texture = (ROOT / self.texture_name).read_bytes()
        for model in self.models:
            self.assertEqual(model["textures"][0]["name"], self.texture_name)
            self.assertEqual(model["meta"]["model_format"], "free")
            self.assertEqual(model["resolution"], {"width": 512, "height": 512})
            data = base64.b64decode(model["textures"][0]["source"].split(",", 1)[1])
            self.assertEqual(data, texture)
            self.assertEqual(Image.open(io.BytesIO(data)).size, (512, 512))

    def test_valid_uvs_and_nonzero_geometry(self):
        for element in self.models[0]["elements"]:
            with self.subTest(element=element["name"]):
                if element["type"] == "cube":
                    self.assertTrue(all(b > a for a, b in zip(element["from"], element["to"])))
                    for face in element["faces"].values():
                        self.assertEqual(face["texture"], 0)
                        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 512 for v in face["uv"]))
                    continue
                vertices = element["vertices"]
                edge_counts = {}
                for face in element["faces"].values():
                    keys = face["vertices"]
                    self.assertIn(len(keys), (3, 4))
                    self.assertEqual(set(keys), set(face["uv"]))
                    self.assertEqual(face["texture"], 0)
                    for uv in face["uv"].values():
                        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 512 for v in uv))
                    v = [vertices[k] for k in keys]
                    n = gen.cross(gen.sub(v[1], v[0]), gen.sub(v[2], v[0]))
                    self.assertGreater(gen.dot(n, n), 1e-12)
                    if len(v) == 4:
                        self.assertAlmostEqual(gen.dot(n, gen.sub(v[3], v[0])), 0, delta=1e-3)
                    for a, b in zip(keys, keys[1:] + keys[:1]):
                        edge = tuple(sorted((a, b)))
                        edge_counts[edge] = edge_counts.get(edge, 0) + 1
                self.assertTrue(all(count == 2 for count in edge_counts.values()),
                                "Each solid must be watertight.")

    def test_hollow_body_and_opening_direction(self):
        model = self.models[0]
        body = next(g for g in model["outliner"] if g["name"] == "woodwork")
        elements = {e["uuid"]: e for e in model["elements"]}
        for child in body["children"]:
            e = elements[child]
            # The central cavity, above the floor, is not occupied by a solid block.
            if e["to"][1] > 3:
                self.assertFalse(e["from"][0] < 0 < e["to"][0] and
                                 e["from"][2] < 0 < e["to"][2])
        angle = math.radians(-105)
        front = [0, 12, 8.5]
        delta = gen.sub(front, gen.HINGE)
        y = gen.HINGE[1] + math.cos(angle)*delta[1] - math.sin(angle)*delta[2]
        z = gen.HINGE[2] + math.sin(angle)*delta[1] + math.cos(angle)*delta[2]
        self.assertGreater(y, 27)
        self.assertLess(z, gen.HINGE[2])

    def test_archive_contains_current_deliverables(self):
        with zipfile.ZipFile(ROOT / f"{self.prefix}.zip") as archive:
            self.assertIsNone(archive.testzip())
            expected = [f"{self.prefix}.bbmodel", f"{self.prefix}_open.bbmodel",
                        self.texture_name, self.preview_name, "README.md"]
            self.assertEqual(sorted(archive.namelist()), sorted(expected))
            for name in expected:
                self.assertEqual(archive.read(name), (ROOT / name).read_bytes())

    def test_generation_is_reproducible(self):
        self.assertEqual(hashlib.sha256(gen.atlas(self.epic)).digest(),
                         hashlib.sha256((ROOT / self.texture_name).read_bytes()).digest())
        generated = gen.build().export(False, gen.atlas(self.epic), self.epic)
        self.assertEqual(generated, self.models[0])


class EpicChestModelsTest(ChestModelsTest):
    epic = True
    prefix = "Epic_chest"
    texture_name = "epic_chest_atlas.png"
    preview_name = "epic_preview.png"

    def test_epic_preserves_regular_geometry(self):
        for opened, model in zip((False, True), self.models):
            name = "Regular_chest_open.bbmodel" if opened else "Regular_chest.bbmodel"
            regular = json.loads((ROOT / name).read_text())
            self.assertEqual(model["elements"], regular["elements"])
            self.assertEqual(model["outliner"], regular["outliner"])
            self.assertNotEqual(model["textures"][0]["source"], regular["textures"][0]["source"])

    def test_epic_palette_is_plum_and_gold_not_blue(self):
        image = Image.open(ROOT / self.texture_name).convert("RGB")
        # A warm palette has no blue-dominant pixels, including its treasure.
        red, _, blue = image.split()
        self.assertIsNone(ImageChops.subtract(blue, red).getbbox())
        wood = image.getpixel((32, 32))
        gold = image.getpixel((32, 96))
        self.assertGreater(wood[0], wood[1] + 30)
        self.assertGreater(wood[2], wood[1] + 30)
        self.assertGreater(gold[0], gold[1])
        self.assertGreater(gold[1], gold[2])


if __name__ == "__main__":
    unittest.main()
