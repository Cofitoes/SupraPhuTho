import re

with open('trips_logic_v5.js', 'r', encoding='utf-8') as f:
    js = f.read()

start_str = "            const isValidChunk = (chunk) => {"
end_str = "            let bestScore = evaluateSolution(clusters);"

start_idx = js.find(start_str)
end_idx = js.find(end_str)

if start_idx == -1 or end_idx == -1:
    print("Could not find start or end strings")
else:
    new_func = """            const isValidChunk = (chunk) => {
                if (chunk.length === 0) return true;
                if (chunk.length > 15) return false; // Mới nhất: tối đa là 15 điểm giao
                let w = 0, v = 0, hasBigStore = false;
                for (let i = 0; i < chunk.length; i++) {
                    w += chunk[i].weight || 0;
                    v += chunk[i].volume || 0;
                    if ((chunk[i].weight || 0) > 1900 || (chunk[i].volume || 0) > 14) hasBigStore = true;
                }
                let maxW = hasBigStore ? 4900 : 1900;
                let maxV = hasBigStore ? 26 : 14;
                return w <= maxW && v <= maxV;
            };

"""
    new_js = js[:start_idx] + new_func + js[end_idx:]
    with open('trips_logic_v5.js', 'w', encoding='utf-8') as f:
        f.write(new_js)
    print("Replaced isValidChunk successfully!")
