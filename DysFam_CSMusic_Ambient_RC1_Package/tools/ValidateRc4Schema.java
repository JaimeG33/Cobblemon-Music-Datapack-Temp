import com.google.gson.Gson;
import java.nio.file.Files;
import java.nio.file.Path;
import maxigregrze.cobblesafari.csmusic.CsMusicPiecePattern;
import maxigregrze.cobblesafari.csmusic.CsMusicTimeRange;
import maxigregrze.cobblesafari.csmusic.CsMusicTriggerFileData;

/** Read-only check using the installed CobbleSafari DTO and time/piece classes. */
public class ValidateRc4Schema {
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        Gson gson = new Gson();
        int files = 0, rules = 0, boundaries = 0;
        try (var paths = Files.list(Path.of(args[0]))) {
            for (Path path : paths.filter(p -> p.toString().endsWith(".json")).toList()) {
                var data = gson.fromJson(Files.readString(path), CsMusicTriggerFileData.class);
                require(data.rules != null && !data.rules.isEmpty(), path.toString());
                files++;
                rules += data.rules.size();
                for (var rule : data.rules) {
                    require((rule.music != null) != (rule.tag != null), "music/tag must select exactly one");
                    if (!path.getFileName().toString().startsWith("villages_")) continue;
                    require(rule.priority == 30, "village priority");
                    require("never".equals(rule.when.battle), "village battle exclusion");
                    require("minecraft:overworld".equals(rule.when.dimension), "village dimension");
                    require(rule.when.structure != null, "exact structure string");
                    if (rule.when.time_range != null) {
                        var range = CsMusicTimeRange.fromJson(rule.when.time_range);
                        require(range != null, "invalid time range");
                        boolean day = range.start() == 0;
                        long[] ticks = {0, 11999, 12000, 23999};
                        boolean[] expected = {day, day, !day, !day};
                        for (int i = 0; i < ticks.length; i++) {
                            require(range.matches(ticks[i]) == expected[i], "boundary " + ticks[i]);
                            boundaries++;
                        }
                    }
                    if (rule.when.structure_piece != null) {
                        var piece = CsMusicPiecePattern.fromJson(rule.when.structure_piece);
                        require(piece.matches("cobbletowns:lavender_town/buildings/pokemon_tower"), "tower exact piece");
                        require(!piece.matches("cobbletowns:lavender_town/buildings/center"), "tower must exclude center");
                    }
                }
            }
        }
        require(files == 16 && rules == 1306 && boundaries == 128, "computed schema totals");
        System.out.println("PASS: installed Gson/CobbleSafari DTO: " + files + " files, " + rules + " rules; " + boundaries + " real time-boundary checks; tower piece include/exclude.");
    }
}
