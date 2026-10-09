# Architecture

## Runtime stack

Target environment:

- Minecraft 1.21.1 Fabric
- Cobblemon 1.7.3
- CobbleSafari 0.3.4
- Namespace: `dysfam_music`

The project has two cooperating packs.

## Datapack

The active datapack is rooted at the repository root:

- `pack.mcmeta`
- `data/dysfam_music/csmusic/*.json`
- `data/dysfam_music/csmusic/definition/*.json`

### Track definitions

Files directly under `data/dysfam_music/csmusic/` define playable CSMusic tracks.

Ambient tracks generally use:

- `loop`
- optional `tags`

Battle tracks use:

- `intro`
- required `loop`
- optional `tags`

The sound IDs in these definitions point to sound events supplied by the client resource pack.

### Trigger definitions

Files under `data/dysfam_music/csmusic/definition/` contain trigger rules.

Each rule selects exactly one:

- `music`
- or `tag`

Conditions are ANDed together.

Important battle fields supported by CobbleSafari 0.3.4 include:

- `battle`: `never`, `in_battle`, `wild`, `npc`, or `pvp`
- `species`
- `form`

Generic generation music cannot match `generation` directly, so generation support is implemented by generating exact species rules.

Normal ambient rules use `battle: "never"` so ambient music yields cleanly when a battle begins.

RC4 village rules also use `battle: "never"`, exact Overworld structure IDs and priority 30. Generic villages select one of eight day/night pools; named towns select exact tracks. `structure_piece` restricts Lavender Town's Pokémon Tower to its template bounds. Equal priorities use the source-key order in CobbleSafari 0.3.4; the tower and town rules occupy indices 0 and 1 in one file, respectively. RC4 leaves the Pallet lab on its town theme and reserves Pokémon Center/Mart overrides for RC5.

## Resource pack

The cumulative resource pack is built locally from:

- the external finalized OGG archive
- `manifest/csmusic_release_assets.csv`
- `resourcepack_template/pack.mcmeta`

The builder creates:

- the required OGG files under `assets/dysfam_music/sounds/...`
- `assets/dysfam_music/sounds.json`
- the final ZIP in `build_output/`

`sounds.json` is regenerated from the manifest as UTF-8 without BOM. Do not hand-maintain the template copy as the runtime authority.

## Manifests

### `ambient_rc_assets.csv`

Historical RC1 ambient-only asset manifest. Keep it intact as a rollback/reference snapshot.

### `csmusic_release_assets.csv`

Cumulative release manifest beginning with RC2. It includes all RC1 ambient assets plus new feature assets.

Additional columns:

- `Segment_Role`: `full_loop`, `intro`, `loop`, or later `outro`
- `Feature_Layer`
- `Release_Added`

### `battle_generation_tracks.csv`

Maps generations 1-9 to their generic wild battle CSMusic track.

## Species reference

`docs/reference/cobblemon_species_1.7.3.csv` is generated directly from:

`Cobblemon-fabric-1.7.3+1.21.1.jar`

It records:

- generation
- National PokÃƒÂ©dex number
- display name
- exact `cobblemon:<species>` ID
- source species JSON path

This is the authoritative input for the RC2 full Gen 1-9 rule generator.

## Duplicate datapack workspace

The repository root is the active datapack. The historical package also contains a `datapack/` mirror. For now, patch scripts keep the two copies synchronized so older build/test workflows do not break. Future cleanup may remove the duplicate once the cumulative workflow is stable.

## Generated files

`DysFam_CSMusic_Ambient_RC1_Package/build_output/` is intentionally ignored by Git because it contains large generated resource-pack files. It should always be reproducible from the manifest + source OGG archive.

## RC2 full battle generation

RC2 generates attle_default_gen1.json through attle_default_gen9.json, totaling 1,016 base-species rules at priority 50. Rules match exact cobblemon:<species> IDs.

Forms inherit their base species' generic generation theme because the generic rules do not specify orm. Later special species/form rules can override them at higher priority.

Minecraft 1.21.1 uses data/<namespace>/function/ and data/minecraft/tags/function/ (singular).

## Status functions

- /function dysfam_music:check reports declared/expected pack counts.
- /function dysfam_music:check_audio manually tests one RC2 resource-pack sound event.
- A load/tick session marker displays the online message once per world/server load or /reload.

A vanilla datapack cannot directly inspect the client's enabled resource-pack list or dynamically read CobbleSafari's internal CSMusic loaded-count registry, so those values are reported as expected build counts.
