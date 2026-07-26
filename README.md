# EverLight

[![Minecraft](https://img.shields.io/badge/Minecraft-1.21.4%20(26.2)-brightgreen.svg)](https://minecraft.net/)
[![Java](https://img.shields.io/badge/Java-25-orange.svg)](https://openjdk.org/)
[![NeoForge](https://img.shields.io/badge/NeoForge-26.2-blue.svg)](https://neoforged.net/)
[![Fabric](https://img.shields.io/badge/Fabric-1.21.4-purple.svg)](https://fabricmc.net/)
[![Language](https://img.shields.io/badge/Language-English%20%7C%20%E6%97%A5%E6%9C%AC%E8%AA%9E-informational.svg)](README.ja.md)

**EverLight** is a clean, lightweight, and customizable Fullbright / Night Vision mod for Minecraft **1.21.4 (26.2)**, supporting both **NeoForge** and **Fabric** mod loaders.

[日本語ドキュメントはこちら (README.ja.md)](README.ja.md)

---

## ✨ Features

- 💡 **Instant Fullbright Toggle**: Toggle full daylight visibility in caves, underwater, and night with a single keypress.
- 🧘 **Clean & Invisible**: No potion particle effects, no HUD buff status icons, and no screen flash clutter.
- 🎚️ **Customizable Brightness Level (1.0 - 10.0)**:
  - Interactive **Slider + Numeric Input Box** configuration GUI.
  - Adjust brightness dynamically from subtle enhancement to full illumination.
- 🔌 **Seamless Mod Loader Integration**:
  - **NeoForge**: Configurable directly from the built-in Mod List option screen.
  - **Fabric**: Fully integrated with **ModMenu** GUI.
- 💾 **Persistent Settings**: Automatically saved to `config/mc_ever_light.properties`.

---

## ⌨️ Controls & Usage

| Action | Default Key | Description |
| :--- | :---: | :--- |
| **Toggle Light** | `G` | Toggles EverLight ON or OFF with an in-game HUD message. |
| **Config Screen** | Mod Menu / Mods List | Opens the interactive brightness slider settings screen. |

---

## ⚙️ Configuration GUI

EverLight features a bi-directionally synchronized **Slider + Numeric Input Box**:
- Move the slider to update the numeric value in real time.
- Type any precise number between `1.0` and `10.0` to set the slider position automatically.
- Changes are applied live in game and saved upon pressing **Done**.

---

## 🛠️ Building from Source

This project uses a multi-module Gradle structure powered by Java 25.

```bash
# Clone the repository
git clone https://github.com/datsuns/mc-ever-light.git
cd mc-ever-light

# Build all modules (Common, NeoForge, Fabric)
./gradlew build
```

Compiled mod JAR files will be generated in:
- `neoforge/build/libs/mc-ever-light-1.0.0-neoforge-mc1.21.4.jar`
- `fabric/build/libs/mc-ever-light-1.0.0-fabric-mc1.21.4.jar`

---

## 📄 License

This mod is available under the [MIT License](LICENSE). Feel free to include it in your modpacks!
