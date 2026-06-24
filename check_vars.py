import sys
import re

html = open('demo.html', encoding='utf-8').read()
vars = ['list', 'tripSelect', 'mqBody', 'btn', 'statusCell', 'tbody', 'reqBody', 'fillRateBody', 'ghnTripsBody', 'container', 'otpBody', 'plateSelect', 'orderLookupBody', 'tr', 'logoutBtn', 'tableBody', 'costTable', 'changePassBtn']

for v in vars:
    match = re.search(r'const ' + v + r'\s*=\s*(.*?);', html)
    if match:
        print(f'{v}: {match.group(1)}')
    else:
        # maybe let?
        match = re.search(r'let ' + v + r'\s*=\s*(.*?);', html)
        if match:
            print(f'{v} (let): {match.group(1)}')
        else:
            print(f'{v}: NOT FOUND')
