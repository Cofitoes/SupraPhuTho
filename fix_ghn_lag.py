import re

def fix_ghn_lag(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject global maps for Booking and Concung
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
            window.GlobalBookingMapById = {}; \\
            window.GlobalBookingMapByName = {}; \\
            if (typeof BOOKING_DELIVERY_POINTS !== "undefined") { \\
                BOOKING_DELIVERY_POINTS.forEach(dp => { \\
                    if (dp.id) window.GlobalBookingMapById[dp.id] = dp; \\
                    if (dp.name) window.GlobalBookingMapByName[dp.name] = dp; \\
                }); \
            } \\
            window.GlobalConcungMap = {}; \\
            if (typeof concungData !== "undefined") { \\
                concungData.forEach(item => { \\
                    if (item["MÃ CỬA HÀNG"] || item["MA CA HA?NG"]) window.GlobalConcungMap[item["MÃ CỬA HÀNG"] || item["MA CA HA?NG"]] = item; \\
                    if (item["MÃ BUFF"] || item["MA BUFF"]) window.GlobalConcungMap[item["MÃ BUFF"] || item["MA BUFF"]] = item; \\
                }); \\
            } \\
        </scr' + 'ipt>');
"""
    # Replace the old injection
    content = re.sub(
        r"document\.write\('<script> \\\s*window\.GlobalStoreMapById = \{\};.*?</scr' \+ 'ipt>'\);",
        injection.strip().replace('\\', '\\\\'), # Double backslash to avoid python regex evaluating \n inside replacement string if any
        content,
        flags=re.DOTALL
    )

    # 2. Optimize the Fallback logic inside storesList.forEach
    content = re.sub(
        r"let matched = BOOKING_DELIVERY_POINTS\.find\(dp => dp\.id && s\.id && dp\.id == s\.id\);\s*if \(!matched\) matched = BOOKING_DELIVERY_POINTS\.find\(dp => dp\.name === s\.name\);",
        r"let matched = window.GlobalBookingMapById[s.id] || window.GlobalBookingMapByName[s.name];",
        content
    )

    # 3. Optimize the concung fallback logic
    content = re.sub(
        r"const matched = concungData\.find\(item => [^;]+\);",
        r"const matched = window.GlobalConcungMap[b];",
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed GHN lag in {filepath}")

fix_ghn_lag('index.html')
fix_ghn_lag('demo.html')
