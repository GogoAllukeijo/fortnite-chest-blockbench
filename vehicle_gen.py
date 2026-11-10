"""Build the original SkyManta courier using the shared mesh primitives."""

import base64
import io
import json
import math
from pathlib import Path
import random
import uuid
import zipfile

from PIL import Image, ImageDraw, ImageFont

from gen import Model, NAMES, dot, sub


ROOT = Path(__file__).resolve().parent
CREAM, WHITE, ORANGE = "oak_light", "oak_warm", "oak_honey"
DARK, METAL, COPPER = "iron", "iron_light", "brass"
GLASS, REFLECTION = "teal_dark", "teal_light"
# Slot names match the shared UV layout, but the artwork is vehicle-specific.
LIGHT = "coin_face"
PALETTE = {
    CREAM: (218, 210, 178), WHITE: (245, 238, 210), ORANGE: (204, 84, 40),
    "oak_shade": (116, 46, 30), "oak_amber": (229, 115, 49),
    "oak_end": (187, 176, 141), "inside": (63, 53, 43), "wood_edge": (110, 97, 72),
    COPPER: (187, 111, 58), "brass_light": (244, 181, 102),
    "brass_dark": (102, 65, 38), "brass_edge": (250, 212, 150),
    DARK: (32, 40, 43), METAL: (87, 100, 100), "keyhole": (14, 23, 27),
    "leather": (84, 63, 47), "coin": (240, 156, 47), "coin_edge": (138, 83, 28),
    LIGHT: (255, 226, 146), "teal": (36, 90, 92),
    REFLECTION: (116, 176, 169), GLASS: (19, 51, 61),
    "violet": (202, 67, 45), "violet_light": (254, 145, 75),
    "violet_dark": (104, 35, 29), "lining": (38, 51, 49),
}
PODS = [(sx*25, z) for sx in (-1, 1) for z in (-12, 12)]


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "skymanta-original/" + name))


def texture():
    image = Image.new("RGB", (512, 512), (28, 33, 36))
    for i, name in enumerate(NAMES):
        rng = random.Random(4200+i)
        base = PALETTE[name]
        tile = Image.new("RGB", (64, 64))
        for y in range(64):
            for x in range(64):
                light = rng.uniform(-1.3, 1.3) + 6*(1-y/64)
                tile.putpixel((x, y), tuple(max(0, min(255, round(v+light))) for v in base))
        d = ImageDraw.Draw(tile)
        if name in (CREAM, WHITE, ORANGE, "oak_amber", "oak_end"):
            d.line((2, 61, 61, 61), fill=tuple(max(0, v-24) for v in base))
            d.line((2, 2, 61, 2), fill=tuple(min(255, v+19) for v in base))
            for _ in range(8):
                x, y = rng.randrange(5, 57), rng.randrange(5, 58)
                d.line((x, y, x+3, y), fill=tuple(max(0, v-13) for v in base))
        if name == GLASS:
            d.polygon([(3, 0), (12, 0), (55, 64), (46, 64)], fill=(37, 77, 86))
            d.polygon([(17, 0), (20, 0), (63, 64), (60, 64)], fill=(51, 96, 100))
        image.paste(tile, ((i % 8)*64, (i // 8)*64))
    image.save(ROOT / "SkyManta_atlas.png")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def markings():
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    bold = ImageFont.load_default(size=48)
    small = ImageFont.load_default(size=22)
    d.text((14, 15), "SKYMANTA", font=bold, fill=(44, 49, 45))
    d.text((17, 78), "AERIAL COURIER / 07", font=small, fill=(95, 78, 55))
    d.rounded_rectangle((350, 8, 504, 114), radius=16, fill=(196, 74, 35))
    d.text((385, 25), "07", font=ImageFont.load_default(size=66), fill=(255, 235, 190))
    for x in range(-20, 540, 40):
        d.polygon([(x, 140), (x+20, 140), (x+52, 190), (x+32, 190)],
                  fill=(225, 146, 45))
    # Original manta emblem, not a game logo.
    d.polygon([(128, 222), (153, 266), (234, 295), (177, 307), (144, 294),
               (128, 347), (112, 294), (79, 307), (22, 295), (103, 266)],
              fill=(237, 215, 164))
    d.line([(128, 287), (128, 374)], fill=(237, 215, 164), width=7)
    d.text((275, 242), "LIFT", font=bold, fill=(246, 231, 195))
    d.text((278, 299), "KEEP CLEAR", font=small, fill=(246, 231, 195))
    d.polygon([(370, 390), (420, 440), (395, 440), (395, 490),
               (345, 490), (345, 440), (320, 440)], fill=(230, 120, 55))
    image.save(ROOT / "SkyManta_markings.png")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


class Vehicle(Model):
    def add(self, group, element):
        super().add(group, element)
        old = element["uuid"]
        element["uuid"] = uid(element["name"])
        self.groups[group][self.groups[group].index(old)] = element["uuid"]

    def rod(self, group, name, a, b, radius, material):
        axis = sub(b, a)
        self.cylinder(group, name, [(v+w)/2 for v, w in zip(a, b)], axis,
                      radius, math.sqrt(dot(axis, axis)), material, material)

    def decal(self, name, vertices, uv):
        keys = [f"v{i}" for i in range(4)]
        self.add("markings", {
            "type": "mesh", "name": name, "origin": [0, 0, 0], "rotation": [0, 0, 0],
            "vertices": {key: list(v) for key, v in zip(keys, vertices)},
            "faces": {"front": {"vertices": keys, "texture": 1,
                                "uv": {key: list(v) for key, v in zip(keys, uv)}}},
        })

    def ring(self, name, center, outer, inner, y0, y1, material, lip=False):
        x, z = center
        for i in range(20):
            a, b = 2*math.pi*i/20, 2*math.pi*(i+1)/20
            polygon = [(x+r*math.cos(t), z+r*math.sin(t))
                       for r, t in ((outer, a), (outer, b), (inner, b), (inner, a))]
            self.prism("lift_ducts", f"{name}_{i:02}", polygon, y0, y1, 1,
                       material, "brass_light" if lip else material)


def build():
    m = Vehicle()
    # Eight-point sections form a broad, faceted manta body rather than a vehicle cab.
    sections = [(29, 3.8, 10.5, 16), (21, 9.4, 8.5, 20),
                (7, 12, 7.5, 21), (-12, 10.8, 8.2, 20), (-23, 6, 10.5, 16)]

    def section(z, w, low, high):
        return [(-w*.68, low, z), (w*.68, low, z), (w, low+2.7, z),
                (w, high-2.2, z), (w*.68, high, z), (-w*.68, high, z),
                (-w, high-2.2, z), (-w, low+2.7, z)]

    for i, (a, b) in enumerate(zip(sections, sections[1:])):
        vertices = section(*a) + section(*b)
        faces = [[j, (j+1)%8, (j+1)%8+8, j+8] for j in range(8)]
        for off in (0, 8):
            faces.extend([[off, off+j, off+j+1] for j in range(1, 7)])
        # Tapered hull sections can contain non-planar side quads.
        triangles = []
        colors = {}
        for index, face in enumerate(faces):
            material = (DARK if index in (0, 1, 7) else ORANGE if index in (2, 6)
                        else WHITE if index == 4 else CREAM)
            for tri in ([face[:3], [face[0], face[2], face[3]]] if len(face) == 4 else [face]):
                colors[len(triangles)] = material
                triangles.append(tri)
        m.solid("airframe", f"hull_section_{i}", vertices, triangles, CREAM, colors)

    # Cream deck and split swept wings are supported by thick copper spars.
    m.plate("airframe", "cargo_deck", [-8, -15], [8, 7], 20, 21.3, 1, CREAM, 2)
    for sx in (-1, 1):
        for z in (-12, 12):
            m.prism("wings", f"lift_arm_{sx}_{z}",
                    [(sx*8, z-3.1), (sx*20, z-2.6), (sx*20, z+2.6), (sx*8, z+3.1)],
                    12, 14, 1, ORANGE, DARK)
            m.rod("wings", f"arm_piston_{sx}_{z}", [sx*10, 10.8, z],
                  [sx*19.5, 12.5, z], .75, METAL)
        m.prism("wings", f"swept_wing_{sx}",
                [(sx*10, 2.5), (sx*17, 6), (sx*37, -13),
                 (sx*35, -22), (sx*16, -18), (sx*10, -9)],
                11.6, 12.5, 1, CREAM, ORANGE)
        m.prism("wings", f"wingtip_{sx}",
                [(12, -21), (12, -13), (19.5, -18), (18, -23)],
                min(sx*35, sx*36.2), max(sx*35, sx*36.2), 0, ORANGE, CREAM)
        m.rod("wings", f"wing_edge_{sx}", [sx*17, 12.7, 5], [sx*36, 12.7, -13], .27, COPPER)

    # Four genuinely open ducts with individual rotating impellers.
    for index, (x, z) in enumerate(PODS):
        tag = f"pod_{index+1}"
        m.ring(tag+"_lower", (x, z), 8.1, 6.4, 10.7, 12.2, DARK)
        m.ring(tag+"_shell", (x, z), 8.7, 6.4, 12.2, 16.3, CREAM)
        m.ring(tag+"_orange_lip", (x, z), 8.9, 6.35, 16.3, 16.85, ORANGE)
        m.ring(tag+"_inner_rim", (x, z), 6.62, 6.35, 16.86, 17.12, COPPER, True)
        m.ring(tag+"_inner_wall", (x, z), 6.4, 6.19, 12.3, 16.25, DARK)
        for spoke in range(3):
            a = 2*math.pi*spoke/3
            m.rod("lift_ducts", f"{tag}_stator_{spoke}", [x, 12.6, z],
                  [x+6.3*math.cos(a), 12.6, z+6.3*math.sin(a)], .22, METAL)
        group = f"rotor_{index+1}"
        m.cylinder(group, f"{tag}_hub", [x, 14.4, z], [0, 1, 0], 1.3, 2.2, DARK, COPPER, 12)
        m.cylinder(group, f"{tag}_cap", [x, 15.55, z], [0, 1, 0], .8, .25, COPPER, "brass_light")
        for blade in range(6):
            a = 2*math.pi*blade/6
            def rotate(u, v):
                return (x+u*math.cos(a)-v*math.sin(a), z+u*math.sin(a)+v*math.cos(a))
            poly = [rotate(u, v) for u, v in ((.9, -.3), (4.8, -1.3), (5.9, -.65), (5.4, .45), (1.2, .5))]
            m.prism(group, f"{tag}_blade_{blade}", poly, 14.35, 14.6, 1, METAL, DARK)
            tip = [rotate(u, v) for u, v in ((4.7, -.75), (5.55, -.57), (5.25, .16), (4.6, .3))]
            m.prism(group, f"{tag}_blade_tip_{blade}", tip, 14.61, 14.65, 1, "coin")
        for a in (0, math.pi/2, math.pi, math.pi*1.5):
            px, pz = x+7.6*math.cos(a), z+7.6*math.sin(a)
            m.cylinder("hardware", f"{tag}_rim_fastener_{a}", [px, 16.93, pz],
                       [0, 1, 0], .21, .16, DARK, METAL)
        m.plate("hardware", tag+"_status_housing", [x-1.6, z-8.74], [x+1.6, z-8.3],
                13.2, 14.5, 1, DARK, .15)

    # Low, angular panoramic cockpit: painted reflective glazing with structural mullions.
    canopy = [(-6.5, 19, 11), (6.5, 19, 11), (5.2, 19.2, 23), (-5.2, 19.2, 23),
              (-4.6, 26.4, 11), (4.6, 26.4, 11), (3.7, 23.8, 20.5), (-3.7, 23.8, 20.5)]
    faces = [[0, 1, 2], [0, 2, 3], [4, 7, 6], [4, 6, 5],
             [3, 2, 6], [3, 6, 7], [0, 3, 7], [0, 7, 4],
             [2, 1, 5], [2, 5, 6], [1, 0, 4], [1, 4, 5]]
    m.solid("cockpit", "panoramic_glazing", canopy, faces, GLASS, {0: DARK, 1: DARK, 10: ORANGE, 11: ORANGE})
    for i, (a, b) in enumerate(((0, 3), (3, 2), (2, 1), (1, 0), (4, 7), (7, 6),
                                (6, 5), (5, 4), (0, 4), (1, 5), (2, 6), (3, 7))):
        m.rod("cockpit", f"canopy_frame_{i}", canopy[a], canopy[b], .24, CREAM)
    m.rod("cockpit", "center_windshield_bar", [0, 19.2, 23.1], [0, 23.85, 20.55], .16, COPPER)
    m.plate("cockpit", "roof_spine", [-1.4, 8.8], [1.4, 12], 26.1, 26.7, 1, ORANGE, .35)
    for sx in (-1, 1):
        m.rod("cockpit", f"nose_rail_{sx}", [sx*6.3, 18.5, 23], [sx*3.1, 16.9, 28], .35, COPPER)
        m.plate("hardware", f"headlight_bezel_{sx}", [sx*2.7-1.25, 12.6], [sx*2.7+1.25, 14.5],
                28.95, 29.25, 2, DARK, .3)
        m.plate("hardware", f"headlight_lens_{sx}", [sx*2.7-.85, 12.95], [sx*2.7+.85, 14.15],
                29.26, 29.42, 2, LIGHT, .2)

    # Accessible cargo bay roof, latches, service grilles and a rear loading hatch.
    m.plate("cargo", "cargo_hatch_recess", [-6, -12], [6, 6], 21.32, 21.52, 1, DARK, 1)
    m.plate("cargo", "cargo_hatch", [-5.65, -11.65], [5.65, 5.65], 21.53, 21.85, 1, ORANGE, 1)
    for x in (-5.2, 5.2):
        for z in (-8, 2):
            m.cube("cargo", f"hatch_lock_{x}_{z}", [x-.3, 21.86, z-.8], [x+.3, 22.2, z+.8], METAL)
    for z in (-13.6, 7):
        m.rod("cargo", f"deck_handle_{z}", [-3, 21.7, z], [3, 21.7, z], .22, COPPER)
    for sx in (-1, 1):
        for z in (-8, -5, -2, 1):
            m.plate("hardware", f"side_port_{sx}_{z}", [11.3, z-.95], [14.4, z+.95],
                    min(sx*11.06, sx*11.28), max(sx*11.06, sx*11.28), 0, DARK, .3)
        m.plate("hardware", f"deck_vent_{sx}", [sx*7.4-.7, -9], [sx*7.4+.7, 3],
                21.32, 21.53, 1, DARK, .3)
        for z in range(-8, 4, 2):
            m.cube("hardware", f"vent_louver_{sx}_{z}",
                   [sx*7.4-.6, 21.54, z-.16], [sx*7.4+.6, 21.78, z+.16], METAL)
    m.plate("cargo", "rear_door", [-4.3, 11.2], [4.3, 15.8], -23.23, -23.02, 2, DARK, .65)
    for x in (-2.15, 2.15):
        m.plate("cargo", f"rear_door_panel_{x}", [x-1.98, 11.4], [x+1.98, 15.55],
                -23.38, -23.24, 2, CREAM, .35)

    # Twin rear fins and propulsion nozzles, without balloon rigging.
    for sx in (-1, 1):
        m.prism("tail", f"tail_boom_{sx}", [(sx*5, -16), (sx*9, -17), (sx*9, -34), (sx*6, -35)],
                13, 15, 1, CREAM, ORANGE)
        m.prism("tail", f"tail_fin_{sx}", [(13.6, -23), (25, -31), (24, -35), (13.6, -34)],
                min(sx*7.3, sx*8.15), max(sx*7.3, sx*8.15), 0, ORANGE, CREAM)
        m.rod("tail", f"tail_fin_trim_{sx}", [sx*7.7, 25, -31], [sx*7.7, 24, -35], .22, COPPER)
        m.cylinder("propulsion", f"rear_motor_{sx}", [sx*5.7, 10.3, -21.7], [0, 0, 1],
                   2.5, 5, METAL, DARK, 12)
        m.cylinder("propulsion", f"exhaust_rim_{sx}", [sx*5.7, 10.3, -24.35], [0, 0, 1],
                   2.3, .45, COPPER, "brass_dark", 12)
        m.cylinder("propulsion", f"exhaust_recess_{sx}", [sx*5.7, 10.3, -24.62], [0, 0, 1],
                   1.8, .16, DARK, "keyhole", 12)
        m.cylinder("propulsion", f"exhaust_core_{sx}", [sx*5.7, 10.3, -24.74], [0, 0, 1],
                   1.15, .16, ORANGE, LIGHT, 12)
        m.rod("landing_gear", f"skid_{sx}", [sx*9, 1.5, -13], [sx*9, 1.5, 17], .7, DARK)
        m.rod("landing_gear", f"skid_nose_{sx}", [sx*9, 1.5, 17], [sx*9, 3.2, 20], .7, COPPER)
        for z in (-10, 13):
            m.rod("landing_gear", f"strut_{sx}_{z}", [sx*7, 8.8, z], [sx*9, 2, z], .5, METAL)
            m.rod("landing_gear", f"strut_sleeve_{sx}_{z}", [sx*7, 8.8, z], [sx*8, 5.5, z], .8, ORANGE)
    m.rod("hardware", "aerial_mast", [0, 21, -15], [0, 29, -17], .14, METAL)
    m.cylinder("hardware", "amber_beacon", [0, 29.4, -17], [0, 1, 0], .45, .8, ORANGE, LIGHT)
    m.rod("hardware", "pitot_tube", [0, 13.8, 29], [0, 13.8, 32], .15, METAL)

    m.decal("manta_roof_emblem", [(-4.3, 21.87, -7.5), (-4.3, 21.87, 3.2),
                                  (4.3, 21.87, 3.2), (4.3, 21.87, -7.5)],
            [(0, 384), (0, 210), (256, 210), (256, 384)])
    m.decal("deck_07", [(-2, 21.88, -11), (-2, 21.88, -8),
                        (2, 21.88, -8), (2, 21.88, -11)],
            [(350, 0), (350, 116), (512, 116), (512, 0)])
    for sx in (-1, 1):
        x = sx*8.18
        verts = [(x, 15.8, -24.7), (x, 22.5, -30.4),
                 (x, 22.5, -33.6), (x, 15.8, -33.6)]
        uv = [(350, 116), (350, 0), (512, 0), (512, 116)]
        if sx == -1:
            uv = [(862-u, v) for u, v in uv]
        if sx == 1:
            verts.reverse()
            uv.reverse()
        m.decal(f"tail_07_{sx}", verts, uv)
        def side_x(z):
            return sx*(12+(z-7)*1.2/19+.025)
        verts = [(side_x(5), 14.8, 5), (side_x(5), 17.4, 5),
                 (side_x(-9), 17.4, -9), (side_x(-9), 14.8, -9)]
        uv = [(0, 116), (0, 0), (340, 0), (340, 116)]
        if sx == -1:
            uv = [(340-u, v) for u, v in uv]
        if sx == 1:
            verts.reverse()
            uv.reverse()
        m.decal(f"fuselage_name_{sx}", verts, uv)
    return m


def export(model, atlas, decals):
    groups, animators = [], {}
    for name, children in model.groups.items():
        pivot = [0, 0, 0]
        if name.startswith("rotor_"):
            index = int(name[-1])-1
            x, z = PODS[index]
            pivot = [x, 14.4, z]
            direction = 1 if index in (0, 3) else -1
            animators[uid("group/"+name)] = {
                "name": name, "type": "bone",
                "keyframes": [{"channel": "rotation", "time": t, "interpolation": "linear",
                               "uuid": uid(f"{name}/key/{t}"),
                               "data_points": [{"x": "0", "y": str(direction*360*t), "z": "0"}]}
                              for t in (0, .25, .5, .75, 1)],
            }
        groups.append({"name": name, "uuid": uid("group/"+name), "origin": pivot,
                       "rotation": [0, 0, 0], "children": children, "export": True,
                       "visibility": True, "isOpen": False})
    textures = []
    for i, (name, data) in enumerate((("SkyManta_atlas.png", atlas), ("SkyManta_markings.png", decals))):
        textures.append({"name": name, "id": str(i), "uuid": uid(name), "width": 512, "height": 512,
                         "uv_width": 512, "uv_height": 512, "render_mode": "default",
                         "render_sides": "front", "internal": True, "saved": True, "visible": True,
                         "source": "data:image/png;base64,"+base64.b64encode(data).decode()})
    return {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": "SkyManta", "resolution": {"width": 512, "height": 512},
            "elements": model.elements, "outliner": groups, "textures": textures,
            "animations": [{"name": "rotors_spin", "uuid": uid("animation/rotors"),
                            "loop": "loop", "length": 1, "snapping": 24, "animators": animators}]}


def main():
    model = build()
    data = export(model, texture(), markings())
    (ROOT / "SkyManta.bbmodel").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    files = ["SkyManta.bbmodel", "SkyManta_atlas.png", "SkyManta_markings.png", "SkyManta_README.md"]
    # Allow the initial model build before its first Blockbench preview is captured.
    if (ROOT / "SkyManta_preview.png").exists():
        files.append("SkyManta_preview.png")
    with zipfile.ZipFile(ROOT / "SkyManta.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, (ROOT / name).read_bytes())
    print(f"Generated SkyManta: {len(model.elements)} editable parts, four animated rotors.")


if __name__ == "__main__":
    main()
