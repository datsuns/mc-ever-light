# EverLight (エバーライト)

[![Minecraft](https://img.shields.io/badge/Minecraft-1.21.4%20(26.2)-brightgreen.svg)](https://minecraft.net/)
[![Java](https://img.shields.io/badge/Java-25-orange.svg)](https://openjdk.org/)
[![NeoForge](https://img.shields.io/badge/NeoForge-26.2-blue.svg)](https://neoforged.net/)
[![Fabric](https://img.shields.io/badge/Fabric-1.21.4-purple.svg)](https://fabricmc.net/)
[![English Docs](https://img.shields.io/badge/Language-English%20%7C%20%E6%97%A5%E6%9C%AC%E8%AA%9E-informational.svg)](README.md)

**EverLight** は、Minecraft **1.21.4 (26.2)** 向けの高機能・軽量マルチローダー（**NeoForge** & **Fabric** 対応）明暗調整・暗視（Fullbright）Mod です。

[Click here for English Documentation (README.md)](README.md)

---

## ✨ 主な機能

- 💡 **ワンタッチ視界全開 (Fullbright)**: 洞窟や夜間、水中でもワンキーで即座に昼間同様の明瞭な視界を確保。
- 🧘 **画面を汚さないクリア設計**: 暗視パーティクル粒子や右上のバフエフェクトアイコン、画面点滅は一切表示されません。
- 🎚️ **明るさレベルの自由調整 (1.0 〜 10.0)**:
  - **スライドバー ＋ 数値入力ボックス** による直感的な設定 GUI。
  - 控えめな明暗補正から完全な全開暗視までレベルに合わせて動的に可変設定可能。
- 🔌 **ローダー標準設定メニューとの統合**:
  - **NeoForge**: 組み込み Mod リスト画面の「設定 / Config」ボタンから遷移。
  - **Fabric**: **ModMenu** の GUI メニューから遷移。
- 💾 **設定の自動永続化**: 変更した設定は `config/mc_ever_light.properties` へ自動保存されます。

---

## ⌨️ 操作方法・キー割り当て

| 操作 | デフォルトキー | 説明 |
| :--- | :---: | :--- |
| **ライト ON / OFF 切替** | `G` | ゲーム中に EverLight の有効・無効を切り替えます（HUDメッセージ表示）。 |
| **設定画面表示** | 各Modメニュー | スライダーで明るさレベル（1.0 〜 10.0）を調整する設定画面を開きます。 |

※キー割り当てはバニラの「操作設定 (Key Binds)」から自由に変更できます。

---

## ⚙️ 設定 GUI メニュー

EverLight の設定画面は、**スライダーと数値入力ボックスが双方向に連動**します：
- **スライダー操作**: マウスドラッグで数値を連続変更。
- **数値入力**: キーボードで `1.0` 〜 `10.0` の数値を直接入力すると、スライダー位置が即座に同期。
- **Done (完了)** ボタン押下で即座にゲーム内に反映され、設定ファイルへ保存されます。

---

## 🛠️ ソースコードからのビルド手順

本プロジェクトは Java 25 を利用したマルチプロジェクト構成（Gradle）となっています。

```bash
# リポジトリのクローン
git clone https://github.com/datsuns/mc-ever-light.git
cd mc-ever-light

# 全モジュール (Common, NeoForge, Fabric) のビルド
./gradlew build
```

ビルド完了後、各サブモジュールの `build/libs` 配下に JAR ファイルが生成されます：
- `neoforge/build/libs/mc-ever-light-1.0.0-neoforge-mc1.21.4.jar`
- `fabric/build/libs/mc-ever-light-1.0.0-fabric-mc1.21.4.jar`

---

## 📄 ライセンス

本 Mod は [MIT License](LICENSE) の下で公開されています。Modpack への組み込みや再配布は自由に行っていただけます。
