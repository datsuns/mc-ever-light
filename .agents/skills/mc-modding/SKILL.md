---
name: minecraft-mod-development-workflow
description: Assist in designing, generating, building, and debugging Minecraft Mods (Fabric, NeoForge) and Paper plugins. Includes interactive specification gathering.
---

# Minecraft Mod開発ワークフロー (Fabric / NeoForge / Paper)

このSkillは、ユーザーの曖昧な要求からMinecraft Modやプラグインを詳細化し、自動実装、ビルド、そしてエラー発生時のデバッグをエンドツーエンドで支援するためのガイドラインです。

---

## 1. 開発ライフサイクル

開発は以下の3つのフェーズを順に実行します。

```
[フェーズ1: 仕様詳細化]
  ├ ユーザーへのヒアリング
  └ mod_specification.md の作成・合意
        ▼
[フェーズ2: コード・アセット生成]
  ├ template_generator.py の実行
  └ テンプレートコードとアセット(JSON)の出力
        ▼
[フェーズ3: ビルド & デバッグ]
  ├ gradle_runner.py によるビルド実行
  └ エラー時は error_parser.py で解析・修正ループ
```

---

## 2. フェーズ1: 仕様詳細化 (Interactive Specification)

ユーザーから「〇〇なModを作りたい」という要望を受け取ったら、直ちにコードを書き始めるのではなく、以下のステップを実行します。

### ステップ 2.1: 質問による仕様の明確化
ユーザーのアイデアを具体化するため、以下の観点から不足している情報を質問します。
- **プラットフォーム**: Fabric, NeoForge, Paper のどれをターゲットにするか。
- **基本情報**: Mod名、Mod ID、パッケージ名（例: `com.example.mymod`）。
- **要素の定義**:
  - **アイテム**: 名前、ID、機能（右クリック効果など）、満腹度（食べ物の場合）など。
  - **ブロック**: 名前、ID、硬さ、破壊に必要なツール、光るかどうかなど。
  - **レシピ**: クラフトレシピ（作業台、かまど等）、必要な素材と配置。
  - **アセット**: テクスチャのイメージ（色やデザインの特徴）。

### ステップ 2.2: `mod_specification.md` の作成
合意した仕様を、以下の標準フォーマットに則ってプロジェクトルートに `mod_specification.md` として作成（または更新）します。

```markdown
# Mod Specification - [Mod Name]

- **Platform**: [Fabric / NeoForge / Paper]
- **Minecraft Version**: [e.g., 26.2]
- **Mod ID**: [e.g., testmod]
- **Package**: [e.g., com.example.testmod]

## Elements

### Items
- **Name**: [Item Display Name]
  - **ID**: [item_id]
  - **Type**: [Standard / Food / Tool / Armor]
  - **Description**: [What it does]

### Blocks
- **Name**: [Block Display Name]
  - **ID**: [block_id]
  - **Hardness**: [e.g., 3.0]
  - **Tool**: [e.g., Pickaxe]

### Recipes
- **Type**: [Crafting / Smelting]
  - **Pattern / Ingredients**: [Describe recipe inputs]
  - **Result**: [item_id]
```

---

## 3. フェーズ2: コード・アセット生成 (Generation)

`mod_specification.md` が承認されたら、自動生成ツールを用いて実装を開始します。

1.  `.agents/scripts/template_generator.py` を呼び出し、仕様書の内容をコードに落とし込みます。
2.  スクリプトは、指定されたModding API（`templates/` にあるボイラープレート）の構造に従って、以下のファイルを適切なフォルダに生成・配置します：
    - メインModクラス（レジストリ登録処理を含む）
    - アイテムやブロックの個別クラス
    - JSONアセット（`blockstates`, `models`, `recipes`, `tags`）
      - **注意 (Minecraft 1.21.4/26.x以降)**: 新しいアイテムモデル解決システムに伴い、従来の `models/item/<item_id>.json` の作成だけではゲーム内で正しくロードされません。`assets/<modid>/items/<item_id>.json` にアイテムモデル定義ファイルを必ず作成・配置し、そこから `models/item/...` の従来モデルを参照するようにしてください。
      - **注意 (AI生成テクスチャの透過処理とモザイク回避)**: `generate_image` を使用してアイコン画像を生成する際、「透明背景 (transparent background)」を指定しても、AIはしばしば白とグレーのチェッカーボード（市松模様）を描き込みます。これを単純な単色透過処理でリサイズすると、グレーのグリッドが透過されずにゲーム内でモザイク模様になって残るトラップがあります。
        これを避けるため、テクスチャ切り抜き時には以下の手順を守ってください：
        1. 元の高解像度画像に対して「完全な白（RGB > 240）」と「薄いグレー（RGB > 170 かつ RGBの差が小さい無彩色領域、例: R, G, Bの最大値と最小値の差が15以下）」を共に透明化（Alpha=0）する。
        2. 透過処理をした後に、ニアレストネイバー（Nearest Neighbor）補間を用いて 16x16 等にリサイズし、PNGとして保存する。
    - リソースパック内の言語ファイル（`en_us.json`, `ja_jp.json`）
    - （可能であれば）`generate_image` ツールを使った16x16のピクセルアートテクスチャ（PNG）の自動作成と配置。
3.  **メタデータ・連絡先・依存バージョンの一元管理（マルチローダー構成ベストプラクティス）**:
    - `fabric.mod.json` や `neoforge.mods.toml` などのメタデータファイル内において、Minecraft 本体・依存ライブラリのバージョン、説明文 (`description`)、ホームページ・ソースコード等の URL (`contact` / `displayURL`) を直接ハードコードしてはなりません。
    - バージョン移行や仕様変更時の不整合・手動修正漏れを防ぐため、`gradle.properties` にバージョン番号だけでなく、`mod_description`、`mod_homepage`、`mod_sources` などのメタデータもすべて一元集約し、Gradle の `expand` 機能やリソース展開処理を通じて動的に注入される構成を採用・生成してください。
    - **説明文・URL等の `expand` 適用と言語ファイル (`en_us.json`) への展開**:
      - 説明文や URL などを変数化する際は、Gradle の `processResources` における `filesMatching` タスクの展開対象をメタデータファイル (`fabric.mod.json`, `neoforge.mods.toml`) だけに留めず、英語言語ファイル (`assets/*/lang/en_us.json`) にも拡張してください（例: `filesMatching(["fabric.mod.json", "assets/*/lang/en_us.json"]) { expand properties }`）。
      - これにより、英語のデフォルト説明文を `gradle.properties` 内の `mod_description` 1箇所から、すべての設定ファイル・言語ファイルへ自動的に100%同期・置換させることができます。
    - **Mod Menu / NeoForge MOD一覧における説明文の優先順位仕様と役割の明確化**:
      - **ゲーム内表示用レイヤー (`modmenu.descriptionTranslation.<id>` / `fml.menu.mods.info.description.<id>`)**:
        Fabric の Mod Menu クライアントおよび NeoForge の MOD 一覧画面では、クライアントの言語設定に応じた言語 JSON (`lang/en_us.json` や `ja_jp.json`) 内の専用翻訳キー (`modmenu.descriptionTranslation` や `fml.menu.mods.info.description`) が**最優先で読み込まれ、メタデータの `description` を上書き表示**します。
      - **外部ツール・フォールバック用レイヤー (`fabric.mod.json` / `neoforge.mods.toml` の `description`)**:
        メタデータファイル本体に書かれた `description` は、ゲーム内（Mod Menu導入・翻訳キー存在時）では画面に表示されませんが、Prism Launcher・MultiMC・Modrinthアプリ等の外部ツールでの概要表示、未対応言語でのフォールバック、クラッシュレポート・他MODからの API 参照用に不可欠です。
      - **設計指針**: どちらか一方のみに記述するのではなく、両方のレイヤーを正確に定義し、英語のデフォルト説明文および URL は `gradle.properties` からの置換（`expand`）によって両レイヤー (`*.mod.json`/`*.mods.toml` と `en_us.json`) へ統一注入する設計を採用してください。
    - **Maven リポジトリでの実在バージョン確認**: Minecraft 本体や依存ライブラリ（NeoForge, Fabric API 等）のバージョンを更新する際は、単なる推測（`26.2.0` など）で指定すると依存関係解決に失敗するケースがあります。必ず各公式 Maven リポジトリのメタデータ（`maven-metadata.xml`）を確認し、確実に存在する最新バージョン（`-beta` サフィックスやビルド番号含む、例: `26.2.0.8-beta`, `0.154.0+26.2` など）を特定して `gradle.properties` に指定してください。
    - **バージョン命名体系のマルチローダー差異（注意）**: Fabric/バニラでは `26.x.y` のような新体系のバージョン名（例: `26.1.2`）を指定するのに対し、NeoForgeでは `21.4.x` のような従来のバージョン名（例: `21.4.138`）を使用する不一致が発生します。NeoForgeの依存解決にFabric用バージョン名を流用するとエラーになるため、それぞれのローダー公式リポジトリの命名規則に従って `gradle.properties` にプロパティを切り分けて定義・設定してください。
    - **Gradle 9.x移行と ModDevGradle（NeoForge最新ビルドツール）の必須採用**:
      - NeoForge の古いビルドプラグインである NeoGradle (`net.neoforged.gradle.userdev`) は内部で Gradle 9 で削除された内部クラス（`GUtil` 等）を利用しているため、Gradle 9.x でのビルド時にクラッシュします。
      - ルートプロジェクトを Gradle 9.x 以上のマルチプロジェクトとして構成する場合は、NeoForge サブプロジェクトを必ず最新の **ModDevGradle** (`net.neoforged.moddev`) に移行してください。これにより、Fabric Loom と同じ Gradle 9.x 環境下で安全に共存可能になります。
    - **ProcessResources における UTF-8 エンコーディング設定**:
      - メタデータファイル（`neoforge.mods.toml` や `fabric.mod.json` 等）のテキスト展開処理（`expand` 等）時に、日本語などの非ASCII文字が文字化け（ISO-8859-1等へのフォールバック）するのを防ぐため、すべてのサブプロジェクトで `tasks.withType(ProcessResources).configureEach { filteringCharset = 'UTF-8' }` を設定してください。
4.  **コード生成・ボイラープレート配置時の注意点**:
    - **キーワード置換時のアノテーション破損トラップ**:
      テンプレートやコードの文字列置換で `"modid"` や `'modid'` を実際の Mod ID に置換する際、引用符のない単なる文字列 `modid` を置換対象に含めないでください。NeoForge の `@EventBusSubscriber(modid = MODID)` 等において、アノテーション引数名 `modid` までが誤って置換され、コンパイルエラーの原因となります。必ず引用符付き（`"modid"`, `'modid'`）を対象とするか、アノテーション引数名を保護する正規表現設計を行ってください。
    - **リソース識別子クラスのマッピング差異 (`Identifier` vs `ResourceLocation`)**:
      アイテム、ブロック、カスタム属性、イベント等を登録する際のリソース識別子クラスは、ローダーおよび Minecraft バージョンのマッピング仕様に従って正しく使い分けてください。
      - **Fabric (Yarnマッピング)**: `Identifier`
        - MC 1.21.2+ 以降: `net.minecraft.resources.Identifier`
        - MC 1.20.4 以前: `net.minecraft.util.Identifier`
      - **NeoForge (Mojang公式マッピング)**: `ResourceLocation`
        - `net.minecraft.resources.ResourceLocation`
      誤ったパッケージやクラスをインポートすると、`cannot find symbol` エラーでコンパイルが失敗します。

---

## 4. フェーズ3: ビルド & デバッグ (Build & Debug Loop)

コードとアセットが生成されたら、ビルドと検証を行います。

1.  **ビルドの実行**:
    `.agents/scripts/gradle_runner.py` を実行して、コンパイルまたはビルドタスク（例: `gradlew build`）を走らせます。
2.  **エラーの検知と解析**:
    ビルドが失敗した場合、または起動テストでクラッシュした場合は、`.agents/scripts/error_parser.py` を呼び出してログやクラッシュレポートを解析します。
3.  **自己修復（Self-Healing）**:
    解析ツールが特定した「エラー箇所（ファイル名、行数）」と「エラー原因」に基づき、エージェントは自動的にソースコードの修正案を作成し、ファイルを上書きします。
4.  **再テスト**:
    修正後、再度 `.agents/scripts/gradle_runner.py` を実行し、ビルドが成功するまでこのループを繰り返します。

> [!NOTE]
> **NeoForge 初回ビルド・デコンパイル時の待機戦略**
> NeoForge 環境の初回ビルドや Minecraft バージョン更新時（`createMinecraftArtifacts` タスク等）には、Minecraft 本体の膨大なソースファイル（7,000ファイル以上）に対するデコンパイル・パッチ適用・再コンパイル処理が実行されるため、完了までに **5分〜10分以上** 要する場合があります。エージェントはこれをタイムアウトやビルドフリーズと誤認して処理を中断せず、ロングランニングタスクとして非同期で監視するか、十分な待機時間を前提として行動してください。

> [!WARNING]
> **バージョン更新時の `run/mods/` クリーンアップ注意喚起**
> Minecraft 本体のバージョンを更新（例: 26.1 -> 26.2 等）した際、`./gradlew build` が成功していても、`runClient` 起動時に `fabric/run/mods` や `neoforge/run/mods` フォルダに残っている旧環境のテスト用外部MOD（ModMenu 等）が自動読み込みされ、`NoSuchMethodError` 等でクライアントがクラッシュするトラップがあります。バージョン移行時やクライアント起動クラッシュ時は、必ず `run/mods/` 内に残存する古いサードパーティ製MODを削除または退避してください。

> [!WARNING]
> **GameTest クラスの推測生成と `test` ソースセット設定の罠**
> ユーザーから明示的なテスト指示がない限り、`src/test/java` 内に推測で Minecraft 本体クラス (`net.minecraft.*`) に直接依存するテストや GameTest クラス (`...GameTest.java`) を自動生成・配置することは避けてください。Fabric Loom や NeoGradle の初期テンプレートでは `test` ソースセットに Minecraft 本体のクラスパスが通っておらず、`compileTestJava` エラーを引き起こす主要因となります。テストを自動作成する場合は「4.2 ユニットテスト構成」に従い、ゲームエンジン非依存の純粋な JUnit 5 テストとして構築してください。

### 4.1. リリース自動化と Modrinth パブリッシュ (REST API & Python)

マルチローダー（Fabric + NeoForge）構成において、Modrinth 等のプラットフォームへリリース JAR をパブリッシュする際、Loom や Minotaur などの Gradle プラグインに直接依存すると、依存関係解決の不整合やクラスローダー競合によるビルドエラーを誘発しやすくなります。これを防ぐため、Gradle タスクから Python 仮想環境上の REST API 呼び出し用スクリプトを呼び出す設計を推奨します。また、リリース時には `release_changelog.md` などの更新履歴ファイルを自動参照させ、バージョンごとの変更点を一括登録します。

### 4.2. Architectury (common/fabric/neoforge) 環境におけるユニットテスト構成

Minecraft の実サーバー/クライアントエンジンを起動せずに高速で検証を行うため、コアロジック（武器合成判定、計算倍率、ミッション状態遷移など）は `common` モジュールの `src/test/java` に分離配置し、純粋な JUnit 5 テストとして構築します。
- **ゲーム依存の分離**: `net.minecraft` クラス群に直接依存する処理と、純粋なビジネスロジック（計算・条件チェック）をインターフェースやヘルパーメソッドで分離します。
- **Gradle テストタスク**: `./gradlew test` または `./gradlew :common:test` により、ビルドパイプラインの一部として回帰テストを自動実行します。

---

## 5. 実装パターン・ベストプラクティス (全30大アーキテクチャパターン)

有名Mod（合計数億DL規模）のソースコード解析から抽出した30個の実践的な機能実装パターンと安全ガイドラインは、専用のリファレンスドキュメント [references/patterns.md](references/patterns.md) に集約・整理されています。

ユーザーからの要求仕様が連鎖破壊、HUD描画、BlockEntity/GUI、GeckoLibアニメーション、ワールド生成、マルチプレイ動的イベント、武器進化メカニクス、デバッグコマンド等に該当する場合、必要に応じて上記リファレンスファイルを参照し、標準パターンに則ってコードを生成・修正してください。

---

## 6. プラットフォームおよび Java 25 互換性注記

### 6.1. Paper (サーバープラグイン) 対応についての注意事項
- 本スキルの主要ガイドラインおよびコード生成ロジックは **Fabric** および **NeoForge** (Java Mod) に最適化されています。
- Paper プラグインの開発を行う場合は、Fabric/NeoForge API 固有の処理（Mixin, Cardinal Components, GeckoLib 等）を避け、Paper/Spigot 標準の API (`Listener`, `Event`, `PersistentDataContainer`, `BukkitRunnable` 等) に適切に読み替えてコードを構築してください。

### 6.2. Java 25 ツールチェーン利用時の互換性・ガード規定
本プロジェクトでは **Java 25 (Class file major version 69.0)** の利用が必須前提条件です。
- **コンパイル設定**: `java.toolchain.languageVersion = JavaLanguageVersion.of(25)` を指定します。
- **ビルドツール互換性ガード**: 古いビルドプラグインや古い ASM (9.7以前) が原因で `Unsupported class file major version 69` クラッシュが発生するのを防ぐため、Fabric プロジェクトでは **Fabric Loom 1.9+**、NeoForge プロジェクトでは **ModDevGradle (`net.neoforged.moddev`)** の最新版を必ず使用してください。
