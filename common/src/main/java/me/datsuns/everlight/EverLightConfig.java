package me.datsuns.everlight;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Properties;

public class EverLightConfig {
    private static File configFile;

    public static void init(Path configDir) {
        configFile = configDir.resolve("mc_ever_light.properties").toFile();
        load();
    }

    public static void load() {
        if (configFile == null || !configFile.exists()) {
            save();
            return;
        }

        Properties props = new Properties();
        try (FileReader reader = new FileReader(configFile)) {
            props.load(reader);
            boolean enabled = Boolean.parseBoolean(props.getProperty("enabled", "true"));
            double maxGamma = Double.parseDouble(props.getProperty("maxGamma", "10.0"));
            EverLightCommon.setEnabled(enabled);
            EverLightCommon.setMaxGamma(maxGamma);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void save() {
        if (configFile == null) return;
        
        Properties props = new Properties();
        props.setProperty("enabled", String.valueOf(EverLightCommon.isEnabled()));
        props.setProperty("maxGamma", String.valueOf(EverLightCommon.getMaxGamma()));

        try {
            if (configFile.getParentFile() != null && !configFile.getParentFile().exists()) {
                configFile.getParentFile().mkdirs();
            }
            try (FileWriter writer = new FileWriter(configFile)) {
                props.store(writer, "EverLight Mod Configuration");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
