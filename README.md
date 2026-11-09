# Regular_chest - Blockbench

Original, stylized wooden loot chest inspired by colorful adventure games.
Not an official Fortnite asset and not extracted from any game.

![Closed and open models rendered in Blockbench](preview.png)

## Lataa / Download

[Download both models + textures (ZIP)](https://github.com/GogoAllukeijo/fortnite-chest-blockbench/raw/refs/heads/main/Regular_chest.zip)

- `Regular_chest.bbmodel` - closed chest.
- `Regular_chest_open.bbmodel` - the same chest with its lid opened 105 degrees.
- `chest_atlas.png` - hand-authored procedural 512 x 512 wood, brass and treasure atlas.
- `preview.png` - both actual models rendered in Blockbench.

**Suomeksi:** Pura ZIP ja avaa haluamasi `.bbmodel` Blockbenchissa kohdasta
File > Open Model. Tekstuurit ovat valmiiksi mallin sisalla. Molemmat mallit
ovat muokattavia. Valopilari on poistettu kokonaan.

Open either `.bbmodel` with **File > Open Model** in Blockbench 4.10 or newer.
Textures are embedded: no relinking or plugins are needed.
These are **Generic Model** projects containing cubes and meshes, not direct
Minecraft Java/Bedrock exports. Game-specific conversion requires a suitable
exporter and may require geometry changes.

## Model details

Both files share the same geometry, textures, contents and named editing groups.
Only the `lid` group's rotation differs. Its rear hinge pivot is `[0, 12, -8.6]`;
set its X rotation to `0` to close it or `-105` to open it.

- Wide oak body with individual grain-textured boards, an actual floor and hollow interior.
- Thin, faceted barrel lid with an inner lining, end panels and continuous brass straps.
- Brass edging, corner guards, rivets, a recessed keyhole, hinges and two drop handles.
- Dark velvet lining, stacked stamped coins and small faceted crystals.
- No beam, opaque glow column or oversized ornament on the lid.

The `treasure` group can be hidden or removed for an empty chest.
The textures use painted highlights, not an emissive shader.

## Regenerate

Use Python 3.10+ from any working directory:

```sh
python -m pip install -r requirements.txt
python gen.py
python -m unittest -v test_models.py
```

The generator writes beside itself, uses fixed seeds and stable UUIDs, and
rebuilds the ZIP with both models, the atlas, the saved preview and this README.
The preview is captured separately in Blockbench; the generator does not rerender it.
