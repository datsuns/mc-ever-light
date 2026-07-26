package me.datsuns.everlight.fabric.mixin;

import me.datsuns.everlight.EverLightCommon;
import me.datsuns.everlight.EverLightConfig;
import me.datsuns.everlight.fabric.EverLightFabricClient;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffects;
import org.lwjgl.glfw.GLFW;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Minecraft.class)
public class MinecraftMixin {
    private boolean lastKeyPressed = false;

    @Inject(method = "tick", at = @At("HEAD"))
    private void onTick(CallbackInfo ci) {
        Minecraft mc = (Minecraft) (Object) this;
        if (mc.player == null) return;

        boolean isPressed = InputConstants.isKeyDown(mc.getWindow(), GLFW.GLFW_KEY_G);

        if (isPressed && !lastKeyPressed) {
            boolean state = EverLightCommon.toggle();
            EverLightConfig.save();
            EverLightFabricClient.applyBrightness(mc, state);

            String message = state ? "§a[EverLight] ON" : "§c[EverLight] OFF";
            mc.player.sendSystemMessage(Component.literal(message));
        }
        lastKeyPressed = isPressed;

        if (EverLightCommon.isEnabled()) {
            EverLightFabricClient.applyBrightness(mc, true);
        } else if (!EverLightCommon.isEnabled() && mc.player.hasEffect(MobEffects.NIGHT_VISION)) {
            mc.player.removeEffect(MobEffects.NIGHT_VISION);
        }
    }
}
