import pandas as pd

existing_path = r'g:\My Drive\Training AI\Supra Phú Thọ\DS_Winmart_Extracted.xlsx'

df = pd.read_excel(existing_path)
total = len(df)

# count non empty coords
def is_valid(x):
    if pd.isna(x): return False
    x = str(x).strip()
    if x == '' or x.lower() == 'nan': return False
    return True

with_coords = df['Vị trí Lat/Long'].apply(is_valid).sum()

print(f"Total stores: {total}")
print(f"Stores with coordinates: {with_coords}")
print(f"Stores without coordinates: {total - with_coords}")
