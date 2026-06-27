import os

html_files = [
    r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
    r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
]

for f_path in html_files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        old_block = """        // Xóa hoàn toàn dữ liệu ngày 24/06/2026 ra khỏi bộ nhớ trang web
        if (typeof BOOKING_DELIVERY_POINTS !== 'undefined') {
            BOOKING_DELIVERY_POINTS = BOOKING_DELIVERY_POINTS.filter(x => x.date !== '2026-06-24');
        }
        if (typeof vercelBooking !== 'undefined') {
            vercelBooking = vercelBooking.filter(x => x.date !== '2026-06-24');
        }
        if (typeof BOOKING_SUMMARY !== 'undefined') {
            BOOKING_SUMMARY = BOOKING_SUMMARY.filter(x => x.date !== '2026-06-24');
        }
        if (typeof adhocBookings !== 'undefined') {
            adhocBookings = adhocBookings.filter(x => x.date !== '2026-06-24');
        }
        if (typeof adhocSummary !== 'undefined') {
            adhocSummary = adhocSummary.filter(x => x.date !== '2026-06-24');
        }"""
        
        new_block = """        // Xóa hoàn toàn dữ liệu ngày 24/06/2026 ra khỏi bộ nhớ trang web
        if (typeof BOOKING_DELIVERY_POINTS !== 'undefined') {
            const filtered = BOOKING_DELIVERY_POINTS.filter(x => x.date !== '2026-06-24');
            BOOKING_DELIVERY_POINTS.length = 0;
            BOOKING_DELIVERY_POINTS.push(...filtered);
        }
        if (typeof vercelBooking !== 'undefined') {
            const filtered = vercelBooking.filter(x => x.date !== '2026-06-24');
            vercelBooking.length = 0;
            vercelBooking.push(...filtered);
        }
        if (typeof BOOKING_SUMMARY !== 'undefined') {
            const filtered = BOOKING_SUMMARY.filter(x => x.date !== '2026-06-24');
            BOOKING_SUMMARY.length = 0;
            BOOKING_SUMMARY.push(...filtered);
        }
        if (typeof adhocBookings !== 'undefined') {
            const filtered = adhocBookings.filter(x => x.date !== '2026-06-24');
            adhocBookings.length = 0;
            adhocBookings.push(...filtered);
        }
        if (typeof adhocSummary !== 'undefined') {
            const filtered = adhocSummary.filter(x => x.date !== '2026-06-24');
            adhocSummary.length = 0;
            adhocSummary.push(...filtered);
        }"""
        
        content = content.replace(old_block, new_block)
        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched const filters in: {f_path}")
