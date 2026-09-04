DysFam CSMusic — Ambient Release Candidate 1
================================================

WHAT THIS RC IMPLEMENTS
- Surface biome pools from the latest ToaRex Surface Biomes sheet
- Underground/cave pools from the latest Underground Biomes sheet
- End, Nether, CobbleSafari Safari Zone, and three Legendary Monuments dimensions
- Day/night splits exactly where represented in the final sheet
- Random song pools using native CSMusic definition tags
- Rule priority 10 (the technical equivalent of source Priority 1)

COUNTS
- CSMusic track definitions: 268
- Sound events / locally copied OGGs: 268
- Surface rules: 223
- Underground rules: 14
- Dimension rules: 10
- Total trigger rules: 247

NOT INCLUDED YET
- Weather, villages, Pokecenters/Pokemarts, structures, Pokemon battles
- Raid Den music distinctions (see OPEN ISSUES below)
- EOS - Dark Forest (listed by the final sheet but no matching finalized OGG was found)

BUILD THE RESOURCE PACK
1. Extract this RC package somewhere convenient.
2. Leave the finalized music ZIP at:
   C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip
3. From PowerShell in this package folder, run:
   .\tools\build_ambient_rc_resourcepack.ps1
4. The script validates every source filename, copies the required OGGs, and creates:
   build_output\DysFam_CSMusic_Ambient_RC1_ResourcePack.zip

INSTALL FOR TESTING
1. Put DysFam_CSMusic_Ambient_RC1_Datapack.zip in:
   ...\saves\<TEST WORLD>\datapacks\
2. Put the generated DysFam_CSMusic_Ambient_RC1_ResourcePack.zip in:
   ...\resourcepacks\
3. Enable the resource pack.
4. Keep ReactiveMusic disabled and keep the old Pokemon Music Pack disabled during this test.
5. Use the same full DysFam modpack instance and a throwaway/creative test world.
6. Run:
   /reload
   /cobblesafari csmusic list
   /cobblesafari csmusic current

SUGGESTED TESTS
A. Plains:
   /locate biome minecraft:plains
   /time set day
   /cobblesafari csmusic current
   /time set night
   /cobblesafari csmusic current

B. Desert:
   /locate biome minecraft:desert
   Test day and night.

C. Terralith:
   /locate biome terralith:arid_highlands
   Test day and night.

D. Underground:
   /locate biome minecraft:dripstone_caves
   /locate biome minecraft:deep_dark
   /locate biome terralith:cave/fungal_caves
   Check /cobblesafari csmusic current in each.

E. Nether:
   Check warped_forest, crimson_forest, soul_sand_valley, nether_wastes, and basalt_deltas.
   Each group should select from the matching final-sheet pool.

F. The End:
   Enter minecraft:the_end and verify the End pool.

G. Safari Zone:
   Enter CobbleSafari's Safari Zone and verify dimension_cobblesafari_safari.

IMPORTANT SOURCE-FIDELITY NOTES
- The second spreadsheet header says HILL DAY again, but its tracks are night tracks. RC1 treats it as Hill Night.
- MOUNTAIN DAY is implemented only during daytime because the final sheet has no Mountain Night column.
- SWAMP/MUSHROOM DAY is implemented only during daytime because the final sheet has no night counterpart.
- The final Aquatic Night condition list does not include several cold/frozen-ocean conditions; RC1 does not invent them.
- Equal-priority overlaps (Gravel Beach day and Windswept Spires day/night) are merged into a union random pool.
  This prevents CobbleSafari's deterministic same-priority tie-break from arbitrarily picking one spreadsheet column.

RAID DENS
The final sheet asks for different music for Mega, Tera, Dynamax/Gigantamax, and Legendary Dynamax raids.
Cobblemon Raid Dens uses one dimension (cobblemonraiddens:raid_dimension), and CSMusic 0.3.4 does not expose
those raid mechanics as trigger conditions. RC1 intentionally leaves this portion out instead of pretending
the four cases can be distinguished.

FILES FOR REVIEW
- manifest\ambient_rc_assets.csv
- manifest\ambient_rc_rules.csv
- manifest\ambient_rc_open_issues.csv
