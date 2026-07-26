package me.datsuns.everlight.fabric;

import me.datsuns.everlight.EverLightCommon;
import me.datsuns.everlight.EverLightConfig;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

public class EverLightFabricClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        EverLightConfig.init(FabricLoader.getInstance().getConfigDir());
    }

    public static void applyBrightness(Minecraft mc, boolean enabled) {
        if (mc.player == null) return;

        if (!enabled) {
            if (mc.player.hasEffect(MobEffects.NIGHT_VISION)) {
                mc.player.removeEffect(MobEffects.NIGHT_VISION);
            }
            return;
        }

        double maxGamma = EverLightCommon.getMaxGamma(); // 1.0 ~ 10.0
        double targetGamma = (maxGamma - 1.0) / 9.0;
        mc.options.gamma().set(targetGamma);

        if (maxGamma >= 3.0) {
            if (!mc.player.hasEffect(MobEffects.NIGHT_VISION)) {
                mc.player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, MobEffectInstance.INFINITE_DURATION, 0, false, false, false));
            }
        } else {
            if (mc.player.hasEffect(MobEffects.NIGHT_VISION)) {
                mc.player.removeEffect(MobEffects.NIGHT_VISION);
            }
        }
    }
}
