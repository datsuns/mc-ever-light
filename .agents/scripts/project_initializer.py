import os
import sys
import argparse
import subprocess
import shutil

# 同一ディレクトリの template_generator からインポート
sys.path.append(os.path.dirname(__file__))
try:
    from template_generator import copy_template_dir
except ImportError:
    # フォールバック (インポートできない場合用)
    def copy_template_dir(src, dst, spec):
        print("Warning: template_generator.py not found in sys.path. Cannot initialize template files.")
        return False

def create_junction_or_link(target_path, link_path):
    """OSに応じたジャンクション(Windows)またはシンボリックリンク(Linux/macOS)を作成します。"""
    # 既存のファイルやリンクがあれば削除
    if os.path.exists(link_path) or os.path.islink(link_path):
        if os.path.isdir(link_path) and not os.path.islink(link_path):
            # Windowsのジャンクションはisdir判定されるがislinkはFalseを返すことがあるため、rmdirで削除
            try:
                os.rmdir(link_path)
            except Exception:
                shutil.rmtree(link_path)
        else:
            os.remove(link_path)

    # 親ディレクトリの作成
    os.makedirs(os.path.dirname(link_path), exist_ok=True)

    is_windows = sys.platform.startswith('win')
    
    if is_windows:
        # Windowsのディレクトリジャンクション作成 (管理者権限不要)
        # コマンド: mklink /J <リンク> <ターゲット>
        # パスをバックスラッシュに正規化
        target_norm = os.path.normpath(target_path)
        link_norm = os.path.normpath(link_path)
        cmd = f'cmd /c mklink /J "{link_norm}" "{target_norm}"'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Failed to create junction from {target_norm} to {link_norm}. Error: {result.stderr.decode('cp932', errors='ignore')}")
            return False
    else:
        # Linux / macOS のシンボリックリンク作成
        try:
            os.symlink(target_path, link_path)
        except Exception as e:
            print(f"Failed to create symlink from {target_path} to {link_path}. Error: {e}")
            return False
            
    print(f"Linked: {link_path} -> {target_path}")
    return True

def create_specification_template(target_dir, spec):
    """mod_specification.md のボイラープレートテンプレートを作成します。"""
    spec_path = os.path.join(target_dir, "mod_specification.md")
    if os.path.exists(spec_path):
        print(f"Specification file already exists at {spec_path}. Skipping.")
        return

    content = f"""# Mod Specification - {spec['mod_name']}

## Metadata
*   **Platform**: {spec['platform']}
*   **Minecraft Version**: 1.21.4
*   **Mod ID**: {spec['mod_id']}
*   **Package**: {spec['package']}

---

## Requirements / Features
このModの機能アイデアをここに記述してください。
AIエージェントがこの内容をパース、またはヒアリングを通じて詳細な登録コードを生成します。

### Items
*   **Name**: エメラルドソード
    - **ID**: emerald_sword
    - **Description**: 強力なエメラルド製の剣

### Blocks
*   **Name**: エメラルド鉱石ブロック
    - **ID**: emerald_ore_block
    - **Hardness**: 3.0
    - **Description**: 採掘可能なエメラルドの鉱石

### Recipes
*   **Result**: emerald_sword
    - **Pattern**:
      - " E "
      - " E "
      - " S "
    - **Ingredients**:
      - "E": minecraft:emerald
      - "S": minecraft:stick
"""
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created specification template at {spec_path}")

def main():
    parser = argparse.ArgumentParser(description="Initialize a new Minecraft Mod project linking to the mc-mod-skills engine.")
    parser.add_argument("target_dir", help="Directory where the new mod project will be created.")
    parser.add_argument("--link-only", action="store_true", help="Only link scripts, config, and skills folders without expanding project templates.")
    parser.add_argument("--platform", choices=["fabric", "neoforge", "paper"], help="Target modding platform.")
    parser.add_argument("--name", help="Mod name (e.g. MyMagicMod).")
    parser.add_argument("--id", help="Mod ID (e.g. mymagicmod).")
    parser.add_argument("--package", help="Java package (e.g. com.example.magic).")
    
    args = parser.parse_args()
    
    target_dir = os.path.abspath(args.target_dir)
    engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    if not args.link_only:
        if not args.platform or not args.name or not args.id or not args.package:
            parser.error("--platform, --name, --id, and --package are required when --link-only is not specified.")
            
    if args.link_only:
        print(f"=== Linking Engine to Existing Project: {target_dir} ===")
        os.makedirs(target_dir, exist_ok=True)
    else:
        print(f"=== Initializing Minecraft Mod Project: {args.name} ===")
        print(f"Target Directory: {target_dir}")
        print(f"Engine Directory: {engine_dir}")
        
        # 1. テンプレートプロジェクトのコピー展開
        template_src = os.path.join(engine_dir, "templates", args.platform)
        spec = {
            'platform': args.platform,
            'mod_id': args.id,
            'mod_name': args.name,
            'package': args.package
        }
        
        if os.path.exists(template_src):
            # build.gradleが存在しない場合のみテンプレートをコピー
            if not os.path.exists(os.path.join(target_dir, "build.gradle")):
                print(f"[Init] Copying project templates for {args.platform}...")
                success = copy_template_dir(template_src, target_dir, spec)
                if not success:
                    print("Failed to copy templates.")
                    sys.exit(1)
            else:
                print("[Init] Project template already expanded. Skipping template copy.")
        else:
            print(f"Warning: Template source not found at {template_src}. Skipping template copy.")
            os.makedirs(target_dir, exist_ok=True)

    # 2. ジャンクション/シンボリックリンクの作成
    # リンク対象のリスト (共通エンジン側 -> ターゲット側)
    links_to_create = [
        (".agents", ".agents")
    ]
    
    for rel_src, rel_dst in links_to_create:
        src_path = os.path.join(engine_dir, rel_src)
        dst_path = os.path.join(target_dir, rel_dst)
        create_junction_or_link(src_path, dst_path)

    # 3. .devcontainer 設定ファイルの配置 (コピー)
    devcontainer_src = os.path.join(engine_dir, ".devcontainer")
    devcontainer_dst = os.path.join(target_dir, ".devcontainer")
    if os.path.exists(devcontainer_src) and not os.path.exists(devcontainer_dst):
        print(f"[Init] Copying .devcontainer configuration...")
        shutil.copytree(devcontainer_src, devcontainer_dst)
        print(f"Copied: {devcontainer_dst}")

    # 4. 仕様書テンプレートの作成
    if not args.link_only:
        create_specification_template(target_dir, spec)
    
    # 5. 環境診断と案内の出力
    print("\n" + "="*50)
    print("SUCCESS: Project linked successfully!")
    print("="*50)
    print("Next steps:")
    print(f"  1. Go to the project directory:")
    print(f"     cd {target_dir}")
    print(f"  2. Run the environment check tool to verify dependencies:")
    print(f"     python .agents/scripts/env_doctor.py")
    print(f"  3. Run the version updater tool if you need to upgrade Minecraft version:")
    print(f"     python .agents/scripts/version_updater.py 26.2 --activate")
    print("="*50 + "\n")

if __name__ == '__main__':
    main()
