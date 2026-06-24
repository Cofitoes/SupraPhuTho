import sys

def patch():
    with open('demo.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update headers
    if '<th>Phân loại</th>' not in html:
        html = html.replace('<th>Tỉnh/Thành Phố</th>', '<th>Tỉnh/Thành Phố</th>\n                                <th>Phân loại</th>')

    # 2. Add variable definition
    old_var = 'let province = getProvinceFromNameOrAddress(p.name, p.address);'
    new_var = '''let province = getProvinceFromNameOrAddress(p.name, p.address);
                let phanLoai = p.isGXT ? '<span class=\"trip-status on-time\" style=\"font-size: 0.8rem; background: rgba(59, 130, 246, 0.1); color: #3b82f6;\"><i class=\"fas fa-truck-loading\"></i> Chuyển về GXT</span>' : '<span class=\"trip-status in-progress\" style=\"font-size: 0.8rem; background: rgba(16, 185, 129, 0.1); color: #10b981;\"><i class=\"fas fa-truck\"></i> Giao Thẳng</span>';'''
    if old_var in html and 'let phanLoai' not in html:
        html = html.replace(old_var, new_var)

    # 3. Add column to row
    old_row = '''<td><strong>${province}</strong></td>
                                <td>${mapLink}</td>'''
    new_row = '''<td><strong>${province}</strong></td>
                                <td>${phanLoai}</td>
                                <td>${mapLink}</td>'''
                                
    # Alternative old_row due to spacing
    import re
    if '<td>${phanLoai}</td>' not in html:
        html = re.sub(r'(<td><strong>\$\{province\}</strong></td>\s*)(<td>\$\{mapLink\}</td>)', r'\1<td>${phanLoai}</td>\n                                \2', html)

    with open('demo.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Patched demo.html successfully.")

patch()
