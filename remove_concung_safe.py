import sys
import re

html = open('demo.html', encoding='utf-8').read()

# Remove the concung_data.js script tag entirely
html = html.replace("        document.write('<script src=\"concung_data.js?v=' + cb + '\"></scr' + 'ipt>');\n", "")

# Remove the 'concung' li tab
html = re.sub(r'<li[^>]*data-tab="concung"[^>]*>.*?</li>', '', html, flags=re.DOTALL)

# Remove the concung section
start = html.find('<section id="concung"')
if start != -1:
    end = html.find('</section>', start)
    if end != -1:
        end += len('</section>')
        html = html[:start] + html[end:]

# Handle loadConcungData function
func_start = html.find('async function loadConcungData() {')
if func_start != -1:
    brace_count = 0
    func_end = -1
    for i in range(func_start, len(html)):
        if html[i] == '{':
            brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                func_end = i + 1
                break
    if func_end != -1:
        html = html[:func_start] + html[func_end:]

# Remove loadConcungData(); call
html = html.replace('loadConcungData();\n', '')
html = html.replace('await loadConcungData();\n', '')

# Remove reference to concungData
html = re.sub(r"if\s*\(\s*typeof\s+concungData\s*!==\s*'undefined'\s*\)\s*\{\s*allData\s*=\s*allData\.concat\(concungData\);\s*\}\n?", "", html)

open('demo.html', 'w', encoding='utf-8').write(html)
open('index.html', 'w', encoding='utf-8').write(html)
