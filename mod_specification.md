# Mod Specification - EverLight

- **Platform**: Fabric, NeoForge
- **Minecraft Version**: 26.2
- **Mod Name**: EverLight
- **Mod ID**: `mc_ever_light`
- **Package**: `me.datsuns.everlight`

---

## 1. 概要 (Overview)
`EverLight` は、Minecraft内の時間帯（昼夜）や周囲の明るさ（洞窟・水中・ネザー等）に関わらず、画面全体をプレイヤーの見やすい一定以上の明るさに保つ（Fullbright / Lightmap Override）クライアントサイド専用Modです。

---

## 2. 主な機能仕様 (Features)

### 2.1 ライトマップ / ガンマオーバーライド (Fullbright Engine)
- クライアントの描画処理（Lightmap / Gamma）を調整・オーバーライドし、周囲の明暗に関わらず画面を明るく表示します。
- クライアントサイド専用機能のため、マルチプレイのサーバー側に本Modを導入する必要はありません。

### 2.2 トグル機能 & 操作 (Toggle & Keybind)
- **トグルキー**: ゲーム内のキー設定から変更可能な専用ショートカットキー（デフォルト: `G` キー）を押すことで、EverLight の ON / OFF を瞬時に切り替えられます。
- **画面通知 (ActionBar Notice)**: 切り替え時に画面下部（アクションバー）へ `[EverLight] ON` / `[EverLight] OFF` の状態通知を出力します（ON/OFF切替可能）。

### 2.3 設定画面 (Config Screen / Mod Menu Integration)
- **設定メニュー**: ゲーム内設定（Mod Menu や NeoForge MOD一覧画面の設定ボタン）から明るさの最大倍率（ガンマ値/最大輝度: 100%〜1000%等）を調整可能とします。
- 設定ファイル（JSON / TOML 等）に調整値を保存し、次回起動時も設定が維持されます。

---

## 3. プロジェクト構造 (Multi-loader Architecture)
Architectury / Fabric Loom + ModDevGradle を用いたマルチモジュール構成で構築します：
- `common/`: イベントリスナー定義・ロジック基盤・設定データモデル
- `fabric/`: Fabricクライアント用エントリポイント、Mixin、Mod Menu連携
- `neoforge/`: NeoForgeクライアント用エントリポイント、Mixin、MOD一覧設定ボタン連携
