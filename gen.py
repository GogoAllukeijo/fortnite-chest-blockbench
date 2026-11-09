"""Generate Regular and Epic chest poses, textures and download archives."""

import base64
import io
import json
import math
from pathlib import Path
import random
import uuid
import zipfile

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
SIZE, TILE = 512, 64
HINGE = [0, 12, -8.6]
MATERIALS = {
    "oak_honey": (150, 83, 33),
    "oak_warm": (170, 99, 41),
    "oak_light": (188, 118, 52),
    "oak_shade": (128, 65, 27),
    "oak_amber": (160, 88, 34),
    "oak_end": (145, 78, 31),
    "inside": (82, 43, 24),
    "wood_edge": (105, 53, 24),
    "brass": (200, 143, 49),
    "brass_light": (238, 189, 88),
    "brass_dark": (123, 80, 31),
    "brass_edge": (251, 211, 121),
    "iron": (41, 52, 57),
    "iron_light": (75, 88, 89),
    "keyhole": (22, 24, 24),
    "leather": (78, 42, 27),
    "coin": (231, 173, 53),
    "coin_edge": (163, 106, 28),
    "coin_face": (245, 194, 75),
    "teal": (29, 122, 116),
    "teal_light": (80, 204, 177),
    "teal_dark": (14, 70, 77),
    "violet": (119, 62, 167),
    "violet_light": (192, 127, 225),
    "violet_dark": (63, 35, 101),
    "lining": (29, 65, 64),
}
NAMES = list(MATERIALS)
EPIC_MATERIALS = {
    "oak_honey": (127, 43, 111),
    "oak_warm": (147, 55, 131),
    "oak_light": (166, 69, 147),
    "oak_shade": (101, 31, 88),
    "oak_amber": (140, 45, 122),
    "oak_end": (124, 40, 108),
    "inside": (69, 26, 54),
    "wood_edge": (91, 28, 76),
    "brass": (215, 164, 92),
    "brass_light": (250, 214, 148),
    "brass_dark": (139, 94, 47),
    "brass_edge": (255, 232, 183),
    "iron": (48, 32, 42),
    "iron_light": (89, 61, 76),
    "keyhole": (24, 19, 21),
    "leather": (75, 29, 48),
    "teal": (223, 118, 32),
    "teal_light": (255, 205, 95),
    "teal_dark": (119, 53, 20),
    "violet": (189, 43, 85),
    "violet_light": (255, 127, 151),
    "violet_dark": (90, 20, 45),
    "lining": (60, 22, 43),
}


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "stylized-chest-v2/" + name))


def shade(rgb, amount):
    return tuple(max(0, min(255, round(c + amount))) for c in rgb)


def atlas(epic=False):
    image = Image.new("RGB", (SIZE, SIZE), (34, 30, 28))
    for index, (name, base) in enumerate(MATERIALS.items()):
        if epic:
            base = EPIC_MATERIALS.get(name, base)
        rng = random.Random(490 + index)
        tile = Image.new("RGB", (TILE, TILE))
        wood = name.startswith("oak") or name in ("inside", "wood_edge")
        for y in range(TILE):
            for x in range(TILE):
                light = 5 * math.sin(y * .17) + rng.uniform(-2.2, 2.2)
                if wood:
                    light += 6 * math.sin(y * .51 + math.sin(x * .085))
                else:
                    light += 9 * (1 - y / TILE)
                tile.putpixel((x, y), shade(base, light))
        draw = ImageDraw.Draw(tile)
        if wood:
            for row in range(5, 64, 8):
                phase = rng.random() * 6
                points = [(x, row + round(1.7 * math.sin(x * .095 + phase)))
                          for x in range(2, 62)]
                draw.line(points, fill=shade(base, -25), width=1)
                draw.line([(x, y + 1) for x, y in points], fill=shade(base, 12))
            if name.startswith("oak"):
                cx, cy = rng.randint(18, 45), rng.randint(19, 44)
                for rx, ry in ((11, 5), (7, 3), (3, 1)):
                    draw.ellipse((cx-rx, cy-ry, cx+rx, cy+ry), outline=shade(base, -31))
                draw.line((cx-13, cy, cx+12, cy), fill=shade(base, -20))
            for _ in range(6):
                x, y = rng.randint(5, 45), rng.randint(4, 59)
                draw.line((x, y, x + rng.randint(6, 14), y), fill=shade(base, 18))
        elif name.startswith("brass"):
            for _ in range(22):
                x, y = rng.randint(4, 55), rng.randint(3, 60)
                draw.line((x, y, min(61, x + rng.randint(2, 9)), y-1),
                          fill=shade(base, rng.choice((-15, 16, 23))))
            draw.line((2, 2, 61, 2), fill=shade(base, 27), width=2)
            draw.line((2, 61, 61, 61), fill=shade(base, -23), width=2)
        elif name == "coin_face":
            draw.ellipse((5, 5, 58, 58), outline=shade(base, -45), width=2)
            draw.ellipse((9, 9, 54, 54), outline=shade(base, 28))
            draw.polygon([(32, 14), (44, 32), (32, 49), (20, 32)],
                         fill=shade(base, -27))
            draw.line((32, 17, 23, 32, 32, 45), fill=shade(base, 34), width=2)
        elif name in ("lining", "leather"):
            for y in range(3, 63, 5):
                draw.line((2, y, 61, y), fill=shade(base, 5))
            for x in range(5, 62, 7):
                draw.line((x, 3, x, 60), fill=shade(base, -3))
        image.paste(tile, ((index % 8) * TILE, (index // 8) * TILE))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def uv_bounds(material):
    index = NAMES.index(material)
    x, y = index % 8 * TILE, index // 8 * TILE
    return [x + 2, y + 2, x + 62, y + 62]


def loot_texture(epic=False):
    """Paint a dense, opaque treasure pile in the opening's aspect ratio."""
    scale = 3
    width, height = 512, 320
    rng = random.Random(901)
    image = Image.new("RGB", (width*scale, height*scale), (100, 54, 18))
    draw = ImageDraw.Draw(image)

    def box(x0, y0, x1, y1):
        return tuple(round(v*scale) for v in (x0, y0, x1, y1))

    def points(vertices):
        return [(round(x*scale), round(y*scale)) for x, y in vertices]

    def coin(x, y, radius):
        ry = radius*rng.uniform(.8, 1)
        tone = rng.choice(((223, 157, 41), (240, 178, 52), (204, 132, 30),
                           (245, 193, 75), (224, 161, 48)))
        draw.ellipse(box(x-radius-2, y-ry+3, x+radius+2, y+ry+6), fill=(82, 43, 16))
        draw.ellipse(box(x-radius, y-ry+2, x+radius, y+ry+4), fill=(143, 83, 22))
        draw.ellipse(box(x-radius, y-ry, x+radius, y+ry), fill=tone,
                     outline=(139, 86, 23), width=scale)
        draw.arc(box(x-radius+1, y-ry+1, x+radius-1, y+ry-1), 190, 310,
                 fill=(255, 227, 140), width=2*scale)
        draw.ellipse(box(x-radius*.72, y-ry*.72, x+radius*.72, y+ry*.72),
                     outline=shade(tone, -28), width=scale)
        r = radius*.38
        diamond = [(x, y-r), (x+r*.7, y), (x, y+r), (x-r*.7, y)]
        draw.polygon(points(diamond), fill=shade(tone, -21))
        draw.line(points(diamond[:2]), fill=shade(tone, 35), width=scale)
        for angle in (30, 65, 110, 150):
            a = math.radians(angle)
            px, py = x+radius*.87*math.cos(a), y+ry*.87*math.sin(a)
            draw.line(points([(px, py), (px, py+2)]), fill=(162, 103, 27), width=scale)

    centers = [(x+rng.uniform(-9, 9), y+rng.uniform(-9, 9))
               for y in range(-10, height+24, 23) for x in range(-10, width+24, 24)]
    rng.shuffle(centers)
    for x, y in centers:
        coin(x, y, rng.uniform(13, 22))

    def gem(x, y, radius, material, angle):
        palette = EPIC_MATERIALS if epic else MATERIALS
        base = palette[material]
        light, dark = palette[material+"_light"], palette[material+"_dark"]
        ca, sa = math.cos(angle), math.sin(angle)

        def transform(u, v):
            return (x+radius*(u*ca-v*sa), y+radius*(u*sa+v*ca))

        outer = [transform(u, v) for u, v in
                 ((-.45, -1), (.45, -1), (.85, -.3), (.5, .85), (-.5, .85), (-.85, -.3))]
        inner = [transform(u, v) for u, v in
                 ((-.22, -.5), (.22, -.5), (.4, -.12), (.24, .38), (-.24, .38), (-.4, -.12))]
        shadow = Image.new("RGBA", image.size)
        ImageDraw.Draw(shadow).polygon(points([(u+3, v+5) for u, v in outer]),
                                      fill=(38, 19, 17, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(2*scale))
        image.paste(shadow, (0, 0), shadow)
        draw.polygon(points(outer), fill=dark)
        shades = [light, base, dark, shade(dark, 12), base, shade(light, -12)]
        for i in range(6):
            j = (i+1) % 6
            draw.polygon(points([outer[i], outer[j], inner[j], inner[i]]), fill=shades[i])
        draw.polygon(points(inner), fill=base)
        draw.line(points([outer[5], outer[0], outer[1]]), fill=shade(light, 28), width=scale)
        draw.line(points([inner[5], inner[0], inner[1], inner[2]]), fill=light, width=scale)

    for x, y, r, color, angle in ((93, 88, 27, "teal", -.38),
                                  (277, 67, 23, "violet", .5),
                                  (420, 116, 28, "teal", .34),
                                  (188, 219, 31, "violet", -.4),
                                  (350, 235, 24, "teal", -.65),
                                  (59, 260, 20, "violet", .25)):
        gem(x, y, r, color, angle)

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    # Darkened edges sit naturally beneath the rim rather than looking like a decal.
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            distance = min(x, width-1-x, y, height-1-y)
            factor = .72 + .28*min(distance/18, 1)
            pixels[x, y] = tuple(round(v*factor) for v in pixels[x, y])
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(v):
    length = math.sqrt(dot(v, v))
    return [x / length for x in v]


class Model:
    def __init__(self):
        self.elements = []
        self.groups = {}

    def add(self, group, element):
        element.update(uuid=uid(element["name"]), export=True, visibility=True,
                       locked=False, color=0)
        self.elements.append(element)
        self.groups.setdefault(group, []).append(element["uuid"])

    def cube(self, group, name, lo, hi, material, faces=None):
        self.add(group, {
            "type": "cube", "name": name, "from": lo, "to": hi,
            "origin": [0, 0, 0], "rotation": [0, 0, 0],
            "box_uv": False, "autouv": 0, "rescale": False,
            "faces": {face: {"uv": uv_bounds((faces or {}).get(face, material)), "texture": 0}
                      for face in ("north", "east", "south", "west", "up", "down")},
        })

    def solid(self, group, name, vertices, polygons, material, face_materials=None):
        # All generated solids are convex; orient each face away from its center.
        center = [sum(v[i] for v in vertices) / len(vertices) for i in range(3)]
        faces = {}
        for index, polygon in enumerate(polygons):
            poly = list(polygon)
            normal = cross(sub(vertices[poly[1]], vertices[poly[0]]),
                           sub(vertices[poly[2]], vertices[poly[0]]))
            if dot(normal, sub(vertices[poly[0]], center)) < 0:
                poly.reverse()
            axis = max(range(3), key=lambda i: abs(normal[i]))
            axes = {0: (2, 1), 1: (0, 2), 2: (0, 1)}[axis]
            mat = (face_materials or {}).get(index, material)
            u0, v0, u1, v1 = uv_bounds(mat)
            bounds = [(min(v[a] for v in vertices), max(v[a] for v in vertices)) for a in axes]
            uv = {}
            for vi in poly:
                u, v = [(vertices[vi][a] - low) / max(high - low, .00001)
                        for a, (low, high) in zip(axes, bounds)]
                uv[f"v{vi}"] = [round(u0 + u*(u1-u0), 4), round(v1 - v*(v1-v0), 4)]
            faces[f"f{index}"] = {"vertices": [f"v{i}" for i in poly], "uv": uv, "texture": 0}
        self.add(group, {
            "type": "mesh", "name": name, "origin": [0, 0, 0], "rotation": [0, 0, 0],
            "vertices": {f"v{i}": [round(x, 5) for x in v] for i, v in enumerate(vertices)},
            "faces": faces,
        })

    def prism(self, group, name, polygon, low, high, axis, material, edge=None):
        def xyz(p, depth):
            return {0: [depth, p[0], p[1]], 1: [p[0], depth, p[1]],
                    2: [p[0], p[1], depth]}[axis]
        n = len(polygon)
        vertices = [xyz(p, d) for d in (low, high) for p in polygon]
        faces = [[i, (i+1) % n, (i+1) % n+n, i+n] for i in range(n)]
        materials = {i: edge or material for i in range(n)}
        for offset in (0, n):
            for i in range(1, n-1):
                faces.append([offset, offset+i, offset+i+1])
        self.solid(group, name, vertices, faces, material, materials)

    def plate(self, group, name, a, b, low, high, axis, material, bevel=.3):
        x0, y0 = a
        x1, y1 = b
        polygon = [(x0+bevel, y0), (x1-bevel, y0), (x1, y0+bevel),
                   (x1, y1-bevel), (x1-bevel, y1), (x0+bevel, y1),
                   (x0, y1-bevel), (x0, y0+bevel)]
        self.prism(group, name, polygon, low, high, axis, material, "brass_dark")

    def cylinder(self, group, name, center, axis, radius, length, material,
                 cap=None, sides=8):
        direction = unit(axis)
        tangent = unit(cross(direction, [0, 0, 1] if abs(direction[2]) < .9 else [0, 1, 0]))
        bitangent = cross(direction, tangent)
        vertices = []
        for along, r in ((-length/2, radius*.86), (-length/2+.06, radius),
                         (length/2-.06, radius), (length/2, radius*.86)):
            for i in range(sides):
                t = 2*math.pi*i/sides
                vertices.append([center[k] + direction[k]*along +
                                 r*(tangent[k]*math.cos(t) + bitangent[k]*math.sin(t))
                                 for k in range(3)])
        faces, mats = [], {}
        for ring in range(3):
            for i in range(sides):
                mats[len(faces)] = material if ring == 1 else (cap or material)
                faces.append([ring*sides+i, ring*sides+(i+1)%sides,
                              (ring+1)*sides+(i+1)%sides, (ring+1)*sides+i])
        for offset in (0, 3*sides):
            for i in range(1, sides-1):
                mats[len(faces)] = cap or material
                faces.append([offset, offset+i, offset+i+1])
        self.solid(group, name, vertices, faces, material, mats)

    def rivet(self, group, name, center, normal, radius=.24):
        self.cylinder(group, name, center, normal, radius, .19, "brass_dark", "brass_light")

    def arc(self, name, x0, x1, a0, a1, outer, inner, material, edge=None):
        def yz(a, offset):
            return [12 + (5.6+offset)*math.sin(a), (8.5+offset)*math.cos(a)]
        section = [yz(a0, outer), yz(a1, outer), yz(a1, inner), yz(a0, inner)]
        vertices = [[x, y, z] for x in (x0, x1) for y, z in section]
        faces = [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6],
                 [3, 0, 4, 7], [0, 3, 2, 1], [4, 5, 6, 7]]
        self.solid("lid", name, vertices, faces, material,
                   {i: edge or material for i in (1, 2, 3, 4, 5)})

    def export(self, opened, texture, epic=False):
        outliner = []
        for name, children in self.groups.items():
            outliner.append({
                "name": name, "uuid": uid("group/"+name), "children": children,
                "origin": HINGE if name == "lid" else [0, 0, 0],
                "rotation": [-105, 0, 0] if name == "lid" and opened else [0, 0, 0],
                "export": True, "visibility": True, "isOpen": False,
            })
        return {
            "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": ("Epic_chest" if epic else "Regular_chest") + ("_open" if opened else ""),
            "resolution": {"width": SIZE, "height": SIZE},
            "elements": self.elements, "outliner": outliner,
            "textures": [{
                "name": "epic_chest_atlas.png" if epic else "chest_atlas.png",
                "id": "0", "uuid": uid("epic_atlas" if epic else "atlas"),
                "width": SIZE, "height": SIZE, "uv_width": SIZE, "uv_height": SIZE,
                "render_mode": "default", "render_sides": "front",
                "internal": True, "saved": True, "visible": True,
                "source": "data:image/png;base64," + base64.b64encode(texture).decode(),
            }, {
                "name": ("Epic_chest" if epic else "Regular_chest") + "_loot.png",
                "id": "1", "uuid": uid("epic_loot" if epic else "regular_loot"),
                "width": 512, "height": 320, "uv_width": SIZE, "uv_height": SIZE,
                "render_mode": "default", "render_sides": "front",
                "internal": True, "saved": True, "visible": True,
                "source": "data:image/png;base64," + base64.b64encode(loot_texture(epic)).decode(),
            }],
        }


def build():
    m = Model()
    woods = ["oak_warm", "oak_honey", "oak_light", "oak_amber"]
    # Separate walls and a real floor leave the interior hollow in both poses.
    for i in range(4):
        y0, y1 = 1.65+i*2.52, 1.65+(i+1)*2.52-.065
        for side, z0, z1 in (("front", 7.45, 8.45), ("back", -8.45, -7.45)):
            m.cube("woodwork", f"{side}_oak_plank_{i+1}", [-12.8, y0, z0], [12.8, y1, z1],
                   woods[i], {"up": "wood_edge", "down": "wood_edge",
                              "north" if side == "front" else "south": "inside"})
        for side, x0, x1 in (("left", -12.8, -11.8), ("right", 11.8, 12.8)):
            m.cube("woodwork", f"{side}_oak_plank_{i+1}", [x0, y0, -7.45], [x1, y1, 7.45],
                   woods[(i+1)%4], {"up": "wood_edge", "down": "wood_edge",
                                   "east" if side == "left" else "west": "inside"})
        m.cube("woodwork", f"floor_board_{i+1}", [-11.8+i*5.9, 1.45, -7.45],
               [-11.8+(i+1)*5.9-.04, 2.25, 7.45], "inside")

    for label, y0, y1, mat in (("lower_frame", 1.1, 2.1, "brass_dark"),
                               ("lower_lip", 2.1, 2.45, "brass_light"),
                               ("mouth_frame", 11.2, 11.85, "brass"),
                               ("mouth_bead", 11.85, 12, "brass_light")):
        for side, z0, z1 in (("front", 7.3, 8.73), ("back", -8.73, -7.3)):
            m.cube("frame", f"{label}_{side}", [-13.15, y0, z0], [13.15, y1, z1], mat)
        for side, x0, x1 in (("left", -13.15, -11.7), ("right", 11.7, 13.15)):
            m.cube("frame", f"{label}_{side}", [x0, y0, -7.3], [x1, y1, 7.3], mat)

    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx*11.4, sz*6.9
            m.plate("frame", f"foot_{sx}_{sz}", [x-1.6, z-1.45], [x+1.6, z+1.45],
                    .1, 1.25, 1, "iron", .5)
            m.plate("frame", f"foot_cap_{sx}_{sz}", [x-1.7, z-1.55], [x+1.7, z+1.55],
                    1.05, 1.6, 1, "brass", .45)
            z0, z1 = sorted((sz*8.46, sz*8.8))
            x0, x1 = sorted((sx*11.7, sx*13.15))
            m.plate("frame", f"corner_face_{sx}_{sz}", [x0, 2.4], [x1, 11.15],
                    z0, z1, 2, "brass", .28)
            x0, x1 = sorted((sx*12.82, sx*13.17))
            z0, z1 = sorted((sz*7.1, sz*8.8))
            m.cube("frame", f"corner_return_{sx}_{sz}", [x0, 2.4, z0], [x1, 11.15, z1], "brass")
            for y in (3.05, 10.4):
                m.rivet("hardware", f"corner_bolt_{sx}_{sz}_{y}", [sx*12.42, y, sz*8.86], [0, 0, sz])

    for x in (-8.5, 8.5):
        for sz in (-1, 1):
            z0, z1 = sorted((sz*8.48, sz*8.88))
            m.cube("frame", f"body_band_{x}_{sz}", [x-.86, 2.45, z0], [x+.86, 11.2, z1],
                   "brass", {"east": "brass_light", "west": "brass_dark"})
            z0, z1 = sorted((sz*8.89, sz*8.97))
            for dx in (-.68, .68):
                m.cube("hardware", f"band_bead_{x}_{sz}_{dx}", [x+dx-.045, 2.7, z0],
                       [x+dx+.045, 10.98, z1], "brass_edge")
            for y in (3.15, 6.65, 10.5):
                m.rivet("hardware", f"strap_rivet_{x}_{sz}_{y}", [x, y, sz*9.02], [0, 0, sz], .27)

    # A pair of chunky drop handles, with separate brackets and pivot pins.
    for sx in (-1, 1):
        for z in (-2.15, 2.15):
            lo, hi = sorted((sx*12.85, sx*13.28))
            m.plate("handles", f"handle_mount_{sx}_{z}", [6.8, z-.9], [9.25, z+.9],
                    lo, hi, 0, "iron", .35)
            m.rivet("handles", f"handle_mount_bolt_{sx}_{z}", [sx*13.4, 8.8, z], [sx, 0, 0], .25)
            m.cylinder("handles", f"handle_pivot_{sx}_{z}", [sx*13.55, 7.6, z],
                       [1, 0, 0], .5, .65, "brass_dark", "brass_light")
        path = [(7.6, -2.15), (6.0, -2.4), (5.4, -1.7), (5.4, 1.7), (6, 2.4), (7.6, 2.15)]
        for i, (a, b) in enumerate(zip(path, path[1:])):
            p, q = [sx*13.85, *a], [sx*13.85, *b]
            vector = sub(q, p)
            m.cylinder("handles", f"handle_grip_{sx}_{i}",
                       [(v+w)/2 for v, w in zip(p, q)], vector, .34,
                       math.sqrt(dot(vector, vector))+.12, "brass", "brass_light")

    m.plate("lock", "lock_iron_backing", [-2.5, 4.9], [2.5, 10.3], 8.48, 8.83, 2, "iron", .65)
    m.plate("lock", "lock_brass_shield", [-2.18, 5.2], [2.18, 10.05], 8.83, 9.16, 2, "brass", .6)
    m.plate("lock", "lock_recess", [-1.4, 5.85], [1.4, 8.6], 9.17, 9.24, 2, "brass_dark", .35)
    m.plate("lock", "lock_raised_face", [-1.13, 6.08], [1.13, 8.38], 9.25, 9.5, 2, "brass_light", .3)
    m.cylinder("lock", "keyhole_round", [0, 7.62, 9.54], [0, 0, 1], .39, .14, "keyhole")
    m.prism("lock", "keyhole_taper", [(-.16, 7.45), (.16, 7.45), (.33, 6.66), (-.33, 6.66)],
            9.52, 9.63, 2, "keyhole")
    for x in (-1.68, 1.68):
        for y in (5.82, 9.4):
            m.rivet("lock", f"lock_pin_{x}_{y}", [x, y, 9.23], [0, 0, 1], .16)

    for x in (-8.5, 8.5):
        m.plate("hardware", f"hinge_lower_leaf_{x}", [x-1.05, 9.4], [x+1.05, 11.9],
                -8.98, -8.51, 2, "brass", .23)
        m.cylinder("hardware", f"hinge_barrel_{x}", [x, 12, -8.6], [1, 0, 0],
                   .46, 2.6, "brass_dark", "brass_light")

    for i in range(12):
        a, b = math.pi*i/12, math.pi*(i+1)/12
        m.arc(f"lid_oak_stave_{i+1}", -12.85, 12.85, a+.003, b-.003, 0, -.68,
              woods[i%4], "wood_edge")
        # The inner curved lining is separate from the exterior planks.
        m.arc(f"lid_inner_stave_{i+1}", -11.9, 11.9, a+.004, b-.004, -.685, -.72, "inside")
        for x in (-8.5, 8.5):
            m.arc(f"lid_band_{x}_{i}", x-.87, x+.87, a, b, .34, .06, "brass")
            for dx in (-.72, .72):
                m.arc(f"lid_band_bead_{x}_{i}_{dx}", x+dx-.055, x+dx+.055, a, b,
                      .39, .345, "brass_edge")
            if i % 2 == 0:
                t = (a+b)/2
                normal = unit([0, math.sin(t)/5.6, math.cos(t)/8.5])
                m.rivet("lid", f"lid_rivet_{x}_{i}",
                        [x, 12+5.99*math.sin(t), 8.89*math.cos(t)], normal, .26)
        for sx in (-1, 1):
            lo, hi = sorted((sx*12.4, sx*13.13))
            m.arc(f"lid_end_rim_{sx}_{i}", lo, hi, a, b, .2, -.22, "brass_light")

    for sx in (-1, 1):
        cap = [(12, 8.1)] + [(12+5.25*math.sin(math.pi*i/12), 8.1*math.cos(math.pi*i/12))
                             for i in range(1, 13)]
        lo, hi = sorted((sx*12.06, sx*12.65))
        m.prism("lid", f"lid_end_panel_{sx}", cap, lo, hi, 0, "oak_end", "wood_edge")
        for y in (13.55, 15.1):
            half = 8.1*math.sqrt(1-((y-12)/5.25)**2)
            lo, hi = sorted((sx*12.66, sx*12.68))
            m.cube("lid", f"lid_end_seam_{sx}_{y}", [lo, y, -half], [hi, y+.055, half], "wood_edge")
        lo, hi = sorted((sx*12.69, sx*12.83))
        m.plate("lid", f"lid_end_badge_{sx}", [12.4, -1.5], [15.85, 1.5],
                lo, hi, 0, "brass_dark", .65)
        m.rivet("lid", f"lid_end_badge_boss_{sx}", [sx*12.95, 14.15, 0], [sx, 0, 0], .55)
    for sz in (-1, 1):
        z0, z1 = sorted((sz*8.12, sz*8.72))
        m.cube("lid", f"lid_lower_rail_{sz}", [-13.08, 12.01, z0], [13.08, 12.45, z1], "brass_dark",
               {"up": "brass_light"})
    m.plate("lid", "clasp_hinge_leaf", [-.88, 10.1], [.88, 13.5], 8.83, 9.2, 2, "brass", .25)
    m.plate("lid", "clasp_inlay", [-.49, 10.5], [.49, 12.9], 9.21, 9.3, 2, "brass_light", .15)
    m.rivet("lid", "clasp_hinge_pin", [0, 12.65, 9.38], [0, 0, 1], .23)

    m.cube("treasure", "velvet_lining", [-11.6, 2.26, -7.2], [11.6, 2.43, 7.2], "lining")
    m.cube("treasure", "treasure_fill", [-11.78, 2.43, -7.43], [11.78, 11.15, 7.43], "coin_edge")
    m.elements[-1]["faces"]["up"] = {"uv": [0, 0, SIZE, SIZE], "texture": 1}
    return m


def main():
    model = build()
    for epic in (False, True):
        prefix = "Epic_chest" if epic else "Regular_chest"
        texture_name = "epic_chest_atlas.png" if epic else "chest_atlas.png"
        preview_name = "epic_preview.png" if epic else "preview.png"
        loot_name = f"{prefix}_loot.png"
        texture = atlas(epic)
        (ROOT / texture_name).write_bytes(texture)
        (ROOT / loot_name).write_bytes(loot_texture(epic))
        names = []
        for opened in (False, True):
            name = f"{prefix}{'_open' if opened else ''}.bbmodel"
            data = model.export(opened, texture, epic)
            (ROOT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            names.append(name)
        with zipfile.ZipFile(ROOT / f"{prefix}.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name in names + [texture_name, loot_name, preview_name, "README.md"]:
                entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, (ROOT / name).read_bytes())
    print(f"Generated Regular and Epic poses with {len(model.elements)} editable parts each.")


if __name__ == "__main__":
    main()
