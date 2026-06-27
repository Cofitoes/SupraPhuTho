import subprocess
import os

try:
    # 1. Fix git config
    subprocess.run(["git", "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "config", "core.safecrlf", "false"], check=True)
    
    # 2. Run restore
    restore_script = r"g:\My Drive\Training AI\Supra Phú Thọ\restore_bat.py"
    if os.path.exists(restore_script):
        with open(restore_script, 'r', encoding='utf-8') as f:
            exec(f.read())
            
    # 3. Clean itself up
    os.remove(__file__)
except Exception as e:
    with open(r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log", 'a', encoding='utf-8') as log:
        log.write(f"ERROR fixing git config: {e}\n")
