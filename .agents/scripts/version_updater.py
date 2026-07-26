import os
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
import re

def get_html_or_xml(url):
    """URLからテキストコンテンツ（JSON/XML）を取得します。"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to fetch from {url}. Error: {e}")
        return None

def determine_java_version(mc_version):
    """Minecraftのバージョンから推奨Javaバージョンを判定します。"""
    # 26.x系（最新の実験的バージョン/1.21.4相当）や 1.21.2以上は Java 25
    if mc_version.startswith("26") or mc_version.startswith("27"):
        return "25"
        
    match = re.match(r'^1\.(\d+)(?:\.(\d+))?', mc_version)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else 0
        
        if major > 21 or (major == 21 and minor >= 2):
            return "25"
        elif major == 21 or (major == 20 and minor >= 5):
            return "21"
        elif major >= 17:
            return "17"
            
    return "21" # デフォルト

def fetch_fabric_loader():
    """Fabric Meta APIから最新の安定版 Loader バージョンを取得します。"""
    print("[Updater] Fetching latest Fabric Loader version...")
    url = "https://meta.fabricmc.net/v2/versions/loader"
    data = get_html_or_xml(url)
    if data:
        try:
            loaders = json.loads(data)
            # stable が True の最新のものを探す
            for loader in loaders:
                if loader.get("stable") == True:
                    return loader.get("version")
            # 見つからない場合は最初の要素
            if loaders:
                return loaders[0].get("version")
        except Exception as e:
            print(f"Error parsing Loader JSON: {e}")
    return "0.15.11" # フォールバック

def fetch_fabric_api(mc_version):
    """Fabric Maven メタデータから、指定された Minecraft バージョンに対応する最新の Fabric API バージョンを取得します。"""
    print(f"[Updater] Fetching Fabric API version for Minecraft {mc_version}...")
    url = "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml"
    xml_data = get_html_or_xml(url)
    if xml_data:
        try:
            root = ET.fromstring(xml_data)
            versions = [v.text for v in root.findall(".//version")]
            
            # 指定されたMCバージョン（例: "+1.21.4" や "+26.2"）に合致する最新のバージョンを探す
            suffix = f"+{mc_version}"
            matched = [v for v in versions if v.endswith(suffix)]
            
            if matched:
                # 自然ソートで最新のものを選ぶ（単純ソートでも十分）
                matched.sort()
                return matched[-1]
                
            # スナップショット等の曖昧一致のフォールバック
            # 例: バージョン文字列の中に mc_version が含まれるもの
            matched_lax = [v for v in versions if mc_version in v]
            if matched_lax:
                matched_lax.sort()
                return matched_lax[-1]
        except Exception as e:
            print(f"Error parsing Fabric API Maven XML: {e}")
            
    # デフォルトのフォールバック形式
    return f"0.154.0+{mc_version}"

def fetch_neoforge_version(mc_version):
    """NeoForge Maven メタデータから、指定された Minecraft バージョンに対応する最新の NeoForge バージョンを取得します。"""
    print(f"[Updater] Fetching NeoForge version for Minecraft {mc_version}...")
    url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
    xml_data = get_html_or_xml(url)
    if xml_data:
        try:
            root = ET.fromstring(xml_data)
            versions = [v.text for v in root.findall(".//version")]
            
            # NeoForgeのバージョン体系: 
            # MC 1.21.4 -> NeoForge 21.4.x (21.4.15 等)
            # MC 26.2 -> NeoForge 26.2.x
            # パターンを構成
            prefix = ""
            if mc_version.startswith("1."):
                parts = mc_version.split('.')
                if len(parts) >= 2:
                    prefix = f"{parts[1]}.{parts[2] if len(parts) > 2 else '0'}."
            else:
                prefix = f"{mc_version}."
                
            matched = [v for v in versions if v.startswith(prefix)]
            if matched:
                # バージョン順にソートして最新を取得
                # 例: 21.4.2 と 21.4.10 で正しくソートするためにセグメントに分解してソート
                def version_key(v_str):
                    # 記号やアルファベット（-beta等）を考慮しつつ数値でパース
                    parts = re.split(r'[-.]', v_str)
                    key = []
                    for p in parts:
                        if p.isdigit():
                            key.append(int(p))
                        else:
                            key.append(p)
                    return key
                matched.sort(key=version_key)
                return matched[-1]
        except Exception as e:
            print(f"Error parsing NeoForge Maven XML: {e}")
            
    return f"{mc_version}.0.0-beta" # フォールバック

def main():
    if len(sys.argv) < 2:
        print("Usage: python version_updater.py <minecraft_version> [--activate]")
        sys.exit(1)
        
    mc_version = sys.argv[1]
    activate = "--activate" in sys.argv
    
    print(f"=== Starting Metadata Update for Minecraft {mc_version} ===")
    
    # 1. 各推奨バージョンの収集
    java_ver = determine_java_version(mc_version)
    loader_ver = fetch_fabric_loader()
    fabric_api_ver = fetch_fabric_api(mc_version)
    neoforge_ver = fetch_neoforge_version(mc_version)
    
    # Paperは標準的な構成で出力
    paper_ver = f"{mc_version}-R0.1-SNAPSHOT"
    
    # 2. 設定オブジェクトの構築
    version_config = {
        "minecraft_version": mc_version,
        "java_version": java_ver,
        "platforms": {
            "fabric": {
                "loader_version": loader_ver,
                "api_version": fabric_api_ver,
                "mapping_type": "mojang"
            },
            "neoforge": {
                "version": neoforge_ver,
                "mapping_type": "mojang"
            },
            "paper": {
                "api_version": paper_ver
            }
        }
    }
    
    # 保存先パスの決定
    config_dir = os.path.join(os.path.dirname(__file__), "../config")
    versions_dir = os.path.join(config_dir, "versions")
    os.makedirs(versions_dir, exist_ok=True)
    
    out_file = os.path.join(versions_dir, f"{mc_version}.json")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(version_config, f, indent=2)
        
    print(f"\n[Updater] SUCCESS: Saved configuration to {out_file}")
    print(json.dumps(version_config, indent=2))
    
    # 3. アクティベーション指定がある場合
    if activate:
        active_version_file = os.path.join(config_dir, "active_version.json")
        active_config = {
            "active_version": mc_version
        }
        with open(active_version_file, 'w', encoding='utf-8') as f:
            json.dump(active_config, f, indent=2)
        print(f"[Updater] SUCCESS: Activated version '{mc_version}' in {active_version_file}")

if __name__ == '__main__':
    main()
