import os

for f in [r"g:\My Drive\Training AI\Supra Phú Thọ\read_docx.py", r"g:\My Drive\Training AI\Supra Phú Thọ\read_docx_bg.py"]:
    if os.path.exists(f):
        try:
            os.remove(f)
        except:
            pass

if os.path.exists(__file__):
    os.remove(__file__)
