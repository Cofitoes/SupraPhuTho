import sys
with open('trips_logic_v6.js', 'r', encoding='utf-8') as f:
    code = f.read()

patch = """
window.safeGenerateTrips = function() {
    try {
        return generateTrips();
    } catch(e) {
        document.body.innerHTML += '<div style="position:fixed; top:0; left:0; right:0; background: red; color: white; padding: 20px; z-index:9999; font-size: 20px;">' + e.toString() + '<br>' + e.stack + '</div>';
        return [];
    }
}
"""
if 'safeGenerateTrips' not in code:
    with open('trips_logic_v6.js', 'a', encoding='utf-8') as f:
        f.write('\n' + patch)
        
with open('demo.html', 'r', encoding='utf-8') as f:
    demo = f.read()
demo = demo.replace('generateTrips()', 'safeGenerateTrips()')
demo = demo.replace('trips_logic_v6.js?v=4', 'trips_logic_v6.js?v=5')
with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(demo)
print('Patched for error display')
