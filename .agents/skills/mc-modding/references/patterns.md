# Minecraft Mod実装パターン・ベストプラクティス (全30大アーキテクチャパターン)

世界中であまたダウンロードされている有名Mod（合計数億DL規模）のソースコード解析から抽出した、実践的な機能実装パターンと安全ガイドラインです。ユーザーからの要求仕様が以下の機能に該当する場合、これら標準パターンに則ってコードを生成・修正してください。

> [!IMPORTANT]
> * **アイテムモデル解決システムの新仕様への移行 (1.21.4 / 26.2以降)**:
>   従来の `assets/<modid>/models/item/<item_id>.json` に加え、**`assets/<modid>/items/<item_id>.json`** という新仕様のモデル定義ファイルが必須となりました。これが不足しているとゲーム内でアイテムが missing texture（黒とピンクのチェック柄）になります。必ず `items/` ディレクトリ配下に定義ファイルを作成し、アセット展開を行ってください。
> * **特定ツールクラス（PickaxeItem, SwordItem, ArmorItem等）および Tiers enum の廃止**:
>   これらの特定のツールや装備用クラスは完全に廃止され、標準の `Item` クラス単体に統合されました。
> * **Data Component（データコンポーネント）による挙動定義**:
>   ツールの採掘速度や破壊可能ブロックなどの挙動は、`Item.Properties` を通じて `DataComponents.TOOL` 等のコンポーネントをアタッチすることで定義します。自動生成や実装時には、古い Java クラス（`PickaxeItem` や `Tiers` 等）をインポート・インスタンス化しないように注意してください。

---

### パターンA: プレイヤー採掘イベント・再帰破壊 (連鎖破壊系)
- **対象機能**: 木のまとめ切りや鉱石の連鎖破壊機能。
- **イベントフック**: `PlayerBlockBreakEvents.BEFORE` を使用。プレイヤーが破壊した最初のブロック（起点）を検知し、処理をフック。
- **アルゴリズム最適化 (BFS/DFS)**:
  - ブロックの探索には `Queue<BlockPos>` を用いた幅優先探索（BFS）または深さ優先探索（DFS）を使用。
  - **サーバー負荷対策**: 1ティックに破壊・探索する最大ブロック数上限（例: 64〜128ブロック）や探索距離上限（半径）を必ず設定し、メインスレッドのフリーズを防ぐ。
- **アイテムドロップと耐久度消耗**:
  - ドロップアイテムは破壊した各座標ではなく、**「最初に破壊した起点のブロック座標」に集約してスポーン**させることで、クライアントの描画ラグ（大量のアイテムエンティティ浮遊）を防止。
  - 破壊したブロック数に応じてツールの耐久度を正しく消費させ、耐久度が0になる前に破壊を止めるセーフティガード（`itemStack.damage(...)` と破損判定）を実装。

### パターンB: HUDオーバーレイ・クライアント状態同期 (ステータス表示系)
- **対象機能**: 満腹度・隠しパラメータ（隠しステータス、マナ等）の画面描画や情報表示。
- **差分同期パケット (Delta Sync Pattern)**:
  - 毎ティック全データを送信してネットワーク帯域を無駄にしないため、サーバー側で `Map<UUID, Value>` をキャッシュ。
  - **変更が検知された瞬間のみ**クライアントへ差分パケット（`SaturationSyncPacket` 等）を送信する設計にする。
- **HUD描画 (RenderGameOverlay / HudRenderCallback)**:
  - `HudRenderCallback.EVENT` や Mixin を用いてバニラのHUD描画に介入。
  - **他Mod描画との互換性**: バニラの体力バーや満腹度バーの位置変更（他Modによる拡張）に動的に追従できるよう、固定座標（ハードコード）を避け、描画コンテキストのオフセット座標を参照する。
  - **イベントバス設計**: 自作Modの描画前後にカスタムイベントをパブリッシュすることで、他のHUD系Modが描画位置を調整できるようにする。

### パターンC: BlockEntity・GUIコンテナ・ネットワーク通信 (永続データ・UI系)
- **対象機能**: 独自のインベントリや座標情報を保持するブロック（テレポート装置、特殊かまど、チェスト等）。
- **最新Fabric Networking (1.20.5+/1.21.2+ Payload System)**:
  - `PayloadTypeRegistry.playC2S().register(ID, CODEC)` と `PayloadTypeRegistry.playS2C().register(ID, CODEC)` でレコードクラスのペイロードを登録。
  - **スレッド安全性の鉄則**: `ServerPlayNetworking.registerGlobalReceiver` の受信処理はNetty I/Oスレッドで動くため、**必ず `context.server().execute(() -> { ... })` で包み、サーバースレッド上で同期実行**する。これを怠るとワールド破損や競合クラッシュの原因となる。
- **BlockEntityのコンポーネント対応 (1.21.2+ 準拠)**:
  - アイテムのデータがData Component化されたため、`readNbt` / `writeNbt` でインベントリ（`Inventories.readNbt`/`writeNbt`）を操作する際は、必ず第一引数または第二引数の `RegistryWrapper.WrapperLookup lookup` を渡す。
- **拡張GUI同期 (ExtendedScreenHandlerFactory)**:
  - BlockEntityから画面を開く際、通常のインベントリ以外のメタデータ（座標、名前、オーナーUUID等）を初期同期するため、`ExtendedScreenHandlerFactory<Payload>` を実装して `openHandledScreen` を呼び出す。

### パターンD: Mod Menu統合とUIインジェクト (GUI拡張・設定連携系)
- **対象機能**: Modのコンフィグ画面の追加や、バニラ画面（タイトル、ポーズ画面等）へのカスタムボタン追加。
- **ModMenuApi 連携**:
  - `fabric.mod.json` の `modmenu` エントリポイントに `ModMenuApi` の実装クラスを登録。
  - `getModConfigScreenFactory()` で設定画面ファクトリを返し、他Modの設定画面（Cloth Config等）へスムーズに遷移させる。
- **MixinExtrasを用いた堅牢なUIボタンインジェクト**:
  - タイトル画面等の `init` へのボタン追加時、従来の脆弱な行番号やバイトコードインデックス指定ではなく、**MixinExtras**（`@Definition` と `@Expression`）を活用して対象箇所を安全に特定する。
  - ウィジェットの追加には Fabric API の `Screens.getWidgets(screen).add(new ButtonWidget(...))` を使用。

### パターンE: Cardinal Components API (カスタムデータ動的アタッチ系)
- **対象機能**: プレイヤー、エンティティ、アイテム（ItemStack）、ワールド等への独自パラメータや状態の保存・同期。
- **統一コンポーネントアクセス (ComponentKey Pattern)**:
  - 個別のNBT操作や手動パケット実装を避け、共通インターフェース（例: `MyVitaComponent`）と `ComponentKey` を定義。
  - `MyComponent.KEY.get(entity)` または `KEY.maybeGet(itemStack)` で型安全にアクセス・操作する。
- **自動ネットワーク同期と永続化**:
  - サーバー側で値を変えた後、`component.sync()` または `component.syncWithAll(server)` を呼ぶだけで、パケット生成・送信・クライアント同期が全自動で行われる。
  - バニラの保存システムに自動介入し、独立したコンポーネントタグ内に安全に永続化される。

### パターンF: Cloth Config API (動的GUIライブラリ・設定保存インフラ系)
- **対象機能**: 高機能な設定画面（GUI）の構築と設定値のJSON/YAML保存。
- **AutoConfig パターン (推奨・アノテーション駆動)**:
  - `ConfigData` を継承したPOJOクラスに `@Config(name = "modid")` とフィールドアノテーション（`@ConfigEntry.Gui.Tooltip`, `@ConfigEntry.BoundedDiscrete` 等）を記載。
  - `AutoConfig.register(MyConfig.class, GsonConfigSerializer::new)` だけで設定ファイル永続化とGUI生成を完了させる。
- **Cloth Config Builder パターン (動的構築)**:
  - 画面構造をプログラムで動的に変えたい場合、`ConfigBuilder.create()` から `entryBuilder()` を用いてカテゴリや入力欄を動的に組み立てる。
  - 各入力欄の `.setSaveConsumer(...)` とビルダーの `.setSavingRunnable(...)` で永続化を制御する。

### パターンG: ワールド生成・バイオーム・構造物 (TerraBlender, YUNG's API)
- **対象機能**: 新規バイオームの安全な追加、カスタムディメンション、およびジグソー構造物（村やダンジョン等）の生成。
- **専用ワールド生成APIの利用 (Mixin直接介入の回避)**:
  - バニラの `Structure` やバイオーム生成処理への無秩序な `@Overwrite` Mixin は、他社ワールド生成Mod（Biomes O' Plenty, Terralith等）との致命的な競合を招くため禁止。
  - **TerraBlender**: `Region` クラスを拡張してバイオームウェイトを登録し、`SurfaceRuleManager` を介して地表ルールを安全にマージする。
  - **YUNG's API**: ダンジョンや村などの複雑な構造物は `YungJigsawStructure` やカスタムの `StructurePoolElement` を用いてData Pack駆動で安全に拡張する。

### パターンH: 3Dモデル・アニメーション・エンティティ (GeckoLib)
- **対象機能**: 複雑な関節アニメーションを持つモブ、3Dアイテム、カスタムブロックの描画と制御。
- **共通アニメーションインターフェース (`GeoAnimatable`)**:
  - モブ (`GeoEntity`)、アイテム (`GeoItem`)、ブロック (`GeoBlockEntity`) で同一のステートマシン定義 (`registerControllers`) とインスタンスキャッシュ (`GeckoLibUtil.createInstanceCache`) を共有する。
- **自動ネットワーク同期 (`triggerAnim`)**:
  - サーバー側で `entity.triggerAnim("controller", "anim_name")` を呼ぶだけで、内部の `GeckoLibServices.NETWORK` がトラッキング中の全クライアントへパケットを自動配信するため、手動パケット実装は不要。
- **規約ベースのアセット解決 (`DefaultedGeoModel`)**:
  - `new DefaultedEntityGeoModel<>(MY_MOB)` を用いることで `assets/<modid>/geo/entity/<name>.geo.json` 等を自動解決する。

### パターンI: レシピ・アイテム統合検索・ビューアーAPI (REI, EMI)
- **対象機能**: 独自作業台や特殊加工機械のレシピをインゲームのレシピビューアーへ動的に追加・表示させるプラグイン連携。
- **宣言的プラグイン登録 (Optional Dependency)**:
  - **REI**: `REIClientPlugin` を実装し、`fabric.mod.json` の `"rei_client"` に登録。
  - **EMI**: `EmiPlugin` を実装し、`fabric.mod.json` の `"emi"` に登録。
  - 本体初期化とは分離し、ビューアー導入時のみ動的にクラスをロードする構造にする。
- **5大レジストリ連携**:
  1. `registerCategories` / `addCategory`: 背景・アイコン・タイトルの定義。
  2. `registerDisplays` / `addRecipe`: `RecipeManager` からレシピを取得してスロットマッピング。
  3. `registerScreens` / `addWorkstation`: 進捗矢印クリック時のジャンプと作業台アイコン紐付け。
  4. `registerExclusionZones` / `addExclusionArea`: サイドバー・タブとの重なり除外ゾーン設定。
  5. `registerTransferHandlers` / `addRecipeHandler`: 「+」ボタン押下時の自動クラフトアイテム転送。

### パターンJ: パフォーマンス最適化・描画物理介入 (Sodium, Lithium)
- **対象機能**: 描画パイプライン、モブAI、物理演算、ブロック更新処理等の高速化とメモリ最適化。
- **グラニュラーMixin設定プラグイン (`IMixinConfigPlugin`)**:
  - `IMixinConfigPlugin` を実装し、`onLoad()` でコンフィグを読み込み、`shouldApplyMixin()` で個別の最適化ルール（クラス・パッケージ単位）ごとに適用可否 (`true`/`false`) を動的判定する。
  - 競合する他社軽量化Mod（Embeddium, OptiFine等）を検知した場合、競合するMixinを自動で無効化する安全装置を組み込む。
- **ドメイン分割と非破壊Mixin (`@WrapOperation`)**:
  - ターゲットを責務ごと (`ai`, `entity`, `block`, `hopper`, `world`) に徹底分割。
  - 破壊的な `@Overwrite` を避け、非破壊的な `@WrapOperation` を多用して高い互換性を維持する。

### パターンK: マルチブロック・管路・大容量ストレージ (AE2, Tom's Storage)
- **対象機能**: アイテム/エネルギー管路、複数ブロックをまたぐネットワーク、64個制限を超える大容量インベントリ。
- **64ビット整数型ストレージ抽象化 (`AEKey` / `StoredItemStack` + `long`)**:
  - バニラの `ItemStack` (最大64個・int制限) を排除し、アイテムを不変のキー (`AEKey` / アイテム+NBT) と `long` 型の数量で管理。`KeyCounter` でネットワーク全体の在庫を集計。
- **2フェーズアクションシミュレーション (`SIMULATE` vs `MODULATE`)**:
  - アイテム移動時、必ず事前に `SIMULATE` パスを実行して受入容量・抽出可能量を検証。成功時のみ状態を変化させ、アイテムロストや増殖バグを排除する。
- **グラフ構造によるトポロジーキャッシュ (`IGrid` / `InventoryCableNetwork`)**:
  - 毎tick `level.getBlockEntity()` を探索する処理を避け、ケーブルをメモリ上のグラフ (`IGridNode`) に登録し、設置・破壊時のみトポロジーを再構築・キャッシュする。

### パターンL: ユーティリティ・インベントリUX・ホットキー (Mouse Tweaks, Controlling)
- **対象機能**: インベントリスクリーンのドラッグ操作拡張、キーバインド競合検知、検索UI拡張。
- **コンテナスクリーン抽象化 (`IGuiScreenHandler`)**:
  - コンテナスクリーンを共通インターフェースでラップし、`getSlotUnderMouse` や `clickSlot` を抽象化。右クリックドラッグやホイールスクロールを疑似クリックイベント (`handleInventoryMouseClick`) に変換して送出することで、あらゆるGUIと互換性を維持する。
- **キーバインドAccessor Mixin (`AccessKeyMapping`)**:
  - バニラの `KeyMapping` に `@Accessor` Mixin を注入してキーコード (`InputConstants.Key`) にアクセス。全キーコード配列から登録済みキーを差分フィルタリングして「未割り当てキー一覧」や競合キーをリアルタイム検知する。

### パターンM: チャット・コマンド・サーバー権限管理・環境調整 (Fabric Carpet, LuckPerms)
- **対象機能**: サーバーコマンドの権制限御、カスタムゲーマルール、および権限プラグイン連携。
- **宣言的ルール＆コマンド統括マネージャー (`SettingsManager` / Carpet)**:
  - `@Rule` アノテーションで修飾されたルール設定クラスを `SettingsManager` で一括管理。サーバー起動時に専用ルートコマンド (`/<modid> <ruleName> <value>`) を自動生成し、変更時は全クライアントへパケット同期する。
- **イベント駆動型権限ルーティング (`PermissionCheckEvent` / `fabric-permissions-api`)**:
  - 固定のOPレベル判定 (`source.hasPermission(4)`) をハードコードせず、`fabric-permissions-api` (`Permissions.check(source, "mymod.command.admin", 4)`) を介する。
  - これにより発火する `PermissionCheckEvent` を LuckPerms 等がフックし、インメモリの `PermissionCache` からO(1)で権限状態を高速判定する設計にする。

### パターンN: レンダリングパイプライン＆シェーダー互換API (Iris Shaders, Indium, Continuity)
- **対象機能**: カスタム3Dブロック描画、シェーダーパック互換性維持、接続テクスチャ。
- **Fabric Rendering API (`RendererAccess` / Indium) の徹底**:
  - ブロックモデルやメッシュ生成時、バニラの `BlockModelRenderer` に直接依存するハードコードを避ける。必ず `RendererAccess.INSTANCE.getRenderer().meshBuilder()` を使用し、Sodium / Indium の高速レンダーパイプラインと100%互換なメッシュ転送を行う。
- **シェーダーシャドウパスガード (`IrisApi` / Iris Shaders)**:
  - `IrisApi.getInstance().isShaderPackInUse()` でシェーダー稼働状態を監視し、特にシャドウパス描画中 (`isRenderingShadowPass()`) は2DマップやUIオーバーレイ等の描画を一時非表示にして、影演算破綻や視覚アーティファクトを自動回避する。

### パターンO: 非同期ワールドマッピング＆3Dマッピングエンジン (BlueMap, Xaero's Minimap)
- **対象機能**: ミニマップ、ワールドマップ描画、3Dウェブマップ出力。
- **非同期NIOリージョン解析とスレッドセーフチャンク参照 (`MCARegion` / BlueMap)**:
  - マッピング描画時、サーバーメインスレッドで `world.getChunk(...)` を同期呼び出しすると致命的なラグやデッドロックを招く。
  - ノンブロッキングセーブ (`saveAllChunks(false, true, true)`) を行った上で、バックグラウンドスレッドにて `.mca` リージョンファイルを NIO `FileChannel` で直接パースしてチャンクデータを非同期読み取りするアーキテクチャを採用する。

### パターンP: 3D音響物理＆環境サウンドエンジン (Sound Physics Remastered, Presence Footsteps)
- **対象機能**: リアルタイム残響・リバーブ、音響吸音計算、足音マテリアルマッピング。
- **マルチバウンス音響レイトレーシング＆反射率計算 (`RaycastUtils` / Sound Physics)**:
  - 環境音響シミュレーションにおいて単なる直線距離を使わず、音源からプレイヤーへ16〜32本の音響レイ（光線）を放射 (`RaycastUtils.rayCast`) する。
  - ブロック衝突表面の反射率 (`blockReflectivity`) と空気共有空間 (`sharedAirspace`) を積算して残響（リバーブ）およびローパスフィルターの減衰係数を算出する音響物理アーキテクチャ。

### パターンQ: UDPリアルタイム通信＆ボイスチャット暗号化 (Simple Voice Chat)
- **対象機能**: ボイスチャット、大容量リアルタイムストリーミング通信。
- **独立UDPデータグラムストリーミング＆暗号化認証 (`VoiceProxyServer` / Simple Voice Chat)**:
  - 高頻度な音声ストリーミングや大容量データを Minecraft 標準の TCP/Netty パケット (`ServerPlayNetworking`) に流すと、再送処理によるヘッドオブラインブロッキングが発生する。
  - 必ず独立した UDP `DatagramSocket` を専用ポートにバインドし、MinecraftのUUIDと紐付けた暗号化ハンドシェイクにより低遅延なストリーミングパイプラインを確立する。

### パターンR: 高度なモブAI・Brain/Memoryシステム・パスファインディング (Alex's Mobs, Naturalist)
- **対象機能**: カスタムモブの複雑な行動ツリー、捕食・警戒AI、立体経路探索。
- **モジュラーAIゴール＆動的ターゲットセレクター注入 (`Goal` / Alex's Mobs)**:
  - 複雑なモブAI行動の追加や変更において、バニラのエンティティクラスを Mixin 等で直接上書きしない。
  - 独立したカスタム `Goal` サブクラスを作成し、`registerGoals()` またはエンティティスポーンイベント (`ServerEvents`) にて `goalSelector.addGoal` / `targetSelector.addGoal` で動的にAIタスクを注入・拡張するモジュラー行動設計。

### パターンS: エネルギーネットワーク＆工業・魔術抽象化API (TechReborn, Botania)
- **対象機能**: 工業系エネルギー管路・機械、魔術マナ伝送、祭壇クラフト。
- **Fabric標準EnergyStorage＆BlockApiCache最適化 (`EnergyStorage` / TechReborn)**:
  - 工業系エネルギーネットワークにおいて、毎tick全隣接ブロックの `BlockEntity` キャスティングや導通判定を行うと致命的なサーバー負荷となる。
  - 必ず Fabric 標準の `team.reborn.energy.api.EnergyStorage.SIDED` を使い、隣接ブロック参照を `BlockApiCache<EnergyStorage, Direction>` にキャッシュして計算オーバーヘッドをゼロに抑える最適化設計。
- **非依存型リソース伝送パケット＆火花ネットワーク (`ManaBurst` / Botania)**:
  - 魔術・独自エネルギー（マナ等）の伝送において、通常のインベントリやエネルギーパイプラインとは完全に分離した専用エンティティ（光線・バースト・火花）を発射させることで、距離減衰・損失率計算と視覚エフェクトを両立させる抽象化アーキテクチャ。

### パターンT: インベントリ自動整理＆クライアントUX拡張 (Tweakeroo, ItemScroller, IPN)
- **対象機能**: インベントリスクロール、高速一括クラフト、操作遅延シミュレーション。
- **楽観的クライアント同期＆操作遅延レートリミット (`rightClickDelayTimer` / ItemScroller & Tweakeroo)**:
  - インベントリの連続移動や高速一括クラフトを行う際、サーバーからのパケット同期を待たずに連続でパケットを送信すると、深刻なインベントリ同期ズレ（デシンク）や、サーバー側アンチチート（NoCheatPlus等）によるチート誤検知・BANを引き起こす。
  - 必ずクライアント側でスロット状態を楽観的に予測更新（Optimistic UI）しつつ、バニラ標準の `rightClickDelayTimer`（4 tick）や操作インターバルを尊重・シミュレートするパケット送信キューイングを組み込み、安全かつ高速なクライアント操作を実現する。

### パターンU: カスタムノイズ・ディメンション＆高度な地表ルール (Terralith, Biomes O' Plenty)
- **対象機能**: バイオーム分布制御、特殊地表レイヤー生成、カスタムディメンション。
- **Data Packドリブン地形生成＆TerraBlender SurfaceRules統合 (`SurfaceRules` / Terralith & BOP)**:
  - 現代の Minecraft (1.18〜1.21+) において、カスタムバイオームや地表レイヤー（テラコッタ、特殊土壌等）の生成を行う際、カスタム `ChunkGenerator` を実装したり Java コード内でノイズループを直接オーバーライドしてはならない（シェーダーや他ワールド生成Modとの互換性を完全に破壊するため）。
  - 地形の骨格や密度関数 (`density_functions`) は Data Pack (JSON) ドリブンで構築し、地表マテリアルの適用やバイオームブレンドは TerraBlender の `SurfaceRuleManager.addSurfaceRules(...)` を介して合成可能な `SurfaceRules` として登録する現代的ワールドジェネレーション設計。

### パターンV: 動的ライト・光源計算最適化 (Dynamic Lighting & Light Engine Optimization)
- **対象機能**: 手に持った松明や発光エンティティによるリアルタイム光源計算機能（LambDynamicLights, RyoamicLights, Starlight 等）。
- **クライアント空間ルックアップ＆非同期ライトインジェクション (`computeSpatialLookup`)**:
  - 手に持った松明や発光エンティティが移動するたびに、サーバー側のバニラ光計算 (`level.getLightEngine().checkBlock(...)`) を呼び出すと深刻なラグやFPS低下が発生するため、**サーバー側の光エンジンは一切呼び出してはならない**。
  - 光の追跡は完全にクライアント側に分離し、活動中の光源 (`Set<DynamicLightSource>`) を空間ルックアップテーブル (`computeSpatialLookup`) で管理する。その上で、レンダー時 (`EntityRendererMixin` / `ClientLevelMixin`) に座標移動 (`shouldTick`) を検知した差分のみシェーダーやボクセルライトに輝度を直接注入する非同期ライトインジェクション設計を採用する。

### パターンW: カメラアニメーション・映画的演出・シネマティックパイプライン (Cinematic Camera & Viewport Control)
- **対象機能**: 飛行時のロール傾斜や映画的カメラワーク、フリーカム演出機能（Replay Mod, Do a Barrel Roll, Freecam 等）。
- **3軸カメラインターフェース注入＆イベント駆動補間 (`RollCamera`)**:
  - バニラのカメラシステム (`net.minecraft.client.render.Camera`) はピッチとヨーの2軸回転しか持たないため、飛行時の傾き（ロール）や映画的演出を実装する際、プレイヤー本体のエンティティ角度を操作してはならない（操作ベクトルや当たり判定が完全に破綻するため）。
  - Mixin を用いて `Camera` に独自の3軸回転インターフェース (`RollCamera: setRotation(yaw, pitch, roll)`) を注入し、描画前後でトリガーされる専用イベントバス (`EARLY/LATE_CAMERA_MODIFIERS`) を介して滑らかなクォータニオン補間やベジェ曲線演出を適用するデカップリング設計を行う。

### パターンX: スキルツリー・RPGステータス・進行度システム (RPG Progression, Skill Trees & Perk Systems)
- **対象機能**: スキルツリー、ソケットジェム、アフィックス、ステータスポイント分配機能（Apotheosis, Pufferfish's Skills, PlayerEX 等）。
- **Data Pack駆動型属性バインディング＆イベントインジェクション (`RandomAttributeModifier`)**:
  - RPGスキルやステータス補正を実装する際、Javaコード内に固定値や計算ロジックを直書きしたり、バニラのエンティティベース属性を直接永続変更してはならない（リログ時や再計算時に属性値が二重付与されたりデータ破損する原因となるため）。
  - ステータス補正仕様はすべて Data Pack (JSON) 内の `RandomAttributeModifier` としてデータ化し、適用時は一意のUUIDを伴う一時的なイベントフック (`StackAttributeModifiersEvent` / `ItemAttributeModifierEvent`) を介して動的に付加・分離するクリーンなスタック設計にする。

### パターンY: マルチパートエンティティ・搭乗物・複雑コリジョン (Multi-part Entities, Vehicles & Complex Hitboxes)
- **対象機能**: 飛行船、巨大機械、複数当たり判定を持つ大型搭乗物やマルチパートボス機能（Create, Immersive Aircraft, Eureka / Valkyrien Skies 2 等）。
- **二重座標空間変換＆ShipTransform行列インジェクション (`ShipTransform`)**:
  - 飛行船などのマルチパート動的構造物を動かす際、ワールド空間のブロック座標やエンティティ座標を毎tick直接移動・更新してはならない（莫大なブロック更新ログや同期ズレ、ラグの原因となるため）。
  - 船体専用のローカル座標系（Ship Space）を構築し、ワールド空間との変換行列 (`ShipTransform: worldToShip / shipToWorld`) を保持する。当たり判定 (`MixinEntity`)、描画 (`MixinLevelRenderer`)、カメラ視点 (`MixinCamera`) の各フック時に座標をリアルタイム変換する二重座標空間アーキテクチャを採用する。

### パターンZ: トランザクション型経済・ショップ・街構想＆領地保護 (Economy, Shop UI & Land Claim Protection)
- **対象機能**: 通貨取引、プレイヤー間ショップ、街づくり、チャンク領地保護機能（FTB Chunks / Teams, Lightman's Currency, OpenPartiesAndClaims 等）。
- **アトミックデータアタッチメント財布＆チャンク境界イベントフック (`ClaimedChunkManager`)**:
  - 経済システムやショップ、領地保護を実装する際、インベントリ通常スロットのアイテム移動に依存して取引を行ったり、クライアント側の判定でブロック破壊・侵入を制御してはならない（アイテム増殖＝デュープやチートによる領地荒らしを引き起こすため）。
  - 通貨はプレイヤーデータに直接アタッチされたアトミックな専用スロット (`LCDataAttachments.WALLET` / `WalletSlot`) を介してサーバー主導で決済し、領地保護はサーバー全体のインタラクションイベント（破壊、設置、ピストン、流体、延焼）を中央のチャンク管理API (`ClaimedChunkManager`) でフックして状態更新前に即キャンセルする堅牢なトランザクション設計を採用する。

### パターンAA: マルチプレイ対応型個別GUI一時停止とインゲーム脅威隔離 (Level-Up Pausing & Threat Isolation)
- **対象機能**: レベルアップ時のアイテム選択画面、またはプレイヤーがインゲームで安全に操作・閲覧する必要があるカスタムGUI画面。
- **コンテナ消去・離脱イベントフックの徹底 (`removed`)**:
  - GUI内の「決定ボタン」等のクリックイベントのみで一時停止状態や無敵状態の解除（クリーンアップ）を行うと、プレイヤーがインベントリキー（Eキー）やEscapeキーでGUIを閉じた際に状態が解除されず、無敵状態のままゲームが継続するなどの致命的な脆弱性になります。
  - 必ずカスタム `ChestMenu` クラスにおいて `removed(Player player)` をオーバーライドし、画面が閉じる際の最終クリーンアップ処理（一時停止フラグの解除、無敵属性の無効化等）がどのような離脱経路でも100%実行されるように設計します。
- **マルチプレイ対応の一時停止＆脅威隔離 (Individual Pausing)**:
  - サーバーのグローバルなティック進行を止めるのではなく、対象プレイヤーに紐づくセッションオブジェクトに `paused` フラグを設けて個別にゲームタイマー進行や自動攻撃をバイパスします。
  - レベルアップ中はプレイヤーに一時的なサーバー側無敵属性（`player.setInvulnerable(true)`）を設定し、さらにティックイベント等でプレイヤーの周囲（例: 半径30ブロック）にいるモンスターの標的をクリア（`monster.setTarget(null)`）することで、他のプレイヤーの進行を邪魔することなく、対象プレイヤーを安全に脅威から隔離します。
- **具体的なコード実装パターン**:
  - **メニューのクリーンアップ処理 (Menu Class)**:
    ```java
    @Override
    public void removed(Player player) {
        super.removed(player);
        if (!player.level().isClientSide() && player instanceof ServerPlayer sp) {
            SurvivalSession session = SurvivalGameManager.getSession(sp.getUUID());
            if (session != null) {
                session.setPaused(false);
            }
            sp.setInvulnerable(false); // 無敵の解除
        }
    }
    ```
  - **サーバースレッドTickでの脅威隔離 (Game Logic: Fabric API `ServerTickEvents` 例。NeoForgeの場合は `ServerTickEvent.Post` を使用)**:
    ```java
    ServerTickEvents.END_SERVER_TICK.register(server -> {
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            SurvivalSession session = activeSessions.get(player.getUUID());
            if (session != null && session.isActive()) {
                if (session.isPaused()) {
                    // 周囲のモンスターのターゲットをクリアして安全を確保する
                    List<Monster> monsters = player.level().getEntitiesOfClass(Monster.class, player.getBoundingBox().inflate(30.0));
                    for (Monster monster : monsters) {
                        if (monster.getTarget() == player) {
                            monster.setTarget(null);
                        }
                    }
                    continue; // 一時停止中はセッションタイマー等の処理をスキップ
                }
                session.incrementTick();
                // ... 通常のゲーム更新処理
            }
        }
    });
    ```

### パターンAB: マルチプレイ対応MODでの動的イベント実装パターン (Co-op Mission / Dynamic Event System)
- **対象機能**: 祭壇防衛や時間制限ミッションなど、ワールド内で動的に発生するマルチプレイ協力イベント。
- **サーバー主導のミッションライフサイクル**:
  - イベントの生成・タイマー更新・状態遷移（待機・開始・進行・成功/失敗判定・報酬処理）はすべてサーバースレッド主導で行う。
  - タイマーや進行度（例: 防衛成功率、ウェーブ数）は `CustomPayload` パケットを用いて周期的または変化時にクライアントへS2C同期する。
- **エリア判定とマルチプレイヤーの同期**:
  - イベント発生地点からの距離判定（`BoundingBox.inflate` や `BlockPos.distSqr`）を介して、周辺にいる全プレイヤーにミッションHUDや演出パーティクルを表示する。
  - イベント中限定のオブジェクティブ（祭壇への敵侵入検知や防衛対象の耐久値減少）をサーバースレッドのTickイベントで安全に評価・監視する。

### パターンAC: 武器・アクティブ/パッシブアイテムの進化（合成）メカニクス (Weapon Evolution & Craft Synergy)
- **対象機能**: 特定レベルに達したメイン武器と指定のパッシブアイテムを組み合わせた上位武器への進化・合成処理（Survivors / Roguelike系メカニクス）。
- **条件判定とデータ駆動マッピング**:
  - メイン武器のレベルMAX到達判定（データコンポーネントまたはNBT参照）と、プレイヤーの所持インベントリ内にある特定パッシブアイテムの有無を判定する。
  - 合成レシピはハードコードを避け、`EvolutionRecipe` クラスやデータパック対応のレジストリ（`MainItem + PassiveItem -> EvolvedItem`）としてマッピング管理する。
- **宝箱・リザルト時の決定と置換アトミック処理**:
  - 条件を満たした状態で宝箱開封や進化イベントが発生した際、メイン武器を削除し上位武器を生成付与する処理は、インベントリ操作時の整合性を保つためアトミックに同一ティックで実行する。

### パターンAD: 開発・デバッグ支援コマンドツリー構築 (Brigadier Command Framework for Debugging)
- **対象機能**: イベントの強制発動、フェーズ即時変更、特定アイテム/ステータス付与などの開発・テスト用コマンド。
- **Brigadier コマンド登録**:
  - `CommandRegistrationCallback` (Fabric) または `RegisterCommandsEvent` (NeoForge) を介して、モジュラーなコマンドツリー（例: `/spawnsurvivors mission <type>`, `/spawnsurvivors phase <number>`）を登録する。
- **権限レベルと環境分離**:
  - コマンド実行時の権限チェック（`source.hasPermission(2)` などOPレベル権限）を徹底し、一般プレイヤーがマルチプレイでデバッグコマンドを実行できないように防護ガードを設置する。

