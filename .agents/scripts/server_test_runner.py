import os
import sys
import subprocess
import time
import threading

def safe_decode(b):
    """バイト列を安全に文字列へデコードします。"""
    if not b:
        return ""
    for encoding in ['utf-8', 'cp932', 'shift_jis']:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', errors='ignore')

def fix_gradlew_newlines(project_dir):
    """WindowsのCRLF改行コードによってLinuxコンテナ内でエラーになるのを防ぐため、gradlewの改行コードをLFに変換します。"""
    gradlew_path = os.path.join(project_dir, "gradlew")
    if os.path.exists(gradlew_path):
        try:
            with open(gradlew_path, 'rb') as f:
                content = f.read()
            # \r\n を \n に変換
            lf_content = content.replace(b'\r\n', b'\n')
            if lf_content != content:
                with open(gradlew_path, 'wb') as f:
                    f.write(lf_content)
                print(f"[ServerTest] Fixed gradlew CRLF -> LF for {gradlew_path}")
        except Exception as e:
            print(f"[ServerTest] Warning: Failed to check/fix gradlew line endings: {e}")

def agree_to_eula(project_dir):
    """MinecraftのEULAに自動で同意（eula.txtの生成・更新）します。"""
    paths = [
        os.path.join(project_dir, "eula.txt"),
        os.path.join(project_dir, "run", "eula.txt")
    ]
    for path in paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n")
                f.write(f"# {time.strftime('%a %b %d %H:%M:%S %Z %Y')}\n")
                f.write("eula=true\n")
            print(f"[ServerTest] Auto-agreed to EULA at {path}")
        except Exception as e:
            print(f"[ServerTest] Warning: Failed to write EULA to {path}: {e}")

def cleanup_old_crashes(project_dir):
    """古いクラッシュレポートを削除して、エラー判定の混同を防ぎます。"""
    import glob
    search_paths = [
        os.path.join(project_dir, 'crash-reports', '*.txt'),
        os.path.join(project_dir, 'run', 'crash-reports', '*.txt')
    ]
    for path in search_paths:
        for f in glob.glob(path):
            try:
                os.remove(f)
                print(f"[ServerTest] Cleaned up old crash report: {f}")
            except Exception as e:
                print(f"[ServerTest] Warning: Failed to delete old crash report {f}: {e}")

def run_server_test(project_dir, timeout_seconds=300):
    """
    指定されたプロジェクトディレクトリ上でヘッドレスサーバーを起動し、
    ログを監視して正常起動・異常クラッシュを判定します。
    """
    print(f"=== Starting Headless Server Test for project: {project_dir} ===")
    
    # 前処理: 改行コードの修正、EULA同意、古いクラッシュ削除
    fix_gradlew_newlines(project_dir)
    agree_to_eula(project_dir)
    cleanup_old_crashes(project_dir)
    
    # 実行コマンドの決定 (OS互換)
    is_windows = sys.platform.startswith('win')
    cmd = ["gradlew.bat", "runServer"] if is_windows else ["./gradlew", "runServer"]
    
    # プロセスの非同期起動
    try:
        process = subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # stderrをstdoutにマージして一本で監視
            shell=is_windows
        )
    except Exception as e:
        print(f"[ServerTest] ERROR: Failed to launch process: {e}")
        return False, str(e)

    # 状態管理変数
    success = False
    error_detected = False
    error_log = []
    full_log = []
    
    # 起動検知のシグナル
    # 例: "Done (2.345s)! For help, type "help""
    done_pattern = "Done ("
    
    # クラッシュ・エラーを示す一般的なパターン
    error_patterns = [
        "Exception in thread",
        "FATAL ERROR",
        "MixinInitialisationError",
        "Mixin apply failed",
        "Uncaught exception in thread",
        "NullPointerException",
        "IllegalStateException",
        "FAILED"
    ]

    print("[ServerTest] Monitoring server log output (this may take a few minutes)...")
    
    # タイムアウトスレッドの開始
    def check_timeout():
        time.sleep(timeout_seconds)
        if process.poll() is None:
            print(f"\n[ServerTest] ERROR: Timeout reached ({timeout_seconds}s). Terminating server...")
            process.terminate()
            
    timeout_thread = threading.Thread(target=check_timeout, daemon=True)
    timeout_thread.start()

    # ログ監視ループ
    try:
        while True:
            line_bytes = process.stdout.readline()
            if not line_bytes and process.poll() is not None:
                break
                
            line = safe_decode(line_bytes)
            if not line:
                continue
                
            full_log.append(line.strip())
            # ログをリアルタイムで出力
            print(line, end="")
            
            # エラーパターンの監視
            for err in error_patterns:
                if err in line:
                    error_detected = True
                    # 周辺ログの記録
                    error_log.append(line.strip())
                    
            if error_detected:
                # エラー検出時は追加の数行（スタックトレース等）をキャプチャするために少し蓄積
                error_log.append(line.strip())
                if len(error_log) > 20: # 20行ほどキャプチャしたら終了
                    print("\n[ServerTest] Major error detected in logs. Terminating server...")
                    process.terminate()
                    break

            # 起動完了の検知
            if done_pattern in line and ")! For help" in line:
                print("\n[ServerTest] SUCCESS: Server started successfully. Sending 'stop' command...")
                success = True
                try:
                    process.stdin.write(b"stop\n")
                    process.stdin.flush()
                except Exception as e:
                    print(f"[ServerTest] Failed to write 'stop' to stdin: {e}")
                    process.terminate()
                break
                
    except Exception as e:
        print(f"\n[ServerTest] Error during log monitoring: {e}")
        process.terminate()

    # プロセスの終了待ち
    print("[ServerTest] Waiting for server process to exit...")
    ret_code = process.wait()
    
    # 結果の判定
    if success:
        print("\n[ServerTest] Verification SUCCESS! Server initialized and shut down cleanly.")
        return True, "Clean startup and shutdown confirmed."
    else:
        # エラーパーサー用にエラー周辺のログを出力
        print("\n[ServerTest] Verification FAILED! Server crashed or failed to initialize.")
        err_msg = "\n".join(error_log) if error_log else "Server process exited prematurely with code " + str(ret_code)
        
        # error_parser.py をインポートして詳細解析を試みる
        sys.path.append(os.path.dirname(__file__))
        try:
            from error_parser import analyze_output
            report = analyze_output("\n".join(full_log), project_dir)
            if report:
                print("\n=== PARSED ERROR REPORT ===")
                print(report)
                print("===========================")
        except Exception as pe:
            print(f"Failed to parse error log with error_parser: {pe}")
            
        return False, err_msg

def main():
    if len(sys.argv) < 2:
        print("Usage: python server_test_runner.py <project_directory> [timeout_seconds]")
        sys.exit(1)
        
    project_dir = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    success, desc = run_server_test(project_dir, timeout)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
