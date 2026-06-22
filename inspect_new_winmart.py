import pandas as pd

file_path = r'g:\My Drive\Training AI\Supra Phú Thọ\Danh sách Winmart (1).xlsx'
out_path = r'g:\My Drive\Training AI\Supra Phú Thọ\new_winmart_cols.txt'

try:
    df = pd.read_excel(file_path, nrows=5)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("Columns:\n")
        f.write(str(df.columns.tolist()) + "\n\n")
        f.write("First row:\n")
        f.write(str(df.iloc[0].to_dict()) + "\n")
        
    df2 = pd.read_excel(file_path, header=1, nrows=5)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write("\nColumns (Header 1):\n")
        f.write(str(df2.columns.tolist()) + "\n\n")
        f.write("First row (Header 1):\n")
        f.write(str(df2.iloc[0].to_dict()) + "\n")
except Exception as e:
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("Error: " + str(e))
