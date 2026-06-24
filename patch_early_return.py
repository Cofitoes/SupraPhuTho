import sys
with open('demo.html', 'r', encoding='utf-8') as f:
    demo = f.read()

demo = demo.replace('if (window.lastGeneratedType === targetType) {\nreturn; // Already generated for this type\n}', '// Removed early return')
demo = demo.replace('trips_logic_v6.js?v=7', 'trips_logic_v6.js?v=8')

with open('demo.html', 'w', encoding='utf-8') as f:
    f.write(demo)

print('Patched early return')
