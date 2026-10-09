# RC4 exact structure and building map

Verified against installed BCA 4.3.0, Terralith 2.6.2, CobbleTowns 1.1.3 and Legendary Monuments 8.1 archives on 2026-10-09. Archive presence establishes an ID/template candidate; gameplay detection is separately identified in the research report.

All RC4 village rules use priority 30, Overworld and `battle: "never"`. Generic pools have day [0,12000) and night [12000,24000). Pool song lists are in the audio inventory.

| Exact structure ID | Category | Intended music | Condition | Workbook source |
|---|---|---|---|---|
| `bca:village/default_small` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/default_mid` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/default_large` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/fighting_small` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/fighting_mid` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/fighting_large` | basic | `village_basic_day` / `village_basic_night` | `structure` | Villages A/B conditions |
| `bca:village/dark_small` | magic | `village_magic_day` / `village_magic_night` | `structure` | Villages C/D conditions |
| `bca:village/dark_mid` | magic | `village_magic_day` / `village_magic_night` | `structure` | Villages C/D conditions |
| `bca:village/fairy_small` | magic | `village_magic_day` / `village_magic_night` | `structure` | Villages C/D conditions |
| `bca:village/fairy_mid` | magic | `village_magic_day` / `village_magic_night` | `structure` | Villages C/D conditions |
| `bca:village/ice_small` | cold | `village_cold_day` / `village_cold_night` | `structure` | Villages E/F conditions |
| `bca:village/ice_mid` | cold | `village_cold_day` / `village_cold_night` | `structure` | Villages E/F conditions |
| `bca:village/ice_large` | cold | `village_cold_day` / `village_cold_night` | `structure` | Villages E/F conditions |
| `terralith:fortified_village` | basic | `village_basic_day` / `village_basic_night` | `structure` | A9/B9 |
| `terralith:fortified_desert_village` | hot | `village_hot_day` / `village_hot_night` | `structure` | G3/H3 |
| `cobbletowns:pallet_town` | named town | LGPE - Pallet Town | `structure` | I5: LGPE - Pallet Town |
| `cobbletowns:lavender_town` | named town | LGPE - Lavander Town | `structure` | I9: LGPE - Lavander Town |
| `cobbletowns:cherrygrove_city` | named town | HGSS - Cherrygrove City | `structure` | I17: HGSS - Cherrygrove City |
| `cobbletowns:pacifidlog_town` | named town | ORAS - Pacificlog Town | `structure` | I21: ORAS - Pacificlog Town |
| `cobbletowns:twinleaf_town` | named town | BDSP - Twinleaf Town (Day) / (Night), approved | `structure` with time ranges | I25: BDSP - Twinleaf Town; user approved split |
| `cobbletowns:floaroma_town` | named town | BDSP - Floaroma Town | `structure` | I29: BDSP - Floaroma Town |
| `cobbletowns:lentimas_town` | named town | BW - Lentimas Town | `structure` | I33: BW - Lentimas Town |
| `legendarymonuments:traditional_village/ecruteak` | named legendary village | HGSS - Ecruteak City | `structure` | J3/J5 |
| `legendarymonuments:traditional_village/nonlegendary` | unassigned variant | No workbook assignment; keep ambient unless user extends mapping | `structure` if added | None |

## Exact special building candidates

`structure_piece` accepts the template ID, not the template-pool ID. These rows distinguish the workbook-assigned tower from RC5 candidates; RC5 center/mart song selection has not been audited in this RC4 pass. Pallet lab inherits Pallet Town in RC4 because the Villages sheet assigns no laboratory override.

| Exact piece ID | Parent/category | Intended RC4 music / future work | Match |
|---|---|---|---|
| `bca:default/one_off/pokecenter` | BCA village where placed | Inherit category pool; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `bca:default/one_off/structure_pokemart` | BCA village where placed | Inherit category pool; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `legendarymonuments:traditional_village/common/utilities/center` | Traditional village where placed | Inherit parent mapping; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `legendarymonuments:traditional_village/common/utilities/mart` | Traditional village where placed | Inherit parent mapping; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:cherrygrove_city/buildings/center` | cherrygrove_city | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:cherrygrove_city/buildings/mart` | cherrygrove_city | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:floaroma_town/buildings/center` | floaroma_town | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:floaroma_town/buildings/mart` | floaroma_town | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:lavender_town/buildings/center` | lavender_town | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:lavender_town/buildings/mart` | lavender_town | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:lavender_town/buildings/pokemon_tower` | lavender_town | LGPE - Pokemon Tower (I13); deliberate precedence over Lavender Town | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:lentimas_town/buildings/center` | lentimas_town | Inherit town theme; center/mart override deferred to RC5 | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:pallet_town/rare_structures/lab` | pallet_town | LGPE - Pallet Town; no separate lab assignment | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:pokecenter/pokecenter` | pokecenter | No RC4 village assignment; standalone RC5 target | `structure_piece` with exact parent `structure` where applicable |
| `cobbletowns:pokemart/pokemart` | pokemart | No RC4 village assignment; standalone RC5 target | `structure_piece` with exact parent `structure` where applicable |

Town centers/signs and `pokemart_shopkeeper` templates are not Pokémon Center/Mart building IDs. The archive has no town-specific center/mart templates for Pallet, Twinleaf or Pacifidlog, and no town-specific mart template for Lentimas; do not fabricate these IDs. Legendary Monuments `traditional_village/nonlegendary/center` is a settlement center, not automatically a Pokécenter.

Avoid `#bca:villages` (includes witch hut) and `#terralith:fortified_villages` (merges two music categories). `#legendarymonuments:ecruteak` currently contains only the legendary Ecruteak structure, but use the exact ID for this release.
