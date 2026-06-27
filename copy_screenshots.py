import os
import subprocess

try:
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    # Files to delete
    files_to_delete = [
        "patch.py",
        "patch_catch.py",
        "patch_demo.py",
        "patch_district.py",
        "patch_early_return.py",
        "patch_empty.py",
        "patch_html_v6.py",
        "patch_logic.py",
        "patch_v3.py",
        "patch_v4.py",
        "patch_v6.py",
        "patch_valid.py",
        "temp_script.js",
        "unhide_button.py",
        "git_push.log"
    ]

    deleted_any = False
    for f in files_to_delete:
        f_path = os.path.join(r"g:\My Drive\Training AI\Supra Phú Thọ", f)
        if os.path.exists(f_path):
            os.remove(f_path)
            # Remove from git index
            subprocess.run([git_path, "rm", "--cached", f], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", capture_output=True)
            deleted_any = True

    if deleted_any:
        # Commit cleanup
        subprocess.run([git_path, "commit", "-m", "Clean up temporary patch and helper files"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ")
        subprocess.run([git_path, "push", "origin", "main"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ")

except Exception as e:
    pass
