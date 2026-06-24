with open('demo.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('src="trips_logic_v5.js?v=2"', 'src="trips_logic_v5.js?v=3"')

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(html)
