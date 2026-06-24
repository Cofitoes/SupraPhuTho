import sys
with open('demo.html', 'r', encoding='utf-8') as f:
    demo = f.read()

patch = '''console.error('Optimization run error:', err);
    document.body.innerHTML += '<div style="position:fixed; top:100px; left:0; right:0; background: purple; color: white; padding: 20px; z-index:9999; font-size: 20px;">CLICK HANDLER ERROR: ' + err.toString() + '<br>' + err.stack + '</div>';'''

demo = demo.replace("console.error('Optimization run error:', err);", patch)
demo = demo.replace('trips_logic_v6.js?v=10', 'trips_logic_v6.js?v=11')

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(demo)

print('Patched demo.html catch block')
