import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os


# Field to name the file
field = "hinhsu"

# Number of pages to crawl
start_page = 1
total_pages = 28

#DÂN SỰ 25

output_file = f"file_link_download_{field}.txt"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(output_file + ".log", mode="w")
    ]
)

# Chrome headless setup
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-images")  # Disable images to speed up loading
chrome_options.add_argument("--blink-settings=imagesEnabled=false")
chrome_options.add_argument("--window-size=1920,1080")

# Cookies login
cookies = [
    {'name': 'UserLN', 'value': 'c9c5aGJtZE1ZVzVRYUhWdmJtZDhNWHcyTXpnNE1qWXpPVEkzT1RVeE1qVTBNamU0', 'domain': 'lawnet.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'gyfj33l3kvon40qxih43v043', 'domain': 'lawnet.vn'},
    {'name': 'TVPLCOM.AUTH', 'value': 'CF3B986FDFD7E968576113CFFF855498CE8ACAED53B96BE8CA13A0A73F068137D800D72DD26487305D1AE1592568008111A7BFE7C909577474C44F2460A9994A741305748F6ECC63283C3AE7A05BAC28492E2927E224D3DE0B51642D86491E8F0C73BA1450021FE050D01CC948793EEB16A96DC334FC8ECDE2969BC6C007A04CDCBCB9480CC779697D7D14F69C1A20CA', 'domain': 'lawnet.vn'}
]

try:
    driver = webdriver.Chrome(options=chrome_options)
    base_url = "https://lawnet.vn"
    driver.get(base_url)

    # Add cookies
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

    download_urls = []

    for page_number in range(start_page, total_pages + 1):
        try:
            page_url = f"https://lawnet.vn/van-ban-phap-luat?SearchModelType=0&Title=V%C4%83n%20b%E1%BA%A3n%20ph%C3%A1p%20lu%E1%BA%ADt&page={page_number}&DescEN=&DescVN=&KeywordEN=&KeywordVN=&keyword=&area=&lan=1&match=false&matchTemp=false&type=0&typeTemp=&field=31&organ=&status=1&bday=13/05/1945&eday=13/05/2025&bdayCHL=&edayCHL=&sort=0&signer=&isscan=&istranslated="
            # Update url filter field from web, change page={page_number}
            driver.get(page_url)

            # Get link
            links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.pl-0.pl-md-2.pr-2.pr-md-0 a.text-tvpl-black")
                )
            )

            for link in links:
                href = link.get_attribute("href")
                if href:
                    download_urls.append(href)
                    logging.info(f"Found link: {href}")

        except Exception as e:
            logging.error(f"Error at page {page_number}: {e}")

    download_dir = "link_downloads"
    os.makedirs(download_dir, exist_ok=True) 
    file_path = os.path.join(download_dir, output_file)
    with open(file_path, "w", encoding="utf-8") as f:
        for url in download_urls:
            f.write(url + "\n")

    # Wait before processing next document
    wait_seconds = 12
    logging.info(f"Waiting {wait_seconds} seconds before next download...")
    time.sleep(wait_seconds)

    logging.info(f"🎉 Done. Total {len(download_urls)} links saved to {output_file}")

except Exception as e:
    logging.critical(f"❌ Fatal error: {e}")

finally:
    if 'driver' in locals():
        driver.quit()
