import os
import sys
import json
import urllib.request
import re

# キャッシュディレクトリの定義 (ワークスペース内)
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../.cache/mappings')
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

def get_mappings_url_from_manifest(version):
    """
    Mojangのバージョンマニフェストから、指定されたバージョンの mappings URL を取得します。
    """
    try:
        print(f"Fetching version manifest to find mappings for Minecraft {version}...")
        with urllib.request.urlopen(MANIFEST_URL) as response:
            manifest = json.loads(response.read().decode('utf-8'))
            
        version_url = None
        for v in manifest.get('versions', []):
            if v.get('id') == version:
                version_url = v.get('url')
                break
                
        if not version_url:
            # 26.2 などの新しいバージョンがまだ見つからない場合のフォールバック（最新のリリースを使用）
            print(f"Version {version} not found in manifest. Trying to find latest release...")
            latest_release = manifest.get('latest', {}).get('release')
            for v in manifest.get('versions', []):
                if v.get('id') == latest_release:
                    version_url = v.get('url')
                    version = latest_release
                    print(f"Fallback to latest release version: {version}")
                    break

        if not version_url:
            return None, None

        # バージョン詳細JSONの取得
        with urllib.request.urlopen(version_url) as response:
            version_details = json.loads(response.read().decode('utf-8'))
            
        downloads = version_details.get('downloads', {})
        client_mappings_info = downloads.get('client_mappings')
        if not client_mappings_info:
            return "DEOBFUSCATED", version
            
        client_mappings = client_mappings_info.get('url')
        return client_mappings, version
    except Exception as e:
        print(f"Error fetching mappings URL: {e}")
        return None, None

def download_mappings(version, file_path):
    """
    指定バージョンのマッピングファイルをダウンロードして保存します。
    """
    url, actual_version = get_mappings_url_from_manifest(version)
    if not url:
        print(f"Could not find mappings URL for version {version}")
        return False
    if url == "DEOBFUSCATED":
        return "DEOBFUSCATED"
        
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    print(f"Downloading Mojang Mappings for {actual_version} from {url}...")
    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"Saved mappings to {file_path}")
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def parse_proguard_mappings(file_path):
    """
    Proguardマッピングファイルをパースし、クラス、メソッド、フィールドのマッピング情報を返します。
    """
    class_to_obf = {}
    obf_to_class = {}
    
    # 簡易辞書 (メモリ効率を考慮し、検索対象の主要情報のみを整理)
    # 構造: { 'net.minecraft.world.entity.LivingEntity': { 'obf': 'bff', 'methods': { 'tick': 'l' }, 'fields': { 'health': 'a' } } }
    mappings = {}
    
    print(f"Parsing mappings file: {file_path}...")
    current_class = None
    
    # クラス定義: org.example.Class -> obf:
    # メンバ定義:     type name -> obf
    # もしくは      line:line:type name(args) -> obf
    class_pattern = re.compile(r'^([\w\.\$]+)\s+->\s+([\w\.\$]+):')
    member_pattern = re.compile(r'^\s+(?:\d+:\d+:)?([\w\.\$<>\[\]]+)\s+([\w\$<>]+)(?:\((.*?)\))?\s+->\s+([\w\$<>]+)')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_strip = line.strip('\n')
            if not line_strip or line_strip.startswith('#'):
                continue
                
            class_match = class_pattern.match(line_strip)
            if class_match:
                deobf_name, obf_name = class_match.groups()
                current_class = deobf_name
                mappings[current_class] = {
                    'obf': obf_name,
                    'methods': {},
                    'fields': {}
                }
                obf_to_class[obf_name] = deobf_name
                continue
                
            if current_class:
                member_match = member_pattern.match(line_strip)
                if member_match:
                    type_name, name, args, obf_member = member_match.groups()
                    if args is not None:
                        # メソッド
                        mappings[current_class]['methods'][name] = obf_member
                    else:
                        # フィールド
                        mappings[current_class]['fields'][name] = obf_member
                        
    return mappings, obf_to_class

def search_mappings(mappings, query):
    """
    マッピングデータをキーワードで検索します。
    """
    results = []
    query_lower = query.lower()
    
    for deobf_class, info in mappings.items():
        # クラス名検索
        if query_lower in deobf_class.lower() or query_lower in info['obf'].lower():
            results.append({
                'type': 'class',
                'deobf': deobf_class,
                'obf': info['obf']
            })
            
        # メンバ検索 (マッチ数の制限)
        if len(results) < 30:
            for method, obf in info['methods'].items():
                if query_lower == method.lower():
                    results.append({
                        'type': 'method',
                        'class': deobf_class,
                        'deobf': method,
                        'obf': obf
                    })
            for field, obf in info['fields'].items():
                if query_lower == field.lower():
                    results.append({
                        'type': 'field',
                        'class': deobf_class,
                        'deobf': field,
                        'obf': obf
                    })
                    
    return results[:30]

def main():
    if len(sys.argv) < 2:
        print("Usage: python mapping_helper.py <search_query> [version]")
        sys.exit(1)
        
    query = sys.argv[1]
    
    # バージョンの決定 (引数か、無ければ config から読み込み)
    version = "26.2"
    if len(sys.argv) > 2:
        version = sys.argv[2]
    else:
        # active_version.json から読み込みを試みる
        config_path = os.path.join(os.path.dirname(__file__), '../config/active_version.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    version = config.get('active_version', version)
            except Exception:
                pass

    mappings_file = os.path.join(CACHE_DIR, f"{version}_client_mappings.txt")
    
    if not os.path.exists(mappings_file):
        status = download_mappings(version, mappings_file)
        if status == "DEOBFUSCATED":
            print(f"Minecraft {version} is distributed without obfuscation (Deobfuscated).")
            print("No mapping resolution is needed. You can use official class/method names directly.")
            sys.exit(0)
        elif not status:
            print("Failed to obtain mappings.")
            sys.exit(1)
            
    mappings, _ = parse_proguard_mappings(mappings_file)
    
    print(f"\nSearching for '{query}' in Mojang Mappings ({version})...")
    results = search_mappings(mappings, query)
    
    if not results:
        print("No matches found.")
    else:
        print(f"\nFound {len(results)} matches:")
        for r in results:
            if r['type'] == 'class':
                print(f"[Class]  {r['deobf']}  ->  {r['obf']}")
            elif r['type'] == 'method':
                print(f"[Method] {r['class']}.{r['deobf']}()  ->  {r['obf']}")
            elif r['type'] == 'field':
                print(f"[Field]  {r['class']}.{r['deobf']}  ->  {r['obf']}")

if __name__ == '__main__':
    main()
