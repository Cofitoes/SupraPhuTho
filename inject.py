def optimize_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Inject global cache map initialization
    injection = """
        document.write('<script> \\
            window.GlobalStoreMapById = {}; \\
            window.GlobalStoreMapByName = {}; \\
            if (typeof STORE_LIST_DATA !== "undefined") { \\
                STORE_LIST_DATA.forEach(s => { \\
                    if (s.id) window.GlobalStoreMapById[s.id] = s; \\
                    if (s.name) window.GlobalStoreMapByName[s.name] = s; \\
                }); \\
            } \\
        </scr' + 'ipt>');
"""
    if "window.GlobalStoreMapById =" not in content:
        target = "document.write('<script src=\"data_ghn_so.js?v=' + cb + '\" charset=\"UTF-8\"></scr' + 'ipt>');"
        content = content.replace(target, target + injection)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

optimize_html('index.html')
optimize_html('demo.html')
print("Injected Global Map!")
