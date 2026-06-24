import sys
import re

html = open('demo.html', encoding='utf-8').read()
vars = ['list', 'tripSelect', 'mqBody', 'btn', 'statusCell', 'tbody', 'reqBody', 'fillRateBody', 'ghnTripsBody', 'container', 'otpBody', 'plateSelect', 'orderLookupBody', 'tr', 'logoutBtn', 'tableBody', 'costTable', 'changePassBtn']

for v in vars:
    print(f"\n--- {v} ---")
    matches = re.findall(r'const\s+' + v + r'\s*=\s*([^;]+);', html)
    for m in matches: print(f"const {v} = {m};")
    matches = re.findall(r'let\s+' + v + r'\s*=\s*([^;]+);', html)
    for m in matches: print(f"let {v} = {m};")
    matches = re.findall(r'var\s+' + v + r'\s*=\s*([^;]+);', html)
    for m in matches: print(f"var {v} = {m};")
