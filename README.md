# Regular_chest & Epic_chest - Blockbench

Original, stylized wooden loot chest inspired by colorful adventure games.
Not an official Fortnite asset and not extracted from any game.

## Lataa / Download

### Regular_chest

[Download Regular chest + textures (ZIP)](https://github.com/GogoAllukeijo/fortnite-chest-blockbench/raw/refs/heads/main/Regular_chest.zip)

![Regular chest rendered in Blockbench](https://raw.githubusercontent.com/GogoAllukeijo/fortnite-chest-blockbench/main/preview.png)

- `Regular_chest.bbmodel` - closed chest.
- `Regular_chest_open.bbmodel` - the same chest with its lid opened 105 degrees.
- `chest_atlas.png` - hand-authored procedural 512 x 512 wood, brass and treasure atlas.
- `preview.png` - both actual models rendered in Blockbench.

### Epic_chest

[Download Epic chest + textures (ZIP)](https://github.com/GogoAllukeijo/fortnite-chest-blockbench/raw/refs/heads/main/Epic_chest.zip)

![Epic chest rendered in Blockbench](https://raw.githubusercontent.com/GogoAllukeijo/fortnite-chest-blockbench/main/epic_preview.png)

- `Epic_chest.bbmodel` - closed Epic chest.
- `Epic_chest_open.bbmodel` - open Epic chest.
- `epic_chest_atlas.png` - embedded 512 x 512 Epic texture atlas.
- `epic_preview.png` - both Epic poses rendered in Blockbench.

Epic uses rich plum-purple wood, warm champagne-gold hardware, burgundy lining
and amber/ruby treasure. There are no blue surfaces or light beams.
It preserves Regular's geometry, hinge, editing groups and level of detail.
Regular's models and colors are unchanged. Each ZIP contains only its own variant.

**Suomeksi:** Pura ZIP ja avaa haluamasi `.bbmodel` Blockbenchissa kohdasta
File > Open Model. Tekstuurit ovat valmiiksi mallin sisalla. Molemmat mallit
ovat muokattavia. Valopilari on poistettu kokonaan.

Open either `.bbmodel` with **File > Open Model** in Blockbench 4.10 or newer.
Textures are embedded: no relinking or plugins are needed.
These are **Generic Model** projects containing cubes and meshes, not direct
Minecraft Java/Bedrock exports. Game-specific conversion requires a suitable
exporter and may require geometry changes.

## Model details

The closed and open files of each variant share geometry, textures, contents and editing groups.
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
rebuilds each variant's ZIP with its two models, atlas, saved preview and this README.
Previews are captured separately in Blockbench; the generator does not rerender them.
