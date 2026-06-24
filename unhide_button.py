import sys
with open('demo.html', 'r', encoding='utf-8') as f:
    demo = f.read()

demo = demo.replace('id="btn-run-optimization" style="display: none;"', 'id="btn-run-optimization" style="display: inline-block;"')
demo = demo.replace('trips_logic_v6.js?v=5', 'trips_logic_v6.js?v=6')

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(demo)

print('Patched button display')
