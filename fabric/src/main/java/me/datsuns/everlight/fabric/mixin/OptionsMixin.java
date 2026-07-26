package me.datsuns.everlight.fabric.mixin;

import me.datsuns.everlight.EverLightCommon;
import net.minecraft.client.OptionInstance;
import net.minecraft.client.Options;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Options.class)
public class OptionsMixin {

    @Inject(method = "gamma", at = @At("RETURN"), cancellable = true)
    private void onGamma(CallbackInfoReturnable<OptionInstance<Double>> cir) {
        if (EverLightCommon.isEnabled()) {
            // Options gamma override
        }
    }
}
