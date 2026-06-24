import re

def fix_all(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix the document.write block
    # In the original file, it looks like:
    #             window.GlobalConcungMap = {}; \
    #             if (typeof concungData !== "undefined") { \
    #                 concungData.forEach(item => { \
    #                     if (item["MÃ CỬA HÀNG"] || item["MA CA HA?NG"]) window.GlobalConcungMap[item["MÃ CỬA HÀNG"] || item["MA CA HA?NG"]] = item; \
    #                     if (item["MÃ BUFF"] || item["MA BUFF"]) window.GlobalConcungMap[item["MÃ BUFF"] || item["MA BUFF"]] = item; \
    #                 }); \
    #             } \
    #         </scr' + 'ipt>');
    
    # We want to replace it to just properly close the script tag without concung stuff
    # We can match up to window.GlobalConcungMap and replace everything up to </scr' + 'ipt>');
    content = re.sub(
        r"window\.GlobalConcungMap = \{\}; \\\n\s*if \(typeof concungData !== \"undefined\"\) \{ \\\n\s*concungData\.forEach\(item => \{ \\\n.*?\}\); \\\n\s*\} \\\n",
        "", content, flags=re.DOTALL
    )

    # 2. Fix concung_data.js inclusion
    content = re.sub(r"document\.write\('<script src=\"concung_data\.js\?v=' \+ cb \+ '\" charset=\"UTF-8\"></scr' \+ 'ipt>'\);\n\s*", "", content)

    # 3. Fix the standalone if returning false
    content = re.sub(
        r"if \(typeof concungData !== 'undefined'\) \{\s*const b = p\.buff \|\| p\.Buff \|\| p\.BUFF;\s*if \(b\) \{\s*const matched = window\.GlobalConcungMap\[b\];\s*if \(matched && matched\['Trạng thái hệ thống'\] === 'Giao hàng thành công'\) \{\s*return false;\s*\}\s*\}\s*\}",
        "", content
    )
    # also with weird characters
    content = re.sub(
        r"if \(typeof concungData !== 'undefined'\) \{\s*const b = p\.buff \|\| p\.Buff \|\| p\.BUFF;\s*if \(b\) \{\s*const matched = window\.GlobalConcungMap\[b\];\s*if \(matched && matched\['Trng thAi h th`ng'\] === 'Giao hAng thAnh cA'ng'\) \{\s*return false;\s*\}\s*\}\s*\}",
        "", content
    )

    # 4. Fix else if for doList
    content = re.sub(
        r"\} else if \(searchName && typeof concungData !== 'undefined'\) \{\s*const matched = window\.GlobalConcungMap\[b\];\s*if \(matched && \(matched\['[^']+\] \|\| matched\['[^']+\]\)\) \{\s*doList\.push\(matched\['[^']+\] \|\| matched\['[^']+\]\);\s*\}\s*\}",
        "}", content
    )

    # 5. Fix else if for ghnList
    content = re.sub(
        r"\} else if \(b && typeof concungData !== 'undefined'\) \{\s*const matched = window\.GlobalConcungMap\[b\];\s*if \(matched && \(matched\['[^']+\] \|\| matched\['[^']+\]\)\) \{\s*ghnList\.push\(matched\['[^']+\] \|\| matched\['[^']+\]\);\s*\}\s*\}",
        "}", content
    )

    # 6. Fix concat
    content = re.sub(
        r"if \(typeof concungData !== 'undefined'\) \{\s*allData = allData\.concat\(concungData\);\s*\}",
        "", content
    )

    # 7. HTML
    content = re.sub(
        r"<!-- 1\. Ch\?n NgAy & MA `n ConCung -->\s*<div class=\"form-group\" style=\"flex:1;\">\s*<label for=\"incident-concung-code\">\s*<svg.*?</svg>\s*\?n ConCung</label>\s*<input type=\"text\" id=\"incident-concung-code\" class=\"actual-time-input\"\s*style=\"[^\"]*\"\s*placeholder=\"[^\"]*\">\s*</div>",
        "<!-- 1. Chọn Ngày -->", content, flags=re.DOTALL
    )

    content = re.sub(r"const concungCodeVal = document\.getElementById\('incident-concung-code'\)\.value\.trim\(\);\n\s*", "", content)
    content = re.sub(r"concungCode: concungCodeVal,\n\s*", "", content)
    content = re.sub(r"document\.getElementById\('incident-concung-code'\)\.value = \"\";\n\s*", "", content)
    
    content = re.sub(r"<th>MA `n ConCung</th>\n\s*", "", content)
    content = re.sub(r"<td><strong style=\"color: var\(--secondary\);\}>\$\{item\.concungCode \|\| '-'}</strong></td>\n\s*", "", content)
    content = content.replace("<td><strong style=\"color: var(--secondary);\">${item.concungCode || '-'}</strong></td>\n", "")

    content = content.replace("<title>Logistics Hub | Quản lý vận hành</title>", "<title>Supra Phú Thọ | Quản Lý Vận Tải Thông Minh</title>")
    content = content.replace("<title>Logistics Hub | Qun lA v-n hAnh</title>", "<title>Supra Phú Thọ | Quản Lý Vận Tải Thông Minh</title>")
    content = content.replace("Logistics Hub Manager", "GHN Manager")
    content = content.replace("Logistics Hub Staff", "GHN Staff")
    content = content.replace("logistics_local_users", "supra_local_users")
    content = content.replace("logistics_incidents", "supra_incidents")
    content = content.replace("logisticsupdate://", "supraupdate://")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

fix_all('index.html')
fix_all('demo.html')

