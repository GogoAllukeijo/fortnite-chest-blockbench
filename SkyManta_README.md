# SkyManta / Aerial Courier 07

An original stylized flying cargo vehicle for Blockbench: a wide manta-shaped
airframe, four ducted lift fans, panoramic cockpit, roof cargo hatch, twin tail
fins and landing skids. Warm ivory panels, burnt-orange trim and copper hardware.

No bus, balloon, Fortnite branding or extracted game assets. This is an original
design, not an official Fortnite vehicle or a reproduction of the Battle Bus.

## Avaa / Open

Pura ZIP ja avaa `SkyManta.bbmodel` Blockbenchissa: **File > Open Model**.
Tekstuurit ja merkinnat ovat valmiiksi mallin sisalla.
**Animate > rotors_spin > Play** pyorittaa neljaa nostoturbiinia.

Open `SkyManta.bbmodel` in Blockbench 4.10 or newer. This is a **Generic Model**
with editable meshes, cubes, named groups and two embedded PNG textures.
The cockpit uses opaque painted reflective glass, not a transparent interior.
The headlights and exhaust use painted bright colors, not an emissive shader.

`rotors_spin` is a one-second linear looping animation; diagonal rotor pairs turn
in opposite directions. Each rotor group's pivot is at its hub. The static duct
housings do not rotate. The model faces +Z, with Y pointing up.

This is a visual asset, not a playable vehicle: flight controls, collision and
physics must be implemented in your game engine. It is not a direct Minecraft
Java/Bedrock model; game-specific export may require conversion.

## Included

- `SkyManta.bbmodel`: editable vehicle and rotor animation.
- `SkyManta_atlas.png`: 512 x 512 painted material atlas.
- `SkyManta_markings.png`: 512 x 512 original emblem, identification and markings.
- `SkyManta_preview.png`: actual Blockbench renders.

## Regenerate in the repository

Uses the shared mesh primitives in `gen.py`, without modifying any chest assets.

```sh
python -m pip install -r requirements.txt
python vehicle_gen.py
python -m unittest -v test_vehicle.py
```

The generator is deterministic and writes beside itself. Capture the preview
separately in Blockbench after visual changes, then regenerate the archive.
