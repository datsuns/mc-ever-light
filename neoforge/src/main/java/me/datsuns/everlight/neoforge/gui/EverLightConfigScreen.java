package me.datsuns.everlight.neoforge.gui;

import me.datsuns.everlight.EverLightCommon;
import me.datsuns.everlight.EverLightConfig;
import me.datsuns.everlight.neoforge.EverLightNeoForge;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.CommonComponents;
import net.minecraft.network.chat.Component;

import java.util.Locale;

public class EverLightConfigScreen extends Screen {
    private final Screen lastScreen;
    private double currentMaxGamma;
    private EditBox numberInput;
    private GammaSlider slider;

    public EverLightConfigScreen(Screen lastScreen) {
        super(Component.literal("EverLight Settings"));
        this.lastScreen = lastScreen;
        this.currentMaxGamma = EverLightCommon.getMaxGamma();
    }

    @Override
    protected void init() {
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        this.slider = new GammaSlider(centerX - 120, centerY - 10, 150, 20, this.currentMaxGamma);
        this.addRenderableWidget(this.slider);

        this.numberInput = new EditBox(this.font, centerX + 40, centerY - 10, 75, 20, Component.literal("Max Gamma"));
        this.numberInput.setValue(String.format(Locale.US, "%.1f", this.currentMaxGamma));
        this.numberInput.setResponder(text -> {
            try {
                double val = Double.parseDouble(text);
                if (val >= 1.0 && val <= 10.0) {
                    this.currentMaxGamma = val;
                    this.slider.setValueDirect((val - 1.0) / 9.0);
                    EverLightCommon.setMaxGamma(this.currentMaxGamma);
                    EverLightNeoForge.applyBrightness(Minecraft.getInstance(), EverLightCommon.isEnabled());
                }
            } catch (NumberFormatException ignored) {
            }
        });
        this.addRenderableWidget(this.numberInput);

        this.addRenderableWidget(Button.builder(CommonComponents.GUI_DONE, button -> {
            EverLightCommon.setMaxGamma(this.currentMaxGamma);
            EverLightConfig.save();
            EverLightNeoForge.applyBrightness(Minecraft.getInstance(), EverLightCommon.isEnabled());
            this.onClose();
        }).bounds(centerX - 100, centerY + 40, 95, 20).build());

        this.addRenderableWidget(Button.builder(CommonComponents.GUI_CANCEL, button -> {
            this.onClose();
        }).bounds(centerX + 5, centerY + 40, 95, 20).build());
    }

    @Override
    public void onClose() {
        super.onClose();
    }

    private class GammaSlider extends AbstractSliderButton {
        public GammaSlider(int x, int y, int width, int height, double value) {
            super(x, y, width, height, Component.empty(), (value - 1.0) / 9.0);
            this.updateMessage();
        }

        public void setValueDirect(double val01) {
            this.value = Math.max(0.0, Math.min(1.0, val01));
            this.updateMessage();
        }

        @Override
        protected void updateMessage() {
            double actualValue = 1.0 + this.value * 9.0;
            this.setMessage(Component.literal(String.format(Locale.US, "Slider: %.1f", actualValue)));
        }

        @Override
        protected void applyValue() {
            double actualValue = 1.0 + this.value * 9.0;
            currentMaxGamma = Math.round(actualValue * 10.0) / 10.0;
            if (numberInput != null) {
                String str = String.format(Locale.US, "%.1f", currentMaxGamma);
                if (!numberInput.getValue().equals(str)) {
                    numberInput.setValue(str);
                }
            }
            EverLightCommon.setMaxGamma(currentMaxGamma);
            EverLightNeoForge.applyBrightness(Minecraft.getInstance(), EverLightCommon.isEnabled());
        }
    }
}
