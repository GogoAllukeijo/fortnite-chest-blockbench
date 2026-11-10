"""Verify the downloadable vehicle, mesh surfaces and actual animation data."""

import base64
import io
import json
import math
import unittest
import zipfile

from PIL import Image

import vehicle_gen as vehicle
from gen import cross, dot, sub


class SkyMantaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads((vehicle.ROOT / "SkyManta.bbmodel").read_text())

    def test_texture_payloads_and_uvs(self):
        self.assertEqual(self.model["name"], "SkyManta")
        self.assertEqual(self.model["meta"]["model_format"], "free")
        for texture in self.model["textures"]:
            payload = base64.b64decode(texture["source"].split(",", 1)[1])
            self.assertEqual(payload, (vehicle.ROOT / texture["name"]).read_bytes())
            self.assertEqual(Image.open(io.BytesIO(payload)).size, (512, 512))
        for element in self.model["elements"]:
            for face in element["faces"].values():
                self.assertIn(face["texture"], (0, 1))
                uv = face["uv"]
                numbers = [n for pair in uv.values() for n in pair] if isinstance(uv, dict) else uv
                self.assertTrue(all(math.isfinite(n) and 0 <= n <= 512 for n in numbers))

    def test_unique_elements_and_group_membership(self):
        ids = [e["uuid"] for e in self.model["elements"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len({e["name"] for e in self.model["elements"]}), len(ids))
        children = [c for g in self.model["outliner"] for c in g["children"]]
        self.assertEqual(sorted(children), sorted(ids))
        self.assertGreater(len(ids), 300)

    def test_valid_solid_geometry_and_decal_normals(self):
        for element in self.model["elements"]:
            with self.subTest(element=element["name"]):
                if element["type"] == "cube":
                    self.assertTrue(all(a < b for a, b in zip(element["from"], element["to"])))
                    continue
                vertices = element["vertices"]
                edges = {}
                for face in element["faces"].values():
                    keys = face["vertices"]
                    self.assertIn(len(keys), (3, 4))
                    v = [vertices[k] for k in keys]
                    normal = cross(sub(v[1], v[0]), sub(v[2], v[0]))
                    self.assertGreater(dot(normal, normal), 1e-10)
                    if len(v) == 4:
                        self.assertAlmostEqual(dot(normal, sub(v[3], v[0])), 0, delta=.02)
                    if face["texture"] == 1:
                        if element["name"].startswith(("manta_", "deck_")):
                            self.assertGreater(normal[1], 0)
                        elif element["name"].startswith(("tail_", "fuselage_")):
                            self.assertGreater(normal[0]*int(element["name"].split("_")[-1]), 0)
                    for a, b in zip(keys, keys[1:]+keys[:1]):
                        edge = tuple(sorted((a, b)))
                        edges[edge] = edges.get(edge, 0)+1
                if not any(f["texture"] == 1 for f in element["faces"].values()):
                    self.assertTrue(all(count == 2 for count in edges.values()))

    def test_four_rotors_stay_inside_the_ducts(self):
        elements = {e["uuid"]: e for e in self.model["elements"]}
        rotors = [g for g in self.model["outliner"] if g["name"].startswith("rotor_")]
        self.assertEqual(len(rotors), 4)
        for group, (x, z) in zip(rotors, vehicle.PODS):
            self.assertEqual(group["origin"], [x, 14.4, z])
            names = [elements[c]["name"] for c in group["children"]]
            self.assertEqual(len([name for name in names if "_blade_" in name and "_tip_" not in name]), 6)
            for child in group["children"]:
                for px, py, pz in elements[child]["vertices"].values():
                    self.assertLess(math.hypot(px-x, pz-z), 6.19)
                    self.assertGreater(py, 12.9)
                    self.assertLess(py, 16.3)

    def test_side_lettering_is_not_mirrored(self):
        for element in self.model["elements"]:
            if not element["name"].startswith(("fuselage_name_", "tail_07_")):
                continue
            side = int(element["name"].split("_")[-1])
            vertices = element["vertices"]
            uv = element["faces"]["front"]["uv"]
            front = max(vertices, key=lambda key: vertices[key][2])
            rear = min(vertices, key=lambda key: vertices[key][2])
            self.assertLess((uv[front][0]-uv[rear][0])*side, 0)

    def test_loop_animation_targets_only_rotors(self):
        animation, = self.model["animations"]
        self.assertEqual(animation["loop"], "loop")
        self.assertEqual(animation["length"], 1)
        rotors = {g["uuid"]: g for g in self.model["outliner"] if g["name"].startswith("rotor_")}
        self.assertEqual(set(animation["animators"]), set(rotors))
        directions = []
        for animator in animation["animators"].values():
            keys = animator["keyframes"]
            self.assertEqual([k["time"] for k in keys], [0, .25, .5, .75, 1])
            for k in keys:
                self.assertEqual(k["interpolation"], "linear")
                self.assertEqual(k["channel"], "rotation")
            directions.append(float(keys[-1]["data_points"][0]["y"]))
        self.assertEqual(sorted(directions), [-360, -360, 360, 360])

    def test_generation_is_reproducible(self):
        generated = vehicle.export(vehicle.build(),
                                   (vehicle.ROOT / "SkyManta_atlas.png").read_bytes(),
                                   (vehicle.ROOT / "SkyManta_markings.png").read_bytes())
        self.assertEqual(generated, self.model)

    def test_archive_contains_all_deliverables(self):
        with zipfile.ZipFile(vehicle.ROOT / "SkyManta.zip") as archive:
            self.assertIsNone(archive.testzip())
            expected = ["SkyManta.bbmodel", "SkyManta_atlas.png", "SkyManta_markings.png",
                        "SkyManta_README.md", "SkyManta_preview.png"]
            self.assertEqual(sorted(archive.namelist()), sorted(expected))
            for name in expected:
                self.assertEqual(archive.read(name), (vehicle.ROOT / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
