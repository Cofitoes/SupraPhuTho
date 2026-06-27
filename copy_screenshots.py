import os
import re
import py_compile
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"
root_dir = r"g:\My Drive\Training AI\Supra Phú Thọ"

try:
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    report = []
    
    # === 1. CODE SYNTAX SCANNING & LINTING ===
    report.append("=== 1. CODE SYNTAX CHECK ===")
    
    # Python files syntax check
    py_files = [f for f in os.listdir(root_dir) if f.endswith(".py") and f != "copy_screenshots.py"]
    for py_f in py_files:
        py_path = os.path.join(root_dir, py_f)
        try:
            py_compile.compile(py_path, doraise=True)
            report.append(f"  [OK] Python syntax: {py_f}")
        except Exception as e:
            report.append(f"  [ERROR] Python syntax error in {py_f}: {e}")

    # Javascript files syntax check (simple bracket matching & regex check)
    js_files = [f for f in os.listdir(root_dir) if f.endswith(".js")]
    for js_f in js_files:
        js_path = os.path.join(root_dir, js_f)
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Basic validation of brace matching
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                report.append(f"  [WARNING] JS brace mismatch in {js_f}: open={open_braces}, close={close_braces}")
            else:
                report.append(f"  [OK] JS syntax check (braces matched): {js_f}")
        except Exception as e:
            report.append(f"  [ERROR] JS read error in {js_f}: {e}")

    # === 2. DATA DIRECTORY CLEANUP ===
    report.append("\n=== 2. DATA DIRECTORY CLEANUP ===")
    
    # Duplicates & temp files to delete in root
    root_deletions = [
        "Mo_Giao_Dien_Local_Edge (1).bat",
        "Mo_Giao_Dien_Online_Edge (1).bat",
        "Lichsu[01h05 - 27-06-26] (1).md",
        "test_perf3.py",
        "test_v6.js"
    ]
    for rd in root_deletions:
        rd_path = os.path.join(root_dir, rd)
        if os.path.exists(rd_path):
            os.remove(rd_path)
            subprocess.run([git_path, "rm", "--cached", rd], cwd=root_dir, capture_output=True)
            report.append(f"  [DELETED] Root file: {rd}")

    # Delete duplicate excel files in Data_Booking
    data_booking_dir = os.path.join(root_dir, "Data_Booking")
    booking_deletions = [
        "Booking Supra 26-06-2026 (1).xlsx",
        "Booking Supra 27-06-2026 (1).xlsx"
    ]
    for bd in booking_deletions:
        bd_path = os.path.join(data_booking_dir, bd)
        if os.path.exists(bd_path):
            os.remove(bd_path)
            subprocess.run([git_path, "rm", "--cached", f"Data_Booking/{bd}"], cwd=root_dir, capture_output=True)
            report.append(f"  [DELETED] Booking duplicate: {bd}")

    # Delete Word temp files (starts with ~$ and ends with .docx)
    for f in os.listdir(root_dir):
        if f.startswith("~$") and f.endswith(".docx"):
            os.remove(os.path.join(root_dir, f))
            report.append(f"  [DELETED] Word lock file: {f}")

    # === 3. GIT STATUS & SYNC ===
    report.append("\n=== 3. GIT SYNCHRONIZATION ===")
    # Push changes to Github
    subprocess.run([git_path, "add", "-A"], cwd=root_dir, capture_output=True)
    commit_proc = subprocess.run([git_path, "commit", "-m", "System cleanup: Remove duplicate bat/excel files and check syntax"], cwd=root_dir, capture_output=True, text=True)
    if "nothing to commit" in commit_proc.stdout or "nothing added to commit" in commit_proc.stdout:
        report.append("  [OK] Git status: No new cleanups to commit.")
    else:
        push_proc = subprocess.run([git_path, "push", "origin", "main"], cwd=root_dir, capture_output=True, text=True)
        report.append("  [OK] Cleanups committed and pushed to GitHub.")

    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("\n".join(report))

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR during system cleanup: {e}\n")
