import os
import sys
import subprocess
import importlib

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(errors='replace')
        sys.stderr.reconfigure(errors='replace')
    except Exception:
        pass

# scripts ディレクトリをパスに追加して別スクリプトをインポートしやすくする
sys.path.append(os.path.dirname(__file__))

def run_gradle(project_dir, task='build'):
    """
    指定されたプロジェクトディレクトリで Gradle タスクを実行します。
    """
    is_windows = sys.platform.startswith('win')
    gradle_cmd = 'gradlew.bat' if is_windows else './gradlew'
    gradle_path = os.path.join(project_dir, gradle_cmd)

    if not os.path.exists(gradle_path):
        # フォルダ直下にない場合、カレントディレクトリで探す
        if os.path.exists(os.path.join(os.getcwd(), gradle_cmd)):
            gradle_path = os.path.join(os.getcwd(), gradle_cmd)
            project_dir = os.getcwd()
        else:
            return False, f"Gradle wrapper ({gradle_cmd}) not found in {project_dir} or current workspace."

    print(f"Executing: {gradle_cmd} {task} inside {project_dir}")

    # コマンドの組み立て
    # Windows の場合は shell=True でバッチファイルとして呼び出す必要がある
    try:
        env = os.environ.copy()
        env['PAGER'] = 'cat'
        
        # 非同期実行ではなく、同期実行して結果をキャプチャ (bytes)
        process = subprocess.run(
            [gradle_cmd if is_windows else gradle_path, task],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=is_windows,
            env=env
        )

        def safe_decode(b):
            if not b:
                return ""
            for encoding in ['utf-8', 'cp932', 'shift_jis']:
                try:
                    return b.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return b.decode('utf-8', errors='ignore')

        stdout_str = safe_decode(process.stdout)
        stderr_str = safe_decode(process.stderr)
        full_output = stdout_str + "\n" + stderr_str

        if process.returncode == 0:
            return True, full_output
        else:
            return False, full_output

    except Exception as e:
        return False, f"Exception occurred while running Gradle: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python gradle_runner.py <project_dir> [task]")
        sys.exit(1)

    project_dir = sys.argv[1]
    task = sys.argv[2] if len(sys.argv) > 2 else 'build'

    success, output = run_gradle(project_dir, task)

    print("\n--- GRADLE OUTPUT ---")
    print(output)
    print("----------------------\n")

    if success:
        print("SUCCESS: Gradle execution completed successfully.")
        sys.exit(0)
    else:
        print("FAILURE: Gradle execution failed.")
        
        # エラーパーサーを呼び出す
        try:
            error_parser = importlib.import_module("error_parser")
            print("\nAnalyzing errors...")
            analysis = error_parser.analyze_output(output, project_dir)
            print("\n--- ERROR ANALYSIS ---")
            print(analysis)
            print("----------------------\n")
        except ImportError:
            print("Warning: error_parser.py not found, skipping analysis.")
            
        sys.exit(1)

if __name__ == '__main__':
    main()
