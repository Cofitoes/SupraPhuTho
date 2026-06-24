from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless=new')
options.add_argument('--log-level=0')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(options=options)
url = 'file:///G:/My%20Drive/Training%20AI/Supra%20Ph%C3%BA%20Th%E1%BB%8D/demo.html'
driver.get(url)
time.sleep(2)

logs = driver.get_log('browser')
for log in logs:
    if log['level'] in ['SEVERE', 'WARNING', 'INFO']:
        print(f"{log['level']}: {log['message']}")

driver.quit()
