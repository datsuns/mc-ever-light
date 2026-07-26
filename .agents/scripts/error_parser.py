import os
import re
import glob

def check_crash_reports(project_dir):
    """
    プロジェクト内の crash-reports ディレクトリから直近のクラッシュレポートを解析します。
    """
    search_paths = [
        os.path.join(project_dir, 'crash-reports', '*.txt'),
        os.path.join(project_dir, 'run', 'crash-reports', '*.txt'),
        # Paper サーバー等の場合
        os.path.join(project_dir, 'logs', 'latest.log')
    ]
    
    crash_files = []
    for path in search_paths:
        if '*' in path:
            crash_files.extend(glob.glob(path))
        elif os.path.exists(path):
            crash_files.append(path)
            
    if not crash_files:
        return []
        
    # 最新のファイルを選択 (latest.log を含む場合は更新日時で比較)
    latest_file = max(crash_files, key=os.path.getmtime)
    
    analysis = []
    try:
        with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        file_link = latest_file.replace('\\', '/')
        analysis.append(f"- **Source File**: [{os.path.basename(latest_file)}](file:///{file_link})")
        
        # クラッシュレポートの場合
        if "Minecraft Crash Report" in content or "Description:" in content:
            desc_match = re.search(r'Description:\s*([^\n]+)', content)
            if desc_match:
                analysis.append(f"- **Description**: `{desc_match.group(1).strip()}`")
                
            # スタックトレースの抽出
            stack_trace_match = re.search(r'Time:.*?\n(.*?)\n\n-- System Details --', content, re.DOTALL)
            if stack_trace_match:
                trace = stack_trace_match.group(1)
                lines = [line.strip() for line in trace.split('\n') if line.strip().startswith('at ')]
                
                # エラー原因となった可能性が高い自作コードの行を探索
                cause_line = None
                for line in lines:
                    # 標準的なライブラリやMinecraft本体以外のパッケージを探す
                    if not any(pkg in line for pkg in ['at java.', 'at sun.', 'at net.minecraft.', 'at org.spongepowered.asm.mixin.', 'at com.mojang.']):
                        cause_line = line
                        break
                
                if not cause_line and lines:
                    cause_line = lines[0] # 見つからなければスタックの最上位
                    
                if cause_line:
                    analysis.append(f"- **Suspected Stack Line**: `{cause_line}`")
                    
                    # クラス名と行数の抽出を試みる
                    # 例: at com.example.mymod.MyMod.onInitialize(MyMod.java:25)
                    loc_match = re.search(r'([\w\.]+)\.([\w\<]+)\(([\w\.]+):(\d+)\)', cause_line)
                    if loc_match:
                        class_name, method, file_name, line_num = loc_match.groups()
                        analysis.append(f"- **File Hint**: `{file_name}` at line `{line_num}` (Method: `{method}`)")
        
        # 通常のログファイルの場合のエラー抽出 (Exceptionの検知)
        else:
            # Exceptionパターン検索 (例: java.lang.NullPointerException: ...)
            exc_matches = re.findall(r'(\b\w+\.\w+\.\w+Exception:\s*[^\n]+)', content)
            if exc_matches:
                # 直近のエラーを表示
                analysis.append(f"- **Detected Exception**: `{exc_matches[-1]}`")
                
    except Exception as e:
        analysis.append(f"- *Failed to parse error log: {str(e)}*")
        
    return analysis

def analyze_output(gradle_output, project_dir):
    """
    Gradle のビルド出力（コンパイルエラーなど）をパースします。
    """
    analysis = []
    
    # コンパイルエラーの抽出パターン (Windows/日本語/文字化け対応)
    # 例: F:\work\...\MyMod.java:12: error: ...
    # もしくは F:\work\...\MyMod.java:12: エラー: ...
    # もしくは F:\work\...\MyMod.java:12: G[: ...
    compile_error_pattern = re.compile(
        r'([a-zA-Z]:\\[^\n:]+|/[^\n:]+):(\d+):\s*(?:error|エラー|G\.|G\:|\:G)\s*:\s*([^\n]+)',
        re.IGNORECASE
    )
    
    matches = compile_error_pattern.findall(gradle_output)
    if matches:
        analysis.append("### Detected Compile Errors")
        for file_path, line_num, reason in matches:
            rel_path = os.path.relpath(file_path, project_dir) if os.path.isabs(file_path) else file_path
            file_link = file_path.replace('\\', '/')
            analysis.append(
                f"- **Type**: Java Compile Error\n"
                f"- **File**: [{os.path.basename(rel_path)}](file:///{file_link})\n"
                f"- **Line**: {line_num}\n"
                f"- **Reason**: `{reason.strip()}`\n"
            )
            
    # Mixin アノテーションプロセッサなどの警告・エラー
    mixin_error_pattern = re.compile(
        r'error:\s+(Mixin\s+annotation\s+processor\s+error:\s+[^\n]+)'
    )
    mixin_matches = mixin_error_pattern.findall(gradle_output)
    if mixin_matches:
        analysis.append("### Detected Mixin Processor Errors")
        for err in mixin_matches:
            analysis.append(f"- **Error**: `{err}`")

    # 実行時クラッシュレポートの確認
    crash_analysis = check_crash_reports(project_dir)
    if crash_analysis:
        analysis.append("### Detected Runtime Diagnostics")
        analysis.extend(crash_analysis)

    # 何も検出されなかったがビルドが失敗している場合
    if not analysis:
        if "BUILD FAILED" in gradle_output:
            analysis.append("### Build Failed (Reason Unknown)\nGradle reported a build failure, but no specific standard Java compiler errors were matched in the console output. This could be due to a Gradle configuration error, dependency resolution failure, or test failure.")
        else:
            analysis.append("No errors or crashes detected in logs.")

    return "\n".join(analysis)

if __name__ == '__main__':
    # 簡易的にコマンドラインからも実行できるようにする
    import sys
    if len(sys.argv) > 1:
        project = sys.argv[1]
        print(check_crash_reports(project))
