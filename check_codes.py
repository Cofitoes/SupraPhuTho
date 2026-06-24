import sys
import pandas as pd
import glob

sys.stdout.reconfigure(encoding='utf-8')
codes = set()
for f in glob.glob(r'Data_Booking\*.xls*'):
    try:
        df = pd.read_excel(f, engine='openpyxl')
        if 'Mã siêu thị ' in df.columns:
            for _, r in df[['Mã siêu thị ', 'Tên siêu thị']].drop_duplicates().iterrows():
                codes.add(f"{str(r['Mã siêu thị ']).strip()} -> {str(r['Tên siêu thị']).strip()}")
    except:
        pass

for c in sorted(list(codes)):
    print(c)
