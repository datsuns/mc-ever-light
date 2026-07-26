import os
import sys
import subprocess
import shutil

def run_command(args, shell=False):
    """コマンドを実行し、成功判定と標準出力を返します。"""
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell
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
            
        stdout_str = safe_decode(result.stdout)
        stderr_str = safe_decode(result.stderr)
        return result.returncode == 0, stdout_str.strip(), stderr_str.strip()
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Dockerのインストールと起動状態をチェックします。"""
    print("[Doctor] Checking Docker status...")
    has_docker = shutil.which("docker") is not None
    if not has_docker:
        return False, "Docker is not installed."
        
    # デーモンの起動状態チェック
    ok, stdout, stderr = run_command(["docker", "info"])
    if not ok:
        return False, "Docker is installed, but the Docker daemon is not running. Please start Docker Desktop/Engine."
        
    return True, "Docker is installed and running."

def check_vscode():
    """VS Codeのインストールをチェックします。"""
    print("[Doctor] Checking VS Code status...")
    has_code = shutil.which("code") is not None
    if has_code:
        return True, "VS Code command 'code' is available on PATH."
        
    # Windowsのデフォルトインストールパスのチェック
    if sys.platform.startswith('win'):
        default_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\bin\code.cmd")
        ]
        for path in default_paths:
            if os.path.exists(path):
                return True, f"VS Code found at default path: {path} (Not on PATH, but available)"
                
    return False, "VS Code (or 'code' command) is not found."

def check_wsl_gui():
    """Windows環境で WSL2/WSLg の状態をチェックします。"""
    if not sys.platform.startswith('win'):
        return True, "Not running on Windows (WSL check skipped)."
        
    print("[Doctor] Checking WSL2 and WSLg status...")
    has_wsl = shutil.which("wsl") is not None
    if not has_wsl:
        return False, "WSL (Windows Subsystem for Linux) is not enabled on this machine."
        
    # WSLのステータスチェック
    ok, stdout, stderr = run_command(["wsl", "--status"])
    if not ok:
        return False, f"WSL command failed: {stderr}. WSL2 might not be fully installed."
        
    # WSLg (GUI) の起動確認
    # WSLの仮想グラフィックドライバやマウントパスの有無を確認
    # 簡易的に、現在実行中のディストリビューションから /mnt/wslg が見えるか調べる
    # もしくは、Windows 11 のビルド番号を確認（WSLgはWin11 / Win10 21H2以降で標準提供）
    import platform
    release = platform.release()
    try:
        build_number = int(platform.version().split('.')[-1])
        if build_number >= 22000: # Windows 11 Build 22000+
            return True, f"Windows 11 detected (Build {build_number}). WSLg GUI forwarding is supported by default."
        else:
            return False, f"Windows version is outdated (Build {build_number}). WSLg requires Windows 11 or Windows 10 Build 19044+."
    except Exception:
        # フォールバック
        return True, "WSL is installed. WSLg support is assumed (Windows 11 target)."

def get_fix_commands(diagnostics):
    """不足しているコンポーネントに対応する修復コマンドを返します。"""
    fixes = {}
    is_windows = sys.platform.startswith('win')
    
    if not diagnostics['docker'][0]:
        if is_windows:
            fixes['Docker Desktop'] = "winget install Docker.DockerDesktop"
        else:
            fixes['Docker Engine'] = "sudo apt-get update && sudo apt-get install -y docker.io && sudo systemctl enable --now docker"
            
    if not diagnostics['vscode'][0]:
        if is_windows:
            fixes['VS Code'] = "winget install Microsoft.VisualStudioCode"
        else:
            fixes['VS Code'] = "sudo snap install --classic code"
            
    if is_windows and not diagnostics['wsl_gui'][0]:
        fixes['WSL2 / WSLg'] = "wsl --install"
        
    return fixes

def run_fix(fixes):
    """修復コマンドを実行します。"""
    print("\n[Doctor] Initiating automatic environment setup...")
    for component, cmd in fixes.items():
        print(f"\nSetting up {component} using command: {cmd}")
        # コマンドのパース (シェル経由で実行)
        ok, stdout, stderr = run_command(cmd, shell=True)
        if ok:
            print(f"SUCCESS: {component} setup completed successfully.")
        else:
            print(f"ERROR: Failed to setup {component}. Details: {stderr}")
            print("Please try running the command manually with administrator privileges.")

def main():
    print("=== Minecraft Modding Environment Doctor ===")
    
    diagnostics = {
        'docker': check_docker(),
        'vscode': check_vscode(),
        'wsl_gui': check_wsl_gui()
    }
    
    print("\n=== DIAGNOSTICS REPORT ===")
    all_ok = True
    for key, (ok, desc) in diagnostics.items():
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {key.upper()}: {desc}")
        if not ok:
            all_ok = False
            
    fixes = get_fix_commands(diagnostics)
    
    if all_ok:
        print("\n[Doctor] Congratulations! Your host environment is fully compatible.")
        print("You can run 'Reopen in Container' in VS Code to start developing.")
        sys.exit(0)
    else:
        print("\n[Doctor] Warning: Some required components are missing or not running.")
        
        if fixes:
            print("\nRecommended repair commands:")
            for comp, cmd in fixes.items():
                print(f"  - {comp}: {cmd}")
                
            # 引数チェック (--fix) またはインタラクティブ実行
            is_fix = "--fix" in sys.argv
            
            if is_fix:
                run_fix(fixes)
            else:
                print("\nTo automatically setup these missing components, run:")
                print("  python scripts/env_doctor.py --fix")
                print("(Note: Automatic install may require administrator/root privileges)")
                
        sys.exit(1)

if __name__ == '__main__':
    main()
