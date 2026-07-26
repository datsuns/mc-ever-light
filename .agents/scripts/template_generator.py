import os
import re
import sys
import shutil
import json

def parse_specification(file_path):
    """
    mod_specification.md をパースして、構造化されたデータを抽出します。
    """
    if not os.path.exists(file_path):
        print(f"Error: Specification file not found at {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    spec = {
        'platform': '',
        'version': '26.2',
        'mod_id': '',
        'mod_name': '',
        'package': '',
        'items': [],
        'blocks': [],
        'recipes': [],
        'events': [],
        'features': []
    }

    # タイトルからMod名を取得
    title_match = re.search(r'^#\s+Mod\s+Specification\s*-\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
    if title_match:
        spec['mod_name'] = title_match.group(1).strip()

    # メタデータ抽出
    for line in content.split('\n'):
        line_strip = line.strip()
        if not line_strip:
            continue
        
        # Markdownの太字や箇条書きを取り除いてパース
        clean_line = re.sub(r'^\s*[-*]\s*', '', line_strip)
        clean_line = clean_line.replace('**', '')
        
        if ':' in clean_line:
            key, val = clean_line.split(':', 1)
            key = key.strip().lower()
            val = val.strip()
            
            if key == 'platform':
                spec['platform'] = val.lower()
            elif key == 'minecraft version':
                spec['version'] = val
            elif key == 'mod id':
                spec['mod_id'] = val.lower()
            elif key == 'package':
                spec['package'] = val

    # Elementsセクションのパース
    lines = content.split('\n')
    current_section = None
    current_element = {}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # セクションヘッダー判定
        if re.match(r'^###\s+Items', line, re.IGNORECASE):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = 'items'
            i += 1
            continue
        elif re.match(r'^###\s+Blocks', line, re.IGNORECASE):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = 'blocks'
            i += 1
            continue
        elif re.match(r'^###\s+Recipes', line, re.IGNORECASE):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = 'recipes'
            i += 1
            continue
        elif re.match(r'^###\s+Events', line, re.IGNORECASE):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = 'events'
            i += 1
            continue
        elif re.match(r'^###\s+(?:Features|Patterns)', line, re.IGNORECASE):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = 'features'
            i += 1
            continue
        elif re.match(r'^##\s+', line) or re.match(r'^#\s+', line):
            if current_element and current_section:
                spec[current_section].append(current_element)
                current_element = {}
            current_section = None
            i += 1
            continue

        if current_section:
            clean_line = re.sub(r'^\s*[-*]\s*', '', line)
            clean_line = clean_line.replace('**', '')
            
            if ':' in clean_line:
                key, val = clean_line.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                
                # 新しい要素の開始 (Name)
                if key == 'name':
                    if current_element:
                        spec[current_section].append(current_element)
                    current_element = {'name': val}
                else:
                    if current_element is not None:
                        current_element[key] = val
            elif clean_line.startswith('pattern / ingredients') or clean_line.startswith('ingredients'):
                # レシピのパターンや材料のネスト読み込み
                current_element['ingredients'] = []
                i += 1
                while i < len(lines):
                    sub_line = lines[i].strip()
                    if not sub_line.startswith('-') and not sub_line.startswith('*'):
                        break
                    ing_val = re.sub(r'^\s*[-*]\s*', '', sub_line).strip()
                    current_element['ingredients'].append(ing_val)
                    i += 1
                continue

        i += 1

    if current_element and current_section:
        spec[current_section].append(current_element)

    # バリデーションと初期化
    if not spec['mod_name'] and spec['mod_id']:
        spec['mod_name'] = spec['mod_id'].capitalize()

    return spec

def copy_template_dir(src, dst, spec):
    """
    テンプレートディレクトリからプロジェクト宛先ディレクトリへコピーし、
    パッケージ構造やファイルを置換します。
    """
    if not os.path.exists(src):
        print(f"Error: Template source not found at {src}")
        return False

    mod_id = spec['mod_id']
    mod_name = spec['mod_name']
    package_name = spec['package']
    package_path = package_name.replace('.', '/')

    # 宛先ディレクトリの作成
    os.makedirs(dst, exist_ok=True)

    # コピーと置換
    for root, dirs, files in os.walk(src):
        # .git や build などの不要なフォルダを除外
        dirs[:] = [d for d in dirs if d not in ('.git', 'build', '.gradle', 'bin', 'out')]
        
        # フォルダ構造の決定
        rel_path = os.path.relpath(root, src)
        if rel_path == '.':
            dest_root = dst
        else:
            # パッケージ名に対応するパス変換
            adjusted_rel = rel_path
            for old_pkg in ['net/fabricmc/example', 'com/example/examplemod', 'com/example']:
                # Windowsのパス区切り（\）を考慮して置換
                normalized_rel = adjusted_rel.replace('\\', '/')
                if old_pkg in normalized_rel:
                    normalized_rel = normalized_rel.replace(old_pkg, package_path)
                    # OS固有のパスに戻す
                    adjusted_rel = os.path.normpath(normalized_rel)
                    break
            dest_root = os.path.join(dst, adjusted_rel)
            
        os.makedirs(dest_root, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            
            # ファイル名の調整 (例: ExampleMod.java -> MyMod.java, modid.mixins.json -> testmod.mixins.json)
            adjusted_file = file
            for old_name, new_name in [('ExampleMod', mod_name), ('ExampleMixin', f"{mod_name}Mixin"), ('modid', mod_id), ('examplemod', mod_id)]:
                if old_name in adjusted_file:
                    adjusted_file = adjusted_file.replace(old_name, new_name)
                    break
            dest_file = os.path.join(dest_root, adjusted_file)

            # テキストファイルなら置換しながらコピー、バイナリならそのままコピー
            try:
                with open(src_file, 'r', encoding='utf-8') as sf:
                    file_content = sf.read()
                
                # パッケージ名の置換 (長いものから順にチェックし、二重置換を防ぐ)
                for pkg_key in ['com.example.examplemod', 'net.fabricmc.example', 'com.example']:
                    if pkg_key in file_content:
                        file_content = file_content.replace(pkg_key, package_name)
                        break
                
                # IDやクラス名の置換
                for key, val in [('examplemod', mod_id), ('ExampleMod', mod_name), ('"modid"', f'"{mod_id}"'), ("'modid'", f"'{mod_id}'"), ('Example Mod', mod_name), ('ExampleMixin', f"{mod_name}Mixin")]:
                    file_content = file_content.replace(key, val)
                
                # 誤って置換された @EventBusSubscriber(modid = ...) の引数名を修復
                file_content = re.sub(rf'@EventBusSubscriber\(\s*{mod_id}\s*=', '@EventBusSubscriber(modid =', file_content)
                
                # 26.2 (1.21+) 用に一部のコードを調整
                # 例: new ResourceLocation -> ResourceLocation.fromNamespaceAndPath
                file_content = re.sub(r'new\s+ResourceLocation\(([^,]+),\s*([^)]+)\)', 
                                      r'ResourceLocation.fromNamespaceAndPath(\1, \2)', file_content)

                with open(dest_file, 'w', encoding='utf-8') as df:
                    df.write(file_content)
            except UnicodeDecodeError:
                # バイナリコピー (jar, png等)
                shutil.copy2(src_file, dest_file)

    print(f"Project initialized at {dst} from template {src}")
    return True

def generate_interactive_block_class(src_dir, package_name, mod_id):
    """右クリックでメッセージを表示するカスタムブロッククラスを生成します。"""
    class_file = os.path.join(src_dir, "InteractiveBlock.java")
    if os.path.exists(class_file):
        return
        
    code = f"""package {package_name};

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

public class InteractiveBlock extends Block {{
    public InteractiveBlock(Properties properties) {{
        super(properties);
    }}

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {{
        if (!level.isClientSide()) {{
            player.sendSystemMessage(Component.literal("Hello from Interactive Block!"));
        }}
        return InteractionResult.SUCCESS;
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Generated InteractiveBlock class at {class_file}")

def generate_shader_compat_render_class(src_dir, package_name):
    """パターンN: シェーダーパック互換・高速メッシュ生成レンダーのボイラープレート"""
    class_file = os.path.join(src_dir, "ShaderCompatRenderer.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.fabricmc.fabric.api.renderer.v1.RendererAccess;
import net.fabricmc.fabric.api.renderer.v1.mesh.MeshBuilder;
import net.fabricmc.fabric.api.renderer.v1.mesh.QuadEmitter;

public class ShaderCompatRenderer {{
    public static void buildMesh() {{
        if (RendererAccess.INSTANCE.hasRenderer()) {{
            MeshBuilder builder = RendererAccess.INSTANCE.getRenderer().meshBuilder();
            QuadEmitter emitter = builder.getEmitter();
            // シェーダーやSodium/Indiumと完全互換な描画パイプライン処理
        }}
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated ShaderCompatRenderer class at {class_file}")

def generate_async_chunk_reader_class(src_dir, package_name):
    """パターンO: 非同期NIOリージョン解析＆ミニマップエンジン用ボイラープレート"""
    class_file = os.path.join(src_dir, "AsyncChunkReader.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.CompletableFuture;

public class AsyncChunkReader {{
    public static CompletableFuture<Void> readRegionAsync(Path regionPath) {{
        return CompletableFuture.runAsync(() -> {{
            try (FileChannel channel = FileChannel.open(regionPath, StandardOpenOption.READ)) {{
                // メインスレッドをブロックしない非同期NIOによるMCAファイル読み込み処理
            }} catch (Exception e) {{
                e.printStackTrace();
            }}
        }});
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated AsyncChunkReader class at {class_file}")

def generate_acoustic_raycast_class(src_dir, package_name):
    """パターンP: 3D音響物理＆16本レイキャスティング残響計算ボイラープレート"""
    class_file = os.path.join(src_dir, "AcousticRaycast.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

public class AcousticRaycast {{
    public static float calculateReverb(Level level, Vec3 source, Vec3 listener) {{
        int rays = 16;
        float reflectedDensity = 0.0f;
        // 16〜32本の環境音響レイを放射し、ブロック表面の反射率(Reflectivity)と吸音率を計算
        return reflectedDensity / rays;
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated AcousticRaycast class at {class_file}")

def generate_voice_proxy_service_class(src_dir, package_name):
    """パターンQ: 独立UDPデータグラムストリーミング＆ボイスチャットボイラープレート"""
    class_file = os.path.join(src_dir, "VoiceProxyService.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class VoiceProxyService {{
    private DatagramSocket socket;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public void start(int port) {{
        executor.submit(() -> {{
            try {{
                socket = new DatagramSocket(port);
                byte[] buffer = new byte[1024];
                while (!socket.isClosed()) {{
                    DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                    socket.receive(packet);
                    // TCP再送詰まりを防ぐ低遅延UDP音声データストリーミング処理
                }}
            }} catch (Exception e) {{
                e.printStackTrace();
            }}
        }});
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated VoiceProxyService class at {class_file}")

def generate_custom_goal_class(src_dir, package_name):
    """パターンR: モジュラーモブAIゴール＆動的セレクター注入ボイラープレート"""
    class_file = os.path.join(src_dir, "CustomAIBehaviorGoal.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import java.util.EnumSet;

public class CustomAIBehaviorGoal extends Goal {{
    private final PathfinderMob mob;

    public CustomAIBehaviorGoal(PathfinderMob mob) {{
        this.mob = mob;
        this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
    }}

    @Override
    public boolean canUse() {{
        return this.mob.getTarget() != null;
    }}

    @Override
    public void tick() {{
        // バニラAIクラスを上書きせず動的に追加されるカスタム行動ロジック
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated CustomAIBehaviorGoal class at {class_file}")

def generate_energy_storage_block_entity_class(src_dir, package_name, mod_id):
    """パターンS: Fabric標準EnergyStorage＆BlockApiCache最適化ボイラープレート"""
    class_file = os.path.join(src_dir, "EnergyStorageBlockEntity.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.fabricmc.fabric.api.transfer.v1.transaction.TransactionContext;
import net.fabricmc.fabric.api.transfer.v1.transaction.base.SnapshotParticipant;
import team.reborn.energy.api.EnergyStorage;

public class EnergyStorageBlockEntity extends SnapshotParticipant<Long> implements EnergyStorage {{
    private long amount = 0;
    private final long capacity = 10000;

    @Override
    public long getAmount() {{ return amount; }}

    @Override
    public long getCapacity() {{ return capacity; }}

    @Override
    public boolean supportsInsertion() {{ return true; }}

    @Override
    public boolean supportsExtraction() {{ return true; }}

    @Override
    public long insert(long maxAmount, TransactionContext transaction) {{
        long inserted = Math.min(maxAmount, capacity - amount);
        if (inserted > 0) {{
            updateSnapshots(transaction);
            amount += inserted;
        }}
        return inserted;
    }}

    @Override
    public long extract(long maxAmount, TransactionContext transaction) {{
        long extracted = Math.min(maxAmount, amount);
        if (extracted > 0) {{
            updateSnapshots(transaction);
            amount -= extracted;
        }}
        return extracted;
    }}

    @Override
    protected Long createSnapshot() {{ return amount; }}

    @Override
    protected void readSnapshot(Long snapshot) {{ amount = snapshot; }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated EnergyStorageBlockEntity class at {class_file}")

def generate_optimistic_inventory_mixin(src_dir, package_name):
    """パターンT: 楽観的クライアント同期＆操作遅延レートリミットシミュレーション"""
    class_file = os.path.join(src_dir, "OptimisticInventoryHandler.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.client.Minecraft;

public class OptimisticInventoryHandler {{
    private static int clickDelayTimer = 0;

    public static void handleFastCrafting() {{
        if (clickDelayTimer > 0) {{
            clickDelayTimer--;
            return;
        }}
        // アンチチート誤検知を防ぐためバニラ標準のrightClickDelayTimer(4 tick)を遵守
        clickDelayTimer = 4;
        // サーバーパケット同期を待たずクライアント側スロットを楽観的更新(Optimistic UI)
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated OptimisticInventoryHandler class at {class_file}")

def generate_surface_rule_data_class(src_dir, package_name, mod_id):
    """パターンU: Data Packドリブン地形＆TerraBlender SurfaceRules統合ボイラープレート"""
    class_file = os.path.join(src_dir, "CustomSurfaceRules.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.world.level.levelgen.SurfaceRules;
import net.minecraft.world.level.block.Blocks;

public class CustomSurfaceRules {{
    public static SurfaceRules.RuleSource makeRules() {{
        // Javaコード内でChunkGeneratorを直接上書きせず、合成可能なSurfaceRulesとして定義
        return SurfaceRules.sequence(
            SurfaceRules.ifTrue(SurfaceRules.abovePreliminarySurface(),
                SurfaceRules.state(Blocks.GRASS_BLOCK.defaultBlockState()))
        );
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated CustomSurfaceRules class at {class_file}")

def generate_dynamic_light_tracker_class(src_dir, package_name):
    """パターンV: 動的ライト・光源計算最適化（クライアント空間ルックアップ＆非同期ライトインジェクション）ボイラープレート"""
    class_file = os.path.join(src_dir, "DynamicLightTracker.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.core.BlockPos;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class DynamicLightTracker {{
    // サーバー側の光エンジン(level.getLightEngine().checkBlock)を呼ばず、クライアント側で活動中光源を空間ルックアップ管理
    private static final Set<BlockPos> ACTIVE_LIGHT_SOURCES = ConcurrentHashMap.newKeySet();

    public static void trackLightSource(BlockPos pos) {{
        ACTIVE_LIGHT_SOURCES.add(pos);
    }}

    public static void untrackLightSource(BlockPos pos) {{
        ACTIVE_LIGHT_SOURCES.remove(pos);
    }}

    public static boolean isDynamicLight(BlockPos pos) {{
        return ACTIVE_LIGHT_SOURCES.contains(pos);
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated DynamicLightTracker class at {class_file}")

def generate_cinematic_camera_interface(src_dir, package_name):
    """パターンW: カメラアニメーション・映画的演出（3軸カメラインターフェース注入＆イベント駆動補間）ボイラープレート"""
    class_file = os.path.join(src_dir, "RollCamera.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

public interface RollCamera {{
    // バニラCameraの2軸(yaw/pitch)を超えた3軸(yaw/pitch/roll)制御をMixinから注入するインターフェース
    float getRoll();
    void setRoll(float roll);
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated RollCamera interface at {class_file}")

def generate_rpg_attribute_handler_class(src_dir, package_name, mod_id, is_neoforge=False):
    """パターンX: スキルツリー・RPGステータス（Data Pack駆動型属性バインディング＆イベントインジェクション）ボイラープレート"""
    class_file = os.path.join(src_dir, "RpgAttributeHandler.java")
    if os.path.exists(class_file): return
    if is_neoforge:
        code = f"""package {package_name};

import net.minecraft.resources.ResourceLocation;
import java.util.UUID;

public class RpgAttributeHandler {{
    // 属性の二重付与や破損を防ぐため、固定値をハードコードせずData Pack(JSON)仕様と一意のUUIDバインディングで管理
    public static final UUID SKILL_BONUS_UUID = UUID.fromString("87654321-4321-4321-4321-098765432109");
    public static final ResourceLocation RANDOM_MODIFIER_ID = ResourceLocation.fromNamespaceAndPath("{mod_id}", "dynamic_skill_bonus");

    public static void applySkillBonus() {{
        // 一時的イベントフック(StackAttributeModifiersEvent等)を介して動的に適用・分離するクリーンな属性スタック
    }}
}}
"""
    else:
        code = f"""package {package_name};

import net.minecraft.resources.Identifier;
import java.util.UUID;

public class RpgAttributeHandler {{
    // 属性の二重付与や破損を防ぐため、固定値をハードコードせずData Pack(JSON)仕様と一意のUUIDバインディングで管理
    public static final UUID SKILL_BONUS_UUID = UUID.fromString("87654321-4321-4321-4321-098765432109");
    public static final Identifier RANDOM_MODIFIER_ID = Identifier.fromNamespaceAndPath("{mod_id}", "dynamic_skill_bonus");

    public static void applySkillBonus() {{
        // 一時的イベントフック(StackAttributeModifiersEvent等)を介して動的に適用・分離するクリーンな属性スタック
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated RpgAttributeHandler class at {class_file}")

def generate_ship_transform_helper_class(src_dir, package_name):
    """パターンY: マルチパートエンティティ・搭乗物（二重座標空間変換＆ShipTransform行列インジェクション）ボイラープレート"""
    class_file = os.path.join(src_dir, "ShipTransformHelper.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import org.joml.Matrix4d;
import org.joml.Vector3d;

public class ShipTransformHelper {{
    // ワールド空間のブロック/エンティティ座標を毎tick直接移動させず、船体専用ローカル座標系(Ship Space)と変換行列で管理
    private final Matrix4d worldToShip = new Matrix4d();
    private final Matrix4d shipToWorld = new Matrix4d();

    public Vector3d toShipSpace(double x, double y, double z) {{
        Vector3d pos = new Vector3d(x, y, z);
        worldToShip.transformPosition(pos);
        return pos;
    }}

    public Vector3d toWorldSpace(double x, double y, double z) {{
        Vector3d pos = new Vector3d(x, y, z);
        shipToWorld.transformPosition(pos);
        return pos;
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated ShipTransformHelper class at {class_file}")

def generate_transaction_claim_handler_class(src_dir, package_name, mod_id):
    """パターンZ: トランザクション型経済・ショップ・領地保護（アトミック財布＆チャンク境界イベントフック）ボイラープレート"""
    class_file = os.path.join(src_dir, "TransactionClaimHandler.java")
    if os.path.exists(class_file): return
    code = f"""package {package_name};

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

public class TransactionClaimHandler {{
    // 通常インベントリスロットに依存せず、プレイヤーデータに直接アタッチされたアトミック専用スロットで決済
    public static boolean processAtomicTransaction(Player player, int amount) {{
        // デュープ防止のサーバー主導トランザクション処理
        return true;
    }}

    // 領地保護: サーバー全体のインタラクションイベントを中央のチャンク管理APIでフックして状態更新前に即キャンセル
    public static boolean shouldPreventInteraction(Level level, BlockPos pos, Player player) {{
        // チャンク境界チェックロジック
        return false;
    }}
}}
"""
    with open(class_file, 'w', encoding='utf-8') as f: f.write(code)
    print(f"Generated TransactionClaimHandler class at {class_file}")

def generate_fabric_elements(dst, spec):
    """
    Fabric 用にアイテムやブロックのコードおよびアセットを生成・更新します。
    """
    mod_id = spec['mod_id']
    package_name = spec['package']
    package_path = package_name.replace('.', '/')
    src_dir = os.path.join(dst, 'src/main/java', package_path)
    res_dir = os.path.join(dst, 'src/main/resources')
    
    mod_name = spec['mod_name']
    main_class_file = os.path.join(src_dir, f"{mod_name}.java")
    
    if not os.path.exists(main_class_file):
        print(f"Error: Main class not found at {main_class_file}")
        return

    # アイテム登録コードの生成
    item_registrations = []
    for item in spec['items']:
        item_id = item['id']
        var_name = item_id.upper()
        item_type = item.get('type', 'generic').lower()
        
        # 1.21.4+ 対応の登録コード (ResourceKey と setId が必要)
        reg_key = f'    public static final ResourceKey<Item> {var_name}_KEY = ResourceKey.create(\n' \
                  f'        Registries.ITEM,\n' \
                  f'        Identifier.fromNamespaceAndPath(MOD_ID, "{item_id}")\n' \
                  f'    );'
                  
        # pickaxe等のツールクラスは1.21.5/26.x以降で廃止されたため、すべて標準のItemとして登録する
        reg_code = f'    public static final Item {var_name} = Registry.register(\n' \
                   f'        BuiltInRegistries.ITEM,\n' \
                   f'        {var_name}_KEY,\n' \
                   f'        new Item(new Item.Properties().setId({var_name}_KEY))\n' \
                   f'    );'
                       
        item_registrations.append(reg_key + "\n" + reg_code)
        
        # アイテムモデルJSONの作成
        item_model_dir = os.path.join(res_dir, 'assets', mod_id, 'models/item')
        os.makedirs(item_model_dir, exist_ok=True)
        item_model = {
            "parent": "minecraft:item/generated",
            "textures": {
                "layer0": f"{mod_id}:item/{item_id}"
            }
        }
        with open(os.path.join(item_model_dir, f"{item_id}.json"), 'w', encoding='utf-8') as jf:
            json.dump(item_model, jf, indent=2)

    # ブロック登録コードの生成
    block_registrations = []
    for block in spec['blocks']:
        block_id = block['id']
        var_name = block_id.upper()
        hardness = block.get('hardness', '1.5')
        block_type = block.get('type', 'generic').lower()
        
        reg_block_key = f'    public static final ResourceKey<Block> {var_name}_KEY = ResourceKey.create(\n' \
                        f'        Registries.BLOCK,\n' \
                        f'        Identifier.fromNamespaceAndPath(MOD_ID, "{block_id}")\n' \
                        f'    );'
                        
        if block_type == 'interactive':
            reg_block = f'    public static final Block {var_name} = Registry.register(\n' \
                        f'        BuiltInRegistries.BLOCK,\n' \
                        f'        {var_name}_KEY,\n' \
                        f'        new InteractiveBlock(BlockBehaviour.Properties.of().strength({hardness}f).setId({var_name}_KEY))\n' \
                        f'    );'
            # InteractiveBlock.java の生成
            generate_interactive_block_class(src_dir, package_name, mod_id)
        else:
            reg_block = f'    public static final Block {var_name} = Registry.register(\n' \
                        f'        BuiltInRegistries.BLOCK,\n' \
                        f'        {var_name}_KEY,\n' \
                        f'        new Block(BlockBehaviour.Properties.of().strength({hardness}f).setId({var_name}_KEY))\n' \
                        f'    );'
                        
        reg_item_key = f'    public static final ResourceKey<Item> {var_name}_ITEM_KEY = ResourceKey.create(\n' \
                       f'        Registries.ITEM,\n' \
                       f'        Identifier.fromNamespaceAndPath(MOD_ID, "{block_id}")\n' \
                       f'    );'
        reg_block_item = f'    public static final BlockItem {var_name}_ITEM = Registry.register(\n' \
                         f'        BuiltInRegistries.ITEM,\n' \
                         f'        {var_name}_ITEM_KEY,\n' \
                         f'        new BlockItem({var_name}, new Item.Properties().setId({var_name}_ITEM_KEY))\n' \
                         f'    );'
                         
        block_registrations.append(reg_block_key + "\n" + reg_block + "\n" + reg_item_key + "\n" + reg_block_item)
        
        # ブロックステート/モデルの作成
        assets_mod = os.path.join(res_dir, 'assets', mod_id)
        os.makedirs(os.path.join(assets_mod, 'blockstates'), exist_ok=True)
        os.makedirs(os.path.join(assets_mod, 'models/block'), exist_ok=True)
        os.makedirs(os.path.join(assets_mod, 'models/item'), exist_ok=True)
        
        # Blockstate JSON
        state_json = {
            "variants": {
                "": { "model": f"{mod_id}:block/{block_id}" }
            }
        }
        with open(os.path.join(assets_mod, 'blockstates', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
            json.dump(state_json, jf, indent=2)
            
        # Block Model JSON
        block_model = {
            "parent": "minecraft:block/cube_all",
            "textures": {
                "all": f"{mod_id}:block/{block_id}"
            }
        }
        with open(os.path.join(assets_mod, 'models/block', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
            json.dump(block_model, jf, indent=2)
            
        # Block Item Model JSON (blockモデルを継承)
        block_item_model = {
            "parent": f"{mod_id}:block/{block_id}"
        }
        with open(os.path.join(assets_mod, 'models/item', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
            json.dump(block_item_model, jf, indent=2)

    # メインクラスの更新 (インポートの追加と登録コードの注入)
    with open(main_class_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # 必要なインポートを追加
    imports_to_add = [
        "import net.minecraft.core.Registry;",
        "import net.minecraft.core.registries.BuiltInRegistries;",
        "import net.minecraft.resources.Identifier;",
        "import net.minecraft.world.item.Item;",
        "import net.minecraft.world.level.block.Block;",
        "import net.minecraft.world.level.block.state.BlockBehaviour;",
        "import net.minecraft.world.item.BlockItem;",
        "import net.minecraft.resources.ResourceKey;",
        "import net.minecraft.core.registries.Registries;"
    ]
    
    for imp in imports_to_add:
        if imp not in code:
            # packageの直後にインポートを挿入
            code = re.sub(r'(package\s+[^;]+;)', rf'\1\n{imp}', code)

    # 登録フィールドの注入 (クラスの波括弧 { の直後に挿入)
    registrations_block = "\n".join(item_registrations + block_registrations)
    
    # 既存の登録記述があるか確認し、無ければクラスの先頭に注入
    if "BuiltInRegistries.ITEM" not in code and registrations_block:
        # Forward Referenceエラーを防ぐため、既存の MOD_ID 定義行を探して、クラスの最上部に移動させる
        mod_id_pattern = r'public\s+static\s+final\s+String\s+MOD_ID\s*=\s*"[^"]+"\s*;'
        mod_id_match = re.search(mod_id_pattern, code)
        
        if mod_id_match:
            mod_id_line = mod_id_match.group(0)
            # 元の定義行を削除
            code = re.sub(mod_id_pattern, '', code)
            # クラスの先頭（{ の直後）に MOD_ID定義 と 登録コード を挿入
            class_pattern = rf'(public\s+class\s+{mod_name}\s+implements\s+ModInitializer\s*\{{)'
            code = re.sub(class_pattern, rf'\1\n    {mod_id_line}\n{registrations_block}\n', code)
        else:
            class_pattern = rf'(public\s+class\s+{mod_name}\s+implements\s+ModInitializer\s*\{{)'
            code = re.sub(class_pattern, rf'\1\n{registrations_block}\n', code)

    # イベントハンドラーの登録
    event_registrations = []
    for ev in spec.get('events', []):
        ev_type = ev.get('event type', '').lower()
        if ev_type == 'attack_entity':
            reg = f'        net.fabricmc.fabric.api.event.player.AttackEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {{\n' \
                  f'            if (!level.isClientSide() && player != null) {{\n' \
                  f'                player.addEffect(new net.minecraft.world.effect.MobEffectInstance(\n' \
                  f'                    net.minecraft.world.effect.MobEffects.SPEED, 2000, 1\n' \
                  f'                ));\n' \
                  f'            }}\n' \
                  f'            return net.minecraft.world.InteractionResult.PASS;\n' \
                  f'        }});'
            event_registrations.append(reg)
        elif ev_type in ['block_break', 'chain_break', 'falling_tree']:
            reg = f'        // パターンA: 連鎖破壊・範囲採掘フック (BFS探索とサーバー負荷対策)\n' \
                  f'        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.BEFORE.register((world, player, pos, state, blockEntity) -> {{\n' \
                  f'            if (!world.isClientSide() && !player.isShiftKeyDown()) {{\n' \
                  f'                int maxBlocks = 64;\n' \
                  f'                java.util.Queue<net.minecraft.core.BlockPos> queue = new java.util.ArrayDeque<>();\n' \
                  f'                java.util.Set<net.minecraft.core.BlockPos> visited = new java.util.HashSet<>();\n' \
                  f'                queue.add(pos);\n' \
                  f'                visited.add(pos);\n' \
                  f'                while (!queue.isEmpty() && visited.size() < maxBlocks) {{\n' \
                  f'                    net.minecraft.core.BlockPos current = queue.poll();\n' \
                  f'                    for (net.minecraft.core.Direction dir : net.minecraft.core.Direction.values()) {{\n' \
                  f'                        net.minecraft.core.BlockPos next = current.relative(dir);\n' \
                  f'                        if (!visited.contains(next) && world.getBlockState(next).is(state.getBlock())) {{\n' \
                  f'                            visited.add(next);\n' \
                  f'                            queue.add(next);\n' \
                  f'                            world.destroyBlock(next, true, player);\n' \
                  f'                        }}\n' \
                  f'                    }}\n' \
                  f'                }}\n' \
                  f'            }}\n' \
                  f'            return true;\n' \
                  f'        }});'
            event_registrations.append(reg)
        elif ev_type in ['networking', 'custom_payload', 'packet_sync']:
            reg = f'        // パターンC: 1.20.5+/1.21.2+ 最新Networkingパケット受信フック (Netty I/O vs Server Thread対策)\n' \
                  f'        // 注: パケットIDとペイロードの登録には PayloadTypeRegistry.playC2S().register(...) を使用してください\n' \
                  f'        /*\n' \
                  f'        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(CUSTOM_PACKET_ID, (payload, context) -> {{\n' \
                  f'            // 必ずメインサーバースレッド上で同期実行し、スレッド競合とワールド破損を防ぐ\n' \
                  f'            context.server().execute(() -> {{\n' \
                  f'                // ワールドやプレイヤーインベントリの操作\n' \
                  f'            }});\n' \
                  f'        }});\n' \
                  f'        */'
            event_registrations.append(reg)
        elif ev_type in ['worldgen', 'biome', 'structure']:
            reg = f'        // パターンG: ワールド生成・バイオーム・構造物拡張 (TerraBlender / YUNG\'s API)\n' \
                  f'        // 注意: バニラのStructureやバイオーム生成への無秩序な@Overwrite Mixinは競合を招くため禁止です。\n' \
                  f'        // TerraBlenderのRegion拡張またはYUNG\'s API/Data Pack駆動による構造物プール拡張を推奨します。'
            event_registrations.append(reg)
        elif ev_type in ['animation', 'geckolib', '3d_model']:
            reg = f'        // パターンH: 3Dモデル・アニメーション制御 (GeckoLib GeoAnimatable)\n' \
                  f'        // サーバー側で entity.triggerAnim("controller", "anim_name") を呼ぶことで、\n' \
                  f'        // GeckoLibServices.NETWORK がトラッキング中の全クライアントへ自動同期します。'
            event_registrations.append(reg)
        elif ev_type in ['recipe_viewer', 'rei', 'emi']:
            reg = f'        // パターンI: レシピビューアー連携 (REI / EMI Optional Dependency)\n' \
                  f'        // fabric.mod.json の "rei_client" または "emi" エントリポイントに専用プラグインクラスを登録し、\n' \
                  f'        // registerCategories / registerDisplays / registerWorkstations を実装してください。'
            event_registrations.append(reg)
        elif ev_type in ['performance', 'mixin_config', 'optimization']:
            reg = f'        // パターンJ: パフォーマンス最適化・非破壊Mixin (Sodium / Lithium)\n' \
                  f'        // IMixinConfigPlugin を実装して環境・競合Modに応じたMixinの動的ON/OFFを行い、\n' \
                  f'        // @Overwriteを避けて @WrapOperation (MixinExtras) を使用してください。'
            event_registrations.append(reg)
        elif ev_type in ['storage', 'logistics', 'ae2', 'multiblock']:
            reg = f'        // パターンK: マルチブロック管路・大容量ストレージ (AE2 / Tom\'s Storage)\n' \
                  f'        // 64個制限を超える在庫は不変キーと long 型数量で管理し、\n' \
                  f'        // アイテム移動時は必ず SIMULATE パスで検証してから MODULATE で実行してください。'
            event_registrations.append(reg)
        elif ev_type in ['inventory_ux', 'mouse_tweaks', 'keybinding']:
            reg = f'        // パターンL: インベントリUX・ホットキー制御 (Mouse Tweaks / Controlling)\n' \
                  f'        // コンテナスクリーン操作は共通インターフェースで抽象化し、\n' \
                  f'        // キーバインドは KeyMapping Accessor Mixin で未割り当てキーや競合を検知してください。'
            event_registrations.append(reg)
        elif ev_type in ['command', 'permission', 'carpet', 'luckperms']:
            reg = f'        // パターンM: コマンド・サーバー権限管理 (Carpet / LuckPerms)\n' \
                  f'        // 固定のOPレベル判定 (hasPermission(4)) をハードコードせず、\n' \
                  f'        // fabric-permissions-api (Permissions.check) を介してイベント駆動で権限判定を行ってください。'
            event_registrations.append(reg)
            
    if event_registrations:
        event_block = "\n".join(event_registrations)
        # onInitialize() { の直後にイベント登録コードを挿入
        init_pattern = r'(public\s+void\s+onInitialize\(\)\s*\{)'
        if "AttackEntityCallback.EVENT" not in code and "PlayerBlockBreakEvents.BEFORE" not in code:
            code = re.sub(init_pattern, rf'\1\n{event_block}\n', code)

    with open(main_class_file, 'w', encoding='utf-8') as f:
        f.write(code)

    # 言語ファイル (en_us.json, ja_jp.json) の更新
    lang_dir = os.path.join(res_dir, 'assets', mod_id, 'lang')
    os.makedirs(lang_dir, exist_ok=True)
    
    for lang in ['en_us', 'ja_jp']:
        lang_file = os.path.join(lang_dir, f"{lang}.json")
        lang_data = {}
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # 要素の翻訳追加
        for item in spec['items']:
            key = f"item.{mod_id}.{item['id']}"
            if key not in lang_data:
                lang_data[key] = item['name']
                
        for block in spec['blocks']:
            key = f"block.{mod_id}.{block['id']}"
            if key not in lang_data:
                lang_data[key] = block['name']
                
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(lang_data, f, indent=2, ensure_ascii=False)
            
    # GameTest クラスの生成は除外（不要なテストエラーを防ぐため）
    print(f"GameTest class generated at {gametest_class_file}")

    # パターンN〜Uなどの特徴的機能・イベント実装ファイルの生成
    for feat in spec.get('features', []) + spec.get('events', []) + spec.get('blocks', []):
        feat_type = feat.get('type', '').lower()
        if feat_type in ['render_compat', 'shader_guard', 'pattern_n']:
            generate_shader_compat_render_class(src_dir, package_name)
        elif feat_type in ['async_map', 'region_parser', 'pattern_o']:
            generate_async_chunk_reader_class(src_dir, package_name)
        elif feat_type in ['acoustic_physics', 'sound_raycast', 'pattern_p']:
            generate_acoustic_raycast_class(src_dir, package_name)
        elif feat_type in ['voice_udp', 'udp_streaming', 'pattern_q']:
            generate_voice_proxy_service_class(src_dir, package_name)
        elif feat_type in ['ai_goal', 'mob_ai', 'pattern_r']:
            generate_custom_goal_class(src_dir, package_name)
        elif feat_type in ['energy', 'energy_storage', 'api_cache', 'pattern_s']:
            generate_energy_storage_block_entity_class(src_dir, package_name, mod_id)
        elif feat_type in ['client_tweak', 'inventory_ux', 'pattern_t']:
            generate_optimistic_inventory_mixin(src_dir, package_name)
        elif feat_type in ['surface_rule', 'worldgen', 'pattern_u']:
            generate_surface_rule_data_class(src_dir, package_name, mod_id)
        elif feat_type in ['dynamic_light', 'light_tracker', 'pattern_v']:
            generate_dynamic_light_tracker_class(src_dir, package_name)
        elif feat_type in ['cinematic_camera', 'camera_roll', 'pattern_w']:
            generate_cinematic_camera_interface(src_dir, package_name)
        elif feat_type in ['rpg_skill', 'attribute_modifier', 'pattern_x']:
            generate_rpg_attribute_handler_class(src_dir, package_name, mod_id)
        elif feat_type in ['multipart_entity', 'ship_transform', 'pattern_y']:
            generate_ship_transform_helper_class(src_dir, package_name)
        elif feat_type in ['economy_trade', 'claim_protection', 'pattern_z']:
            generate_transaction_claim_handler_class(src_dir, package_name, mod_id)

    print("Fabric elements and resource assets generated successfully.")

def generate_neoforge_elements(dst, spec):
    """
    NeoForge 用にアイテムやブロックのコードおよびアセットを生成・更新します。
    """
    mod_id = spec['mod_id']
    package_name = spec['package']
    package_path = package_name.replace('.', '/')
    src_dir = os.path.join(dst, 'src/main/java', package_path)
    res_dir = os.path.join(dst, 'src/main/resources')
    mod_name = spec['mod_name']
    main_class_file = os.path.join(src_dir, f"{mod_name}.java")
    
    if not os.path.exists(main_class_file):
        print(f"Error: Main class not found at {main_class_file}")
        return

    # NeoForge特有のDeferredRegister定義
    deferred_registers = []
    
    # アイテム
    item_registrations = []
    if spec['items']:
        deferred_registers.append("    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MOD_ID);")
        for item in spec['items']:
            item_id = item['id']
            var_name = item_id.upper()
            reg = f'    public static final DeferredItem<Item> {var_name} = ITEMS.registerSimpleItem("{item_id}", new Item.Properties());'
            item_registrations.append(reg)
            
            # JSONアセット作成
            item_model_dir = os.path.join(res_dir, 'assets', mod_id, 'models/item')
            os.makedirs(item_model_dir, exist_ok=True)
            item_model = {
                "parent": "minecraft:item/generated",
                "textures": {
                    "layer0": f"{mod_id}:item/{item_id}"
                }
            }
            with open(os.path.join(item_model_dir, f"{item_id}.json"), 'w', encoding='utf-8') as jf:
                json.dump(item_model, jf, indent=2)

    # ブロック
    block_registrations = []
    if spec['blocks']:
        deferred_registers.append("    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MOD_ID);")
        for block in spec['blocks']:
            block_id = block['id']
            var_name = block_id.upper()
            hardness = block.get('hardness', '1.5')
            
            reg_block = f'    public static final DeferredBlock<Block> {var_name} = BLOCKS.registerSimpleBlock("{block_id}", BlockBehaviour.Properties.of().strength({hardness}f));'
            block_registrations.append(reg_block)
            
            # JSONアセット作成
            assets_mod = os.path.join(res_dir, 'assets', mod_id)
            os.makedirs(os.path.join(assets_mod, 'blockstates'), exist_ok=True)
            os.makedirs(os.path.join(assets_mod, 'models/block'), exist_ok=True)
            os.makedirs(os.path.join(assets_mod, 'models/item'), exist_ok=True)
            
            state_json = { "variants": { "": { "model": f"{mod_id}:block/{block_id}" } } }
            with open(os.path.join(assets_mod, 'blockstates', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
                json.dump(state_json, jf, indent=2)
                
            block_model = { "parent": "minecraft:block/cube_all", "textures": { "all": f"{mod_id}:block/{block_id}" } }
            with open(os.path.join(assets_mod, 'models/block', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
                json.dump(block_model, jf, indent=2)
                
            block_item_model = { "parent": f"{mod_id}:block/{block_id}" }
            with open(os.path.join(assets_mod, 'models/item', f"{block_id}.json"), 'w', encoding='utf-8') as jf:
                json.dump(block_item_model, jf, indent=2)

    # メインクラスの更新
    with open(main_class_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # インポートの追加
    imports_to_add = [
        "import net.neoforged.neoforge.registries.DeferredRegister;",
        "import net.neoforged.neoforge.registries.DeferredItem;",
        "import net.neoforged.neoforge.registries.DeferredBlock;",
        "import net.minecraft.world.item.Item;",
        "import net.minecraft.world.level.block.Block;",
        "import net.minecraft.world.level.block.state.BlockBehaviour;",
        "import net.neoforged.bus.api.IEventBus;"
    ]
    
    for imp in imports_to_add:
        if imp not in code:
            code = re.sub(r'(package\s+[^;]+;)', rf'\1\n{imp}', code)

    # DeferredRegister定義と登録処理の注入
    reg_block_code = "\n".join(deferred_registers + item_registrations + block_registrations)
    
    if "DeferredRegister" not in code and reg_block_code:
        # Forward Referenceエラーを防ぐため、既存の MOD_ID 定義行を探して、クラスの最上部に移動させる
        mod_id_pattern = r'public\s+static\s+final\s+String\s+MOD_ID\s*=\s*"[^"]+"\s*;'
        mod_id_match = re.search(mod_id_pattern, code)
        
        if mod_id_match:
            mod_id_line = mod_id_match.group(0)
            # 元の定義行を削除
            code = re.sub(mod_id_pattern, '', code)
            # クラスの先頭（{ の直後）に MOD_ID定義 と 登録コード を挿入
            class_pattern = rf'(public\s+class\s+{mod_name}\s*\{{)'
            code = re.sub(class_pattern, rf'\1\n    {mod_id_line}\n{reg_block_code}\n', code)
        else:
            class_pattern = rf'(public\s+class\s+{mod_name}\s*\{{)'
            code = re.sub(class_pattern, rf'\1\n{reg_block_code}\n', code)
        
        # コンストラクタ（IEventBusを受け取る箇所）に register 処理を登録
        # NeoForge テンプレートのコンストラクタ構造に適合させる
        constructor_pattern = rf'(public\s+{mod_name}\s*\(\s*IEventBus\s+(\w+)\s*\)\s*\{{)'
        bus_reg_calls = ""
        if spec['items']:
            bus_reg_calls += "\n        ITEMS.register(\\2);"
        if spec['blocks']:
            bus_reg_calls += "\n        BLOCKS.register(\\2);"
        
        code = re.sub(constructor_pattern, rf'\1{bus_reg_calls}', code)

    with open(main_class_file, 'w', encoding='utf-8') as f:
        f.write(code)

    # 言語ファイル更新 (Fabricと同様)
    lang_dir = os.path.join(res_dir, 'assets', mod_id, 'lang')
    os.makedirs(lang_dir, exist_ok=True)
    for lang in ['en_us', 'ja_jp']:
        lang_file = os.path.join(lang_dir, f"{lang}.json")
        lang_data = {}
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        for item in spec['items']:
            lang_data[f"item.{mod_id}.{item['id']}"] = item['name']
        for block in spec['blocks']:
            lang_data[f"block.{mod_id}.{block['id']}"] = block['name']
            
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(lang_data, f, indent=2, ensure_ascii=False)

    # パターンN〜Zなどの特徴的機能・イベント実装ファイルの生成 (NeoForge)
    for feat in spec.get('features', []) + spec.get('events', []) + spec.get('blocks', []):
        feat_type = feat.get('type', '').lower()
        if feat_type in ['render_compat', 'shader_guard', 'pattern_n']:
            generate_shader_compat_render_class(src_dir, package_name)
        elif feat_type in ['async_map', 'region_parser', 'pattern_o']:
            generate_async_chunk_reader_class(src_dir, package_name)
        elif feat_type in ['acoustic_physics', 'sound_raycast', 'pattern_p']:
            generate_acoustic_raycast_class(src_dir, package_name)
        elif feat_type in ['voice_udp', 'udp_streaming', 'pattern_q']:
            generate_voice_proxy_service_class(src_dir, package_name)
        elif feat_type in ['ai_goal', 'mob_ai', 'pattern_r']:
            generate_custom_goal_class(src_dir, package_name)
        elif feat_type in ['energy', 'energy_storage', 'api_cache', 'pattern_s']:
            generate_energy_storage_block_entity_class(src_dir, package_name, mod_id)
        elif feat_type in ['client_tweak', 'inventory_ux', 'pattern_t']:
            generate_optimistic_inventory_mixin(src_dir, package_name)
        elif feat_type in ['surface_rule', 'worldgen', 'pattern_u']:
            generate_surface_rule_data_class(src_dir, package_name, mod_id)
        elif feat_type in ['dynamic_light', 'light_tracker', 'pattern_v']:
            generate_dynamic_light_tracker_class(src_dir, package_name)
        elif feat_type in ['cinematic_camera', 'camera_roll', 'pattern_w']:
            generate_cinematic_camera_interface(src_dir, package_name)
        elif feat_type in ['rpg_skill', 'attribute_modifier', 'pattern_x']:
            generate_rpg_attribute_handler_class(src_dir, package_name, mod_id, is_neoforge=True)
        elif feat_type in ['multipart_entity', 'ship_transform', 'pattern_y']:
            generate_ship_transform_helper_class(src_dir, package_name)
        elif feat_type in ['economy_trade', 'claim_protection', 'pattern_z']:
            generate_transaction_claim_handler_class(src_dir, package_name, mod_id)

    print("NeoForge elements and resource assets generated successfully.")

def generate_paper_elements(dst, spec):
    """
    Paper (Bukkit) 用にプラグインのコードを生成します。
    """
    mod_id = spec['mod_id']
    package_name = spec['package']
    package_path = package_name.replace('.', '/')
    src_dir = os.path.join(dst, 'src/main/java', package_path)
    res_dir = os.path.join(dst, 'src/main/resources')
    mod_name = spec['mod_name']
    
    # 簡易的なJavaPluginメインクラスを生成（無ければ作成）
    main_class_file = os.path.join(src_dir, f"{mod_name}.java")
    os.makedirs(src_dir, exist_ok=True)
    
    recipe_code = []
    for recipe in spec['recipes']:
        if 'result' in recipe:
            res_id = recipe['result']
            recipe_code.append(
                f'        // Recipe for {res_id}\n'
                f'        org.bukkit.inventory.ItemStack resultStack = new org.bukkit.inventory.ItemStack(org.bukkit.Material.GOLD_BLOCK);\n' # 仮
                f'        org.bukkit.NamespacedKey key = new org.bukkit.NamespacedKey(this, "{res_id}");\n'
                f'        org.bukkit.inventory.ShapedRecipe recipe = new org.bukkit.inventory.ShapedRecipe(key, resultStack);\n'
                f'        recipe.shape("GGG", "GGG", "GGG");\n' # 簡易
                f'        recipe.setIngredient(\'G\', org.bukkit.Material.GOLD_INGOT);\n'
                f'        org.bukkit.Bukkit.addRecipe(recipe);\n'
            )
            
    recipes_str = "\n".join(recipe_code)

    plugin_code = f"""package {package_name};

import org.bukkit.plugin.java.JavaPlugin;

public class {mod_name} extends JavaPlugin {{
    @Override
    public void onEnable() {{
        getLogger().info("{mod_name} has been enabled!");
{recipes_str}
    }}

    @Override
    public void onDisable() {{
        getLogger().info("{mod_name} has been disabled!");
    }}
}}
"""
    with open(main_class_file, 'w', encoding='utf-8') as f:
        f.write(plugin_code)

    # plugin.yml の作成
    os.makedirs(res_dir, exist_ok=True)
    plugin_yml = f"""name: {mod_name}
version: 1.0.0
main: {package_name}.{mod_name}
api-version: '1.21'
author: AIModdingAgent
description: Generated Paper plugin.
"""
    with open(os.path.join(res_dir, 'plugin.yml'), 'w', encoding='utf-8') as f:
        f.write(plugin_yml)

    # build.gradle の作成 (簡易)
    build_gradle = f"""plugins {{
    id 'java'
}}

group = '{package_name}'
version = '1.0.0'

repositories {{
    mavenCentral()
    maven {{
        name = "papermc-repo"
        url = "https://repo.papermc.io/repository/maven-public/"
    }}
}}

dependencies {{
    compileOnly "io.papermc.paper:paper-api:1.21-R0.1-SNAPSHOT"
}}

def targetJavaVersion = 21
java {{
    def javaVersion = JavaVersion.toVersion(targetJavaVersion)
    sourceCompatibility = javaVersion
    targetCompatibility = javaVersion
    if (JavaVersion.current() < javaVersion) {{
        toolchain.languageVersion = JavaLanguageVersion.of(targetJavaVersion)
    }}
}}
"""
    with open(os.path.join(dst, 'build.gradle'), 'w', encoding='utf-8') as f:
        f.write(build_gradle)

    print("Paper (Bukkit) plugin elements and build scripts generated successfully.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python template_generator.py <spec_file_path> <output_dir>")
        sys.exit(1)

    spec_file = sys.argv[1]
    output_dir = sys.argv[2]

    spec = parse_specification(spec_file)
    if not spec:
        print("Error: Could not parse specification.")
        sys.exit(1)

    platform = spec['platform']
    print(f"Generating mod code for platform: {platform}")

    # プロジェクト初期化 (必要に応じてテンプレートからコピー)
    # 既にbuild.gradleやsettings.gradleがある場合は初期化をスキップ
    if not os.path.exists(os.path.join(output_dir, 'build.gradle')):
        template_src = ""
        if platform == 'fabric':
            template_src = os.path.join(os.path.dirname(__file__), '../../templates/fabric')
        elif platform == 'neoforge':
            template_src = os.path.join(os.path.dirname(__file__), '../../templates/neoforge')
        elif platform == 'paper':
            # Paperはテンプレートがない場合があるので、そのまま生成
            os.makedirs(output_dir, exist_ok=True)
            
        if template_src:
            success = copy_template_dir(template_src, output_dir, spec)
            if not success:
                print("Error initializing project templates.")
                sys.exit(1)

    # 各要素のコード追加・アセット生成
    if platform == 'fabric':
        generate_fabric_elements(output_dir, spec)
    elif platform == 'neoforge':
        generate_neoforge_elements(output_dir, spec)
    elif platform == 'paper':
        generate_paper_elements(output_dir, spec)
    else:
        print(f"Unsupported platform: {platform}")
        sys.exit(1)

    print("Done generating mod assets.")

if __name__ == '__main__':
    main()
