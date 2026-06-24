import asyncio
from playwright.async_api import async_playwright
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_tabs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on('console', lambda msg: print(f'Console {msg.type}: {msg.text}'))
        
        file_path = os.path.abspath('demo.html')
        
        try:
            await page.goto(f'file:///{file_path}', timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            await page.evaluate('''() => {
                // Mock 1000 points! This will create ~100 clusters!
                window.BOOKING_DELIVERY_POINTS = Array.from({length: 1000}).map((_, i) => ({
                    id: 'S' + i,
                    name: 'Store ' + i,
                    date: '24/06/2026',
                    weight: 100 + Math.random() * 200,
                    volume: 0.5 + Math.random() * 1,
                    address: 'HCM',
                    coords: { lat: 10.762622 + Math.random()*0.1, lng: 106.660172 + Math.random()*0.1 }
                }));
                
                document.getElementById('global-date-filter').value = '2026-06-24';
                
                console.time('Full click');
                const btn = document.querySelector("nav li[data-tab='pending-deliveries']");
                
                const origGenerateTrips = window.generateTrips;
                window.generateTrips = function() {
                    console.time('generateTrips');
                    const res = origGenerateTrips.apply(this, arguments);
                    console.timeEnd('generateTrips');
                    return res;
                };
                
                btn.click();
                console.timeEnd('Full click');
            }''')
            
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f'Exception: {e}')
            
        await browser.close()

asyncio.run(test_tabs())
