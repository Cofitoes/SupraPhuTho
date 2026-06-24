import re, os
html=open('index.html', encoding='utf-8').read()
scripts=re.findall(r'<script.*?src=[\'"]([^\'"]+)[\'"]', html)
scripts = [s.split('?')[0] for s in scripts]
files=[f for f in os.listdir('.') if f.endswith('.js')]
unused=set(files)-set(scripts)
print('Loaded:', scripts)
print('Unused JS:', unused)
