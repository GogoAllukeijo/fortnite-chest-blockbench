import base64, io, json, math, random, uuid
from PIL import Image

PAL = {
    "wood_a": (139, 90, 43), "wood_b": (120, 75, 35), "wood_c": (158, 105, 55),
    "wood_dark": (84, 52, 26), "gold": (255, 200, 40), "gold_hi": (255, 233, 120),
    "gold_dark": (190, 130, 20), "black": (30, 20, 15), "glow": (255, 240, 150),
    "glow2": (255, 190, 60), "gem_blue": (80, 200, 255), "gem_pink": (255, 90, 190),
    "gem_green": (110, 255, 120), "coin": (255, 215, 70), "inside": (60, 36, 18),
}
NAMES = list(PAL)
img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
for i, n in enumerate(NAMES):
    img.putpixel((i % 16, i // 16), PAL[n] + (255,))
buf = io.BytesIO()
img.save(buf, "PNG")
PNG = buf.getvalue()
open("/root/chest/palette.png", "wb").write(PNG)
TEX = "data:image/png;base64," + base64.b64encode(PNG).decode()
TEX_UUID = str(uuid.uuid4())


def uvface(c):
    i = NAMES.index(c)
    x, y = i % 16, i // 16
    return {"uv": [x + .25, y + .25, x + .75, y + .75], "texture": 0}


class Model:
    def __init__(self):
        self.elements = []

    def cube(self, name, frm, to, color, rot=None, origin=None, colors=None):
        u = str(uuid.uuid4())
        faces = {f: uvface((colors or {}).get(f, color))
                 for f in ("north", "east", "south", "west", "up", "down")}
        lo = [min(a, b) for a, b in zip(frm, to)]
        hi = [max(a, b) for a, b in zip(frm, to)]
        e = {"name": name, "box_uv": False, "rescale": False, "locked": False,
             "from": [round(v, 3) for v in lo], "to": [round(v, 3) for v in hi],
             "autouv": 0, "color": 0, "origin": origin or [0, 0, 0],
             "faces": faces, "type": "cube", "uuid": u}
        if rot:
            e["rotation"] = rot
        self.elements.append(e)
        return u


def build(open_lid):
    m = Model()
    body, lid = [], []
    H = 9  # rungon korkeus; etuosa on +Z
    cols = ["wood_a", "wood_c", "wood_b"]
    for i in range(3):
        body.append(m.cube(f"board{i}", [-8, i * 3, -8], [8, (i + 1) * 3, 8], cols[i],
                           colors={"up": "wood_dark"}))
    for i in (1, 2):
        body.append(m.cube(f"seam{i}", [-8.05, i * 3 - .12, -8.05], [8.05, i * 3 + .12, 8.05], "wood_dark"))
    body.append(m.cube("base_trim", [-8.4, 0, -8.4], [8.4, 1.4, 8.4], "gold_dark"))
    body.append(m.cube("base_hi", [-8.45, 1.4, -8.45], [8.45, 1.8, 8.45], "gold"))
    body.append(m.cube("top_rim", [-8.4, H - 1.2, -8.4], [8.4, H, 8.4], "gold"))
    body.append(m.cube("top_rim_hi", [-8.45, H - .4, -8.45], [8.45, H + .05, 8.45], "gold_hi"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            body.append(m.cube("corner", [sx * 7.0, 0, sz * 7.0], [sx * 8.7, H + .1, sz * 8.7], "gold",
                               colors={"up": "gold_hi"}))
            body.append(m.cube("corner_stud", [sx * 6.8, 3.9, sz * 6.8], [sx * 9.0, 5.1, sz * 9.0], "gold_hi"))
    body.append(m.cube("plate", [-2.8, 2.2, 8.4], [2.8, 8.2, 9.0], "gold"))
    body.append(m.cube("plate_hi", [-2.4, 2.6, 9.0], [2.4, 7.8, 9.3], "gold_dark"))
    body.append(m.cube("lock", [-1.8, 3.2, 9.3], [1.8, 6.4, 10.2], "gold_hi"))
    body.append(m.cube("keyhole", [-.5, 4.0, 10.2], [.5, 5.4, 10.4], "black"))
    body.append(m.cube("keyhole2", [-.9, 3.6, 10.2], [.9, 4.3, 10.4], "black"))
    for sx in (-1, 1):
        for y in (2.8, 7.0):
            body.append(m.cube("rivet", [sx * 2.0 - .35, y, 9.3], [sx * 2.0 + .35, y + .7, 9.6], "gold_hi"))

    r, step = 8.0, 12
    w = 2 * r * math.tan(math.radians(step / 2)) + .15
    for k in range(15):
        a = -84 + k * step
        c = "wood_a" if k % 2 == 0 else "wood_c"
        o = [0, H, 0]
        lid.append(m.cube(f"lid_slab{k}", [-8, H, -w / 2], [8, H + r, w / 2], c, rot=[a, 0, 0], origin=o,
                          colors={"east": "wood_dark", "west": "wood_dark", "down": "inside"}))
        for bx in (-6.6, 0.0, 6.6):
            bw = .9 if bx == 0 else 1.6
            lid.append(m.cube(f"lid_band{k}", [bx - bw, H, -w / 2 - .02], [bx + bw, H + r + .45, w / 2 + .02],
                              "gold" if k % 2 == 0 else "gold_dark", rot=[a, 0, 0], origin=o))
        for ex0, ex1 in ((-8.4, -7.9), (7.9, 8.4)):
            lid.append(m.cube(f"lid_edge{k}", [ex0, H, -w / 2 - .03], [ex1, H + r + .2, w / 2 + .03],
                              "gold_hi", rot=[a, 0, 0], origin=o))
    lid.append(m.cube("lid_clasp", [-1.6, H, 8.45], [1.6, H + 2.6, 9.3], "gold"))
    lid.append(m.cube("lid_clasp_hi", [-1.2, H + .4, 9.3], [1.2, H + 2.2, 9.6], "gold_hi"))
    lid.append(m.cube("gem_top", [-1, H + r + .4, -1], [1, H + r + 2.0, 1], "gem_pink",
                      rot=[0, 45, 0], origin=[0, H + r + .4, 0]))
    lid.append(m.cube("gem_top_hi", [-.5, H + r + 2.0, -.5], [.5, H + r + 2.8, .5], "glow",
                      rot=[0, 45, 0], origin=[0, H + r + 2.0, 0]))

    items = []
    if open_lid:
        items.append(m.cube("cavity", [-7, H - .05, -7], [7, H + .02, 7], "inside"))
        items.append(m.cube("glow_layer", [-6.6, H + .02, -6.6], [6.6, H + .5, 6.6], "glow2",
                            colors={"up": "glow"}))
        rnd = random.Random(7)
        for i in range(28):
            x, z = rnd.uniform(-5.8, 5.8), rnd.uniform(-5.8, 5.8)
            h = H + .5 + max(0, 2.2 - math.hypot(x, z) * .35) + rnd.uniform(0, .5)
            s = rnd.uniform(.7, 1.3)
            c = rnd.choice(["coin", "coin", "gold", "gold_hi", "gem_blue", "gem_pink", "gem_green"])
            items.append(m.cube(f"loot{i}", [x - s, h - s, z - s], [x + s, h, z + s], c,
                                rot=[0, rnd.uniform(0, 90), 0], origin=[x, h, z],
                                colors={"up": "glow" if c.startswith("gem") else c}))
        items.append(m.cube("beam", [-3, H + 3, -3], [3, H + 16, 3], "glow"))
        items.append(m.cube("beam_core", [-1.6, H + 3, -1.6], [1.6, H + 20, 1.6], "glow2"))

    def group(name, children, origin=(0, 0, 0), rot=(0, 0, 0)):
        return {"name": name, "origin": list(origin), "rotation": list(rot), "color": 0,
                "uuid": str(uuid.uuid4()), "export": True, "isOpen": False, "locked": False,
                "visibility": True, "autouv": 0, "children": children}

    outliner = [group("body", body),
                group("lid", lid, origin=(0, H, -8), rot=[-110, 0, 0] if open_lid else [0, 0, 0])]
    if items:
        outliner.append(group("loot", items))
    return {
        "meta": {"format_version": "4.10", "creation_time": 1760000000, "model_format": "free", "box_uv": False},
        "name": "fortnite_chest_open" if open_lid else "fortnite_chest",
        "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
        "variable_placeholder_buttons": [], "unhandled_root_fields": {},
        "resolution": {"width": 16, "height": 16},
        "elements": m.elements, "outliner": outliner,
        "textures": [{"path": "", "name": "palette.png", "folder": "", "namespace": "", "id": "0",
                      "width": 16, "height": 16, "uv_width": 16, "uv_height": 16,
                      "particle": False, "use_as_default": False, "layers_enabled": False,
                      "sync_to_project": "", "render_mode": "default", "render_sides": "auto",
                      "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                      "frame_interpolate": False, "visible": True, "internal": True,
                      "saved": True, "uuid": TEX_UUID, "source": TEX}],
    }


for op, fn in ((False, "fortnite_chest_closed.bbmodel"), (True, "fortnite_chest_open.bbmodel")):
    json.dump(build(op), open("/root/chest/" + fn, "w"), indent=1)
print("ok")
