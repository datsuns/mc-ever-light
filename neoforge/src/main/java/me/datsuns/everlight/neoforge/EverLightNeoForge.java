package me.datsuns.everlight.neoforge;

import me.datsuns.everlight.EverLightCommon;
import me.datsuns.everlight.EverLightConfig;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.common.NeoForge;
import org.lwjgl.glfw.GLFW;

@Mod(value = EverLightCommon.MOD_ID, dist = Dist.CLIENT)
public class EverLightNeoForge {
    public static KeyMapping toggleKey;

    public EverLightNeoForge(IEventBus modEventBus, ModContainer modContainer) {
        EverLightConfig.init(FMLPaths.CONFIGDIR.get());
        modEventBus.addListener(this::onClientSetup);
        modEventBus.addListener(this::onRegisterKeyMappings);
        NeoForge.EVENT_BUS.register(this);
    }

    private void onClientSetup(FMLClientSetupEvent event) {
    }

    private void onRegisterKeyMappings(RegisterKeyMappingsEvent event) {
        toggleKey = new KeyMapping(
                "key.mc_ever_light.toggle",
                GLFW.GLFW_KEY_G,
                KeyMapping.Category.MISC
        );
        event.register(toggleKey);
    }

    @SubscribeEvent
    public void onClientTick(ClientTickEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;

        if (toggleKey != null && toggleKey.consumeClick()) {
            boolean state = EverLightCommon.toggle();
            EverLightConfig.save();

            if (state) {
                mc.player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, MobEffectInstance.INFINITE_DURATION, 0, false, false, false));
            } else {
                mc.player.removeEffect(MobEffects.NIGHT_VISION);
            }

            String message = state ? "§a[EverLight] ON" : "§c[EverLight] OFF";
            mc.player.sendSystemMessage(Component.literal(message));
        } else if (EverLightCommon.isEnabled() && !mc.player.hasEffect(MobEffects.NIGHT_VISION)) {
            mc.player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, MobEffectInstance.INFINITE_DURATION, 0, false, false, false));
        }
    }
}
