# Changelog

All notable changes to the **EverLight** mod will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-26

### Added
- Initial release of EverLight for Minecraft **1.21.4 (26.2)** running on **Java 25**.
- Multi-loader support for both **NeoForge** and **Fabric**.
- Instant Fullbright / Night Vision toggle mapped to default key `G` (customizable in Key Binds).
- Completely clean and invisible Fullbright: No potion particles, no HUD buff status icons, and no screen flashing.
- Interactive Configuration GUI with a bi-directionally synchronized **Slider + Numeric Input Box** (Range: `1.0` - `10.0`).
- Dynamic real-time brightness scaling from subtle illumination (`1.0`) to maximum night vision (`10.0`).
- Seamless Mod Loader integration:
  - **NeoForge**: Option screen accessible directly via built-in Mod List (`IConfigScreenFactory`).
  - **Fabric**: Full **ModMenu** GUI integration (`ModMenuApi`).
- Automatic persistent configuration saved to `config/mc_ever_light.properties`.
- High-resolution (512x512) custom mod icon assets featuring a glowing golden lantern and sunburst crystal.
