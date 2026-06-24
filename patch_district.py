import sys, re

def patch():
    with open('demo.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update headers
    # Find <th>Tỉnh/Thành Phố</th> and insert <th>Huyện/Xã</th> before it in the store list table
    html = re.sub(
        r'(<th>Địa Chỉ</th>\s*<th>Tỉnh/Thành Phố</th>)',
        r'<th>Địa Chỉ</th>\n                                <th>Huyện/Xã</th>\n                                <th>Tỉnh/Thành Phố</th>',
        html
    )

    # 3. Update table row
    # We need to insert <td><strong>${p.district || ''}</strong></td> before <td><strong>${province}</strong></td>
    html = re.sub(
        r'(<td.*?title=\"\$\{p\.address \|\| \'\'\}\">\$\{p\.address \|\| \'\'\}</td>\s*)(<td><strong>\$\{province\}</strong></td>)',
        r'\1<td><strong>${p.district || \'\'}</strong></td>\n                        \2',
        html
    )

    with open('demo.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Patched demo.html successfully for Huyện/Xã.")

patch()
