package me.datsuns.everlight;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class EverLightCommonTest {

    @BeforeEach
    public void setUp() {
        EverLightCommon.setEnabled(true);
        EverLightCommon.setMaxGamma(10.0);
    }

    @Test
    public void testToggle() {
        assertTrue(EverLightCommon.isEnabled());
        boolean newState = EverLightCommon.toggle();
        assertFalse(newState);
        assertFalse(EverLightCommon.isEnabled());
    }

    @Test
    public void testMaxGammaClamping() {
        EverLightCommon.setMaxGamma(0.5);
        assertEquals(1.0, EverLightCommon.getMaxGamma(), 0.001);

        EverLightCommon.setMaxGamma(150.0);
        assertEquals(100.0, EverLightCommon.getMaxGamma(), 0.001);

        EverLightCommon.setMaxGamma(5.0);
        assertEquals(5.0, EverLightCommon.getMaxGamma(), 0.001);
    }
}
