import logging
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from retrying import retry
from bs4 import BeautifulSoup

field = "1_baocao2_test"
download_dir = "download_" + field
os.makedirs(download_dir, exist_ok=True)

log_file_dir = "download_file_log"
os.makedirs(log_file_dir, exist_ok=True)
log_file = os.path.join(log_file_dir, f"Save_{field}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode="w", encoding="utf-8")
    ]
)

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
    })
    return driver

cookies = [
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '4C262F512F9A0CB533D38ED63A151092043D27B355189316B43E4DB20816CE30C2E41289113774B996AF26FB95E21374B7CB8ED0D14885DAEE4F01181D277436117255016CBAC63942D4392C4AD1D5A77A8A7B2E31C7A0E4A17FE124C28A33126BE1251365F3F7E6813CD8BEA807375499FE62746CD3F5FE2E0FEA93BC66E09D88F99E15EC08FC4622B3F84558DFA522AA2E35BB8D5A070A1C6024B1B20705A7C1568A6E1FC2522837F7CF1E6A27E00C3F6FF3D87174B5857EB6D69566EDE2A017FECEAA2528E92D884ED712', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'x4khck23viz0ptnhjfk2ji5c', 'domain': 'thuvienphapluat.vn'}
]

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = None
    try:
        driver = create_driver()
        base_url = "https://thuvienphapluat.vn"
        driver.get(base_url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning(f"Could not add cookie: {e}")
        driver.refresh()

        full_url = f"{url}" if url.startswith("http") else f"{base_url}{url}"
        driver.get(full_url)

        delay = random.uniform(3, 6)
        logging.info(f"⏳ Waiting {delay:.2f}s for user emulation...")
        time.sleep(delay)

        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.0))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        except Exception:
            pass

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc, div.col-md-12.py-4"))
            )
        except Exception:
            screenshot_path = f"{download_dir}/error_file_{index}.png"
            driver.save_screenshot(screenshot_path)
            logging.error(f"❌ Main content not found at {full_url} - saved image error {screenshot_path}")
            return False

        try:
            try:
                content_div = driver.find_element(By.CSS_SELECTOR, "div#tab1.contentDoc")
            except:
                content_div = driver.find_element(By.CSS_SELECTOR, "div.col-md-12.py-4")
            html_content = content_div.get_attribute("outerHTML")
        except Exception:
            html_content = driver.page_source

        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        doc_id_with_ext = url.rstrip("/").split("/")[-1]
        doc_id, _ = os.path.splitext(doc_id_with_ext)
        file_path = os.path.join(download_dir, f"{index + 1}_{doc_id}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

        logging.info(f"Saved txt: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Error saving document TXT {index}: {e}")
        if driver is not None:
            driver.save_screenshot(f"{download_dir}/error_file_{index}.png")
        return False
    finally:
        if driver is not None:
            driver.quit()

def main():
    with open('./link_downloads/file_link_download_baocao_full.txt', 'r', encoding='utf-8') as file:
        download_urls = [
            line.strip()
            for line in file
            if line.strip().startswith("https://thuvienphapluat.vn/")
        ]

    logging.info(f"Total {len(download_urls)} links found in {field}.txt")

    max_workers = 5
    start_index = 0
    batch_size = 8

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
                    res = future.result()
                except Exception as e:
                    logging.error(f"Failed to process {url}: {e}")

        delay = random.uniform(5, 8)
        logging.info(f"⏳ {delay:.2f}s between batches...")
        time.sleep(delay)

    logging.info("All TXT content saved.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")