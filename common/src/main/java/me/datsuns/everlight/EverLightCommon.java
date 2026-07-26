package me.datsuns.everlight;

public class EverLightCommon {
    public static final String MOD_ID = "mc_ever_light";
    public static final String MOD_NAME = "EverLight";

    private static boolean enabled = true;
    private static double maxGamma = 10.0; // 1000% brightness

    public static boolean isEnabled() {
        return enabled;
    }

    public static void setEnabled(boolean value) {
        enabled = value;
    }

    public static boolean toggle() {
        enabled = !enabled;
        return enabled;
    }

    public static double getMaxGamma() {
        return maxGamma;
    }

    public static void setMaxGamma(double value) {
        maxGamma = Math.max(1.0, Math.min(100.0, value));
    }
}
