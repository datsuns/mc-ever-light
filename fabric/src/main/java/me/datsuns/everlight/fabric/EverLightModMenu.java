package me.datsuns.everlight.fabric;

import me.datsuns.everlight.fabric.gui.EverLightConfigScreen;
import net.minecraft.client.gui.screens.Screen;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class EverLightModMenu {

    public static Object createModMenuApi() {
        try {
            Class<?> apiClass = Class.forName("com.terraformersmc.modmenu.api.ModMenuApi");
            Class<?> factoryClass = Class.forName("com.terraformersmc.modmenu.api.ConfigScreenFactory");

            InvocationHandler handler = (proxy, method, args) -> {
                if ("getModConfigScreenFactory".equals(method.getName())) {
                    return Proxy.newProxyInstance(
                            factoryClass.getClassLoader(),
                            new Class<?>[]{factoryClass},
                            (fProxy, fMethod, fArgs) -> {
                                if (fArgs != null && fArgs.length >= 1 && fArgs[0] instanceof Screen) {
                                    return new EverLightConfigScreen((Screen) fArgs[0]);
                                }
                                return null;
                            }
                    );
                }
                return null;
            };

            return Proxy.newProxyInstance(apiClass.getClassLoader(), new Class<?>[]{apiClass}, handler);
        } catch (Throwable t) {
            return null;
        }
    }
}
