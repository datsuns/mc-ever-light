package me.datsuns.everlight.fabric;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;
import me.datsuns.everlight.fabric.gui.EverLightConfigScreen;

public class EverLightModMenu implements ModMenuApi {

    @Override
    public ConfigScreenFactory<?> getModConfigScreenFactory() {
        return EverLightConfigScreen::new;
    }
}
