import re

with open('trips_logic_v5.js', 'r', encoding='utf-8') as f:
    js = f.read()

start_str = "            // Cập nhật: Luôn cho phép ghép tối đa lên xe 5T (4900kg / 26CBM) để giảm số chuyến"
end_str = "            solutionGreedy.push(chunk);"

start_idx = js.find(start_str)
end_idx = js.find(end_str)

if start_idx == -1 or end_idx == -1:
    print("Could not find start or end strings")
else:
    new_loop = """            // Priority 3: Trường hợp có Siêu thị nào có lượng hàng = 2 xe 1t9, có thể sắp xe 5 tấn
            let chunkMaxW = 1900;
            let chunkMaxV = 14;
            // Nếu siêu thị mỏ neo vượt quá 1 xe 1.9T thì nâng lên xe 5T
            if (cw > 1900 || cv > 14) {
                chunkMaxW = 4900;
                chunkMaxV = 26;
            }

            let limit = 15; // Mới nhất: Chỉ sử dụng xe 1.9 Tấn để giao thẳng, tối đa là 15 điểm giao
            let added = true;
            while (added && chunk.length < limit) {
                added = false;
                let nearestIdx = -1, minDist = Infinity;
                for (let i = 0; i < remaining.length; i++) {
                    const p = remaining[i];
                    
                    if (cw + (p.weight || 0) <= chunkMaxW && cv + (p.volume || 0) <= chunkMaxV) {
                        const d = calculateDistance(chunk[chunk.length - 1].coords, p.coords);
                        if (d < minDist) { minDist = d; nearestIdx = i; }
                    }
                }
                if (nearestIdx !== -1) {
                    const p = remaining[nearestIdx];
                    cw += p.weight || 0; cv += p.volume || 0;
                    chunk.push(p);
                    remaining.splice(nearestIdx, 1);
                    added = true;
                }
            }
"""
    new_js = js[:start_idx] + new_loop + js[end_idx:]
    with open('trips_logic_v5.js', 'w', encoding='utf-8') as f:
        f.write(new_js)
    print("Replaced successfully!")
