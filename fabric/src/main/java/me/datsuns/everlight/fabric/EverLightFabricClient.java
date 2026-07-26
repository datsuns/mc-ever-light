package me.datsuns.everlight.fabric;

import me.datsuns.everlight.EverLightConfig;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.loader.api.FabricLoader;

public class EverLightFabricClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        EverLightConfig.init(FabricLoader.getInstance().getConfigDir());
    }
}
