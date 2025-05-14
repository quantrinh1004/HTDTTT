import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from retrying import retry
import threading
from bs4 import BeautifulSoup

# Field to name the file
field = "baohiem"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("Save" + field + ".log", mode="w")
    ]
)

# Setup Chrome options for headless execution
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-images")  # Disable images to speed up loading
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,  # Disable images
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    return webdriver.Chrome(options=chrome_options)

# Create download folder
download_dir = "download_" + field
os.makedirs(download_dir, exist_ok=True)

# Cookies login
cookies = [
    {'name': 'UserLN', 'value': 'c9c5aGJtZE1ZVzVRYUhWdmJtZDhNWHcyTXpnNE1qWXpPVEkzT1RVeE1qVTBNamU0', 'domain': 'lawnet.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'gyfj33l3kvon40qxih43v043', 'domain': 'lawnet.vn'},
    {'name': 'TVPLCOM.AUTH', 'value': 'CF3B986FDFD7E968576113CFFF855498CE8ACAED53B96BE8CA13A0A73F068137D800D72DD26487305D1AE1592568008111A7BFE7C909577474C44F2460A9994A741305748F6ECC63283C3AE7A05BAC28492E2927E224D3DE0B51642D86491E8F0C73BA1450021FE050D01CC948793EEB16A96DC334FC8ECDE2969BC6C007A04CDCBCB9480CC779697D7D14F69C1A20CA', 'domain': 'lawnet.vn'}
]


# Thread-local storage for driver instances
thread_local = threading.local()

def get_driver():
    if not hasattr(thread_local, "driver"):
        thread_local.driver = create_driver()
        base_url = "https://lawnet.vn"
        thread_local.driver.get(base_url)
        for cookie in cookies:
            thread_local.driver.add_cookie(cookie)
        thread_local.driver.refresh()
    return thread_local.driver

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = get_driver()
    try:
        full_url = f"https://lawnet.vn{url}" if not url.startswith("http") else url
        driver.get(full_url)

        # Dynamic wait for content
        WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-12.py-4"))
        )

        # Get content
        content_elements = driver.find_elements(By.CSS_SELECTOR, "div.col-md-12.py-4")
        html_content = "\n\n".join([el.get_attribute("outerHTML") for el in content_elements])

        # Parser html to txt
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        # Save content
        doc_id_with_ext = url.rstrip("/").split("/")[-1]
        doc_id, _ = os.path.splitext(doc_id_with_ext) 
        file_path = os.path.join(download_dir, f"{index + 0}_{doc_id}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

        logging.info(f"✅ Saved txt: {file_path}")
        return True

    except Exception as e:
        logging.error(f"❌ Error saving document TXT {index}: {e}")
        driver.save_screenshot(f"error_file_{index}.png")
        raise

def main():
    # Read URLs from file
    with open('link_downloads/file_link_download_baohiem.txt', 'r', encoding='utf-8') as file:
        download_urls = [
            line.strip()
            for line in file
            if line.strip().startswith("https://lawnet.vn/")
        ]

    logging.info(f"Total {len(download_urls)} links found in" + field + ".txt")

    # Process URLs in parallel
    max_workers = 5  # Adjust based on system capacity
    start_index = 0 # Chane if need
    batch_size = 8  # Process in batches to manage memory

    for batch_start in range(start_index, len(download_urls), batch_size):
        batch_urls = download_urls[batch_start:batch_start + batch_size]
        logging.info(f"Processing batch {batch_start} to {batch_start + len(batch_urls)}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(download_content, url, i): url
                for i, url in enumerate(batch_urls, start=batch_start)
            }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Failed to process {url}: {e}")

        # Optional: Small delay between batches to avoid server overload
        time.sleep(12)

    logging.info("🎉 All TXT content saved.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
    finally:
        # Clean up all drivers
        if hasattr(thread_local, "driver"):
            thread_local.driver.quit()
# Saved txt: download_dat_dai_all_txt2_a1_3_2/12957_Cong-van-3344-TCT-CS-mien-giam-tien-thue-dat-111F9.html.txt