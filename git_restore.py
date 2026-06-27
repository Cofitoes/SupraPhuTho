import subprocess
import os

try:
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    # Reset any changes in demo.html and index.html
    subprocess.run([git_path, "checkout", "--", "demo.html", "index.html"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    print("Successfully restored demo.html and index.html using git checkout")
    
    # Self delete
    os.remove(__file__)
except Exception as e:
    with open(r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log", 'w', encoding='utf-8') as log:
        log.write(f"ERROR restoring: {e}\n")
