import re
import sys

def optimize_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject global cache map initialization after trips_logic_v5.js
    injection = r"""
        document.write('<script src="trips_logic_v5.js?v=' + cb + '" charset="UTF-8"></scr' + 'ipt>');
        document.write('<script> \
            window.GlobalStoreMapById = {}; \
            window.GlobalStoreMapByName = {}; \
            if (typeof STORE_LIST_DATA !== "undefined") { \
                STORE_LIST_DATA.forEach(s => { \
                    if (s.id) window.GlobalStoreMapById[s.id] = s; \
                    if (s.name) window.GlobalStoreMapByName[s.name] = s; \
                }); \
            } \
        </scr' + 'ipt>');
"""
    if "window.GlobalStoreMapById" not in content:
        content = re.sub(
            r"document\.write\('<script src=\"trips_logic_v5\.js\?v='\s*\+\s*cb\s*\+\s*'\" charset=\"UTF-8\"></scr'\s*\+\s*'ipt>'\);",
            injection.strip(),
            content
        )

    # 2. Optimize GHN renderTable (isGxt loop)
    # Original: const store = STORE_LIST_DATA.find(s => s.id === sCode || (s.name && s.name.includes(sCode)));
    # Replacement: const store = window.GlobalStoreMapById[sCode] || window.GlobalStoreMapByName[sCode]; // approximate
    # Let's replace the block precisely.
    content = re.sub(
        r"const store = STORE_LIST_DATA\.find\(s => s\.id === sCode \|\| \(s\.name && s\.name\.includes\(sCode\)\)\);",
        r"const store = window.GlobalStoreMapById[sCode] || window.GlobalStoreMapByName[sCode] || (typeof STORE_LIST_DATA !== 'undefined' ? STORE_LIST_DATA.find(s => s.id === sCode || (s.name && s.name.includes(sCode))) : null);",
        content
    )

    # 3. Optimize STORE_GHN_SO_DATA parsing
    # Original: const st = STORE_LIST_DATA.find(s => s.name === storeName);
    content = re.sub(
        r"const st = STORE_LIST_DATA\.find\(s => s\.name === storeName\);",
        r"const st = window.GlobalStoreMapByName[storeName];",
        content
    )

    # 4. Optimize renderStoreList store mapping
    # Original:
    # const storeMap = {};
    # if (typeof STORE_LIST_DATA !== 'undefined') {
    #     STORE_LIST_DATA.forEach(s => { storeMap[s.id] = s; });
    # }
    # We can replace the fallback inside the loop:
    # let store = storeMap[id];
    # if (!store && bInfo && typeof STORE_LIST_DATA !== 'undefined') {
    #     store = STORE_LIST_DATA.find(s => s.name === bInfo.name);
    # }
    content = re.sub(
        r"let store = storeMap\[id\];\s*if \(!store && bInfo && typeof STORE_LIST_DATA !== 'undefined'\) \{\s*store = STORE_LIST_DATA\.find\(s => s\.name === bInfo\.name\);\s*\}",
        r"let store = storeMap[id];\n                  if (!store && bInfo) {\n                      store = window.GlobalStoreMapByName[bInfo.name];\n                  }",
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Optimized {filepath}")

def optimize_trips_logic(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Original capacity loop:
    # let remW = cw, remV = cv;
    # remaining.forEach(p => { remW += (p.weight || 0); remV += (p.volume || 0); });
    # Optimized: We pre-calculate total remaining weight/volume outside the `while` loop, 
    # and just subtract when an item is removed.
    # Actually, remaining is filtered on every iteration. 
    # The array remaining has length ~100-200. forEach is fast.
    # To be extremely safe without breaking logic, we can just rewrite it to a standard fast loop instead of forEach closure.
    # Or precalculate it. Let's just use a basic for loop for speed if needed, but JS engines optimize forEach anyway.
    # Let's replace `remaining.forEach(p => ...)` with a fast for-loop.
    fast_loop = """for (let i = 0; i < remaining.length; i++) {
                  remW += (remaining[i].weight || 0);
                  remV += (remaining[i].volume || 0);
              }"""
    content = re.sub(
        r"remaining\.forEach\(p => \{ remW \+= \(p\.weight \|\| 0\); remV \+= \(p\.volume \|\| 0\); \}\);",
        fast_loop,
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Optimized {filepath}")

if __name__ == '__main__':
    optimize_html('index.html')
    optimize_html('demo.html')
    optimize_trips_logic('trips_logic_v5.js')
