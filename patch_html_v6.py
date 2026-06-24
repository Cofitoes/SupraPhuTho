import re

with open('demo.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'trips_logic_v5\.js\?v=\d+', 'trips_logic_v6.js?v=1', html)
html = html.replace('trips_logic_v5.js', 'trips_logic_v6.js?v=1')

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(html)
