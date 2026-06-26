import sys
with open('trips_logic_v6.js', 'r', encoding='utf-8') as f:
    code = f.read()

patch = '''
    if (gxtPoints.length === 0 && directPoints.length === 0) {
        console.warn('DEBUG: Both gxtPoints and directPoints are EMPTY! DELIVERY_POINTS length: ' + DELIVERY_POINTS.length);
    }
'''

code = code.replace('let directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT !== true);', 
    'let directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT !== true);\n' + patch)

with open('trips_logic_v6.js', 'w', encoding='utf-8') as f:
    f.write(code)
print('Patched logic for empty points')
