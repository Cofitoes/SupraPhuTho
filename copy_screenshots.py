import os
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    # Stage only trips_logic_v6.js
    subprocess.run([git_path, "add", "trips_logic_v6.js"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    
    # Commit
    subprocess.run([git_path, "commit", "-m", "Implement fixed route combining logic in trips_logic_v6.js"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    
    # Push to origin main
    subprocess.run([git_path, "push", "origin", "main"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)

    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("Successfully committed and pushed route combining logic updates to GitHub.\n")

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
