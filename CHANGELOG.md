# 変更履歴 / Changelog

EverLight Mod のすべての注目すべき変更点は、このファイルに記録されます。
All notable changes to the **EverLight** mod will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-26

### 🇯🇵 日本語

#### 追加機能
- Minecraft **1.21.4 (26.2)** / **Java 25** 向け EverLight の初回リリース。
- **NeoForge** および **Fabric** のマルチローダー対応。
- デフォルト `G` キー（操作設定で変更可能）による即時 Fullbright（全開暗視）トグル。
- 完全非可視暗視: ポーション粒子エフェクト、画面点滅、右上HUDステータスアイコンを一切表示しません。
- **スライドバー ＋ 数値入力ボックス** が双方向連動する設定 GUI メニュー（調整範囲: `1.0` 〜 `10.0`）。
- 控えめな明暗補正（`1.0`）から全開暗視（`10.0`）までの動的照度リアルタイムスケーリング。
- ローダー標準設定メニューとの統合:
  - **NeoForge**: 組み込み Mod リストの「設定 / Config」ボタンから直接起動 (`IConfigScreenFactory`)。
  - **Fabric**: **ModMenu** GUI から直接起動 (`ModMenuApi`)。
- 設定の自動永続化 (`config/mc_ever_light.properties`)。
- 黄金のランタンとクリスタルエンブレムを描いた高解像度 (512x512) Mod アイコンアセット。

---

### 🇬🇧 English

#### Added
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
