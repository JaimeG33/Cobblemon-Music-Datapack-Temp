import com.google.gson.Gson;
import java.nio.file.Files;
import java.nio.file.Path;
import maxigregrze.cobblesafari.csmusic.CsMusicPiecePattern;
import maxigregrze.cobblesafari.csmusic.CsMusicTriggerFileData;

/** Parses cumulative rules using the installed DTO; tests exact tower patterns. */
public class ValidateRc5Schema {
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        Gson gson = new Gson();
        int files = 0, rules = 0, structures = 0, pieces = 0;
        try (var paths = Files.list(Path.of(args[0]))) {
            for (Path path : paths.filter(p -> p.toString().endsWith(".json")).toList()) {
                var data = gson.fromJson(Files.readString(path), CsMusicTriggerFileData.class);
                require(data.rules != null && !data.rules.isEmpty(), path.toString());
                files++;
                rules += data.rules.size();
                for (var rule : data.rules) {
                    require((rule.music != null) != (rule.tag != null), "Exactly one music/tag");
                    if (!path.getFileName().toString().startsWith("structures_")) continue;
                    structures++;
                    require(rule.priority == 41 && "never".equals(rule.when.battle), "Structure priority/battle");
                    require(rule.when.structure != null && rule.when.dimension != null, "Structure/dimension");
                    if (rule.when.structure_piece != null) {
                        pieces++;
                        var piece = CsMusicPiecePattern.fromJson(rule.when.structure_piece);
                        String exact = rule.when.structure_piece;
                        require(piece.matches(exact), "Exact piece match");
                        require(!piece.matches(exact + "_unrelated"), "No prefix match");
                        require(!piece.matches("legendarymonuments:traditional_village/ecruteak/center"), "Exclude village center");
                    }
                }
            }
        }
        require(files == 21 && rules == 1351 && structures == 45 && pieces == 7, "Cumulative schema totals");
        System.out.println("PASS installed DTO: 21 files / 1351 rules / 45 RC5 rules / 7 exact pieces.");
    }
}
