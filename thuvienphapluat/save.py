import os
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from retrying import retry
from bs4 import BeautifulSoup


# ======= Configuration =======
FIELD = "final_baocao"
DOWNLOAD_DIR = f"download_{FIELD}"
LOG_FILE_DIR = "download_file_log"
LOG_FILE = os.path.join(LOG_FILE_DIR, f"Save_{FIELD}.log")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_FILE_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    ]
)

# # ======= Cookies =======
# COOKIES = [
#     {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
#     {'name': 'thuvienphapluatnew', 'value': '9137EC1279A1921F03278A20A989C3D91210997D05DFA9AEB8AAE67D2B255CBD95FA9C55799498B7FC9B2B161D61A9E0BB008EF50B4245598698FA633FE1AE2082C7CDB097807FF21429C6B3039D48215002DE730FB4E9FE2DFDF073C15BE592236D9737E61D32E77B3AD60F079C94B0519AA753AC3289FF5D144C7EE7C196471837624268D570B2AAAA0BB69E4B310CBF8115FC8E37255894E2B79E84179AF761C778F6D5004A7142F2206876297B8F4AC5C272FB9BD89707CCAAED9FCEAC73C4892F84105A6B875A486ECE', 'domain': 'thuvienphapluat.vn'},
#     {'name': 'ASP.NET_SessionId', 'value': 'thrrpmphh3ku45s4sfrodxf5', 'domain': 'thuvienphapluat.vn'},
#     {'name': '_ga', 'value': 'GA1.1.1468916141.1751763821', 'domain': 'thuvienphapluat.vn'},
#     {'name': 'cf_clearance', 'value': 'hYwNkbdJ3lPKz5uSWu4P_qhPA7Cm_._oXXVhXre5o9Q-1751857673-1.2.1.1-4_GOWqjYQNNck9CSIVH1JLZWpRdGlnpI5K.nfsqjigNfjZeGVXAKaeTqFyfBVMCQ2UMJkpEEQqCMcTCXff2LjQl1TVfg326X8nkT3J5VHGIeTGLNAto5YkQvgToSxyA8JvbMbZwrur1moquzRgJ2OHJXHpSlrKb6QjAGtzfypY4lRc4phNmpHzrik2PRyLK9tflgwzLtVl0NhBO7gBejVm_eM8s_ICavXC2UWPAXcb8', 'domain': 'thuvienphapluat.vn'},
# ]

COOKIES = [
    {'name': 'G_ENABLED_IDPS', 'value': 'google', 'domain': 'thuvienphapluat.vn'},
    {'name': '__zlcmid', 'value': '1QXnRYh9ROt9ACR', 'domain': 'thuvienphapluat.vn'},
    {'name': 'Culture', 'value': 'vi', 'domain': 'thuvienphapluat.vn'},
    {'name': '3808CE', 'value': '5b564703-a89e-405b-8bd6-8af11692311d', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'thrrpmphh3ku45s4sfrodxf5', 'domain': 'thuvienphapluat.vn'},
    {'name': 'Cookie_VB', 'value': 'close', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ruirophaply-covi19', 'value': '7', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '9137EC1279A1921F03278A20A989C3D91210997D05DFA9AEB8AAE67D2B255CBD95FA9C55799498B7FC9B2B161D61A9E0BB008EF50B4245598698FA633FE1AE2082C7CDB097807FF21429C6B3039D48215002DE730FB4E9FE2DFDF073C15BE592236D9737E61D32E77B3AD60F079C94B0519AA753AC3289FF5D144C7EE7C196471837624268D570B2AAAA0BB69E4B310CBF8115FC8E37255894E2B79E84179AF761C778F6D5004A7142F2206876297B8F4AC5C272FB9BD89707CCAAED9FCEAC73C4892F84105A6B875A486ECE', 'domain': 'thuvienphapluat.vn'},
    {'name': 'dl_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtYzU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'memberga', 'value': 'HoangLanPhuong[Basic][3672270]', 'domain': 'thuvienphapluat.vn'},
    {'name': 'vqc', 'value': '0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'cf_clearance', 'value': 'hYwNkbdJ3lPKz5uSWu4P_qhPA7Cm_._oXXVhXre5o9Q-1751857673-1.2.1.1-4_GOWqjYQNNck9CSIVH1JLZWpRdGlnpI5K.nfsqjigNfjZeGVXAKaeTqFyfBVMCQ2UMJkpEEQqCMcTCXff2LjQl1TVfg326X8nkT3J5VHGIeTGLNAto5YkQvgToSxyA8JvbMbZwrur1moquzRgJ2OHJXHpSlrKb6QjAGtzfypY4lRc4phNmpHzrik2PRyLK9tflgwzLtVl0NhBO7gBejVm_eM8s_ICavXC2UWPAXcb8', 'domain': 'thuvienphapluat.vn'},
]


# ======= Functions =======
def create_driver():
    chrome_options = Options()

    # ❌ KHÔNG bật headless nếu bị phát hiện
    chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")

    # ✅ Dùng user-agent chuẩn trình duyệt phổ biến, KHÔNG có "Headless"
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    )

    # ❌ KHÔNG tắt hình ảnh để tránh bị nghi ngờ
    # chrome_options.add_argument("--blink-settings=imagesEnabled=false")

    # ✅ Tránh bật chế độ automation
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # ✅ Ngăn một số flag automation
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # ✅ Dùng prefs để tắt một số popup
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    # ✅ Khởi tạo driver
    driver = webdriver.Chrome(options=chrome_options)

    # ✅ Vô hiệu hóa navigator.webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3]
            });
        """
    })

    return driver


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = None
    try:
        driver = create_driver()
        base_url = "https://thuvienphapluat.vn"

        logging.info("Accessing homepage to set cookies...")
        driver.get(base_url)
        delay1 = random.uniform(3, 6)
        time.sleep(delay1)

        for cookie in COOKIES:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning(f"Could not add cookie: {e}")

        driver.refresh()
        driver.get("https://thuvienphapluat.vn/tra-cuu-phap-luat-moi.aspx")
        delay2 = random.uniform(3, 8)
        time.sleep(delay2)

        full_url = url if url.startswith("http") else f"{base_url}{url}"
        driver.get(full_url)

        delay = random.uniform(2, 6)
        logging.info(f"Waiting {delay:.2f}s for user emulation...")
        time.sleep(delay)

        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.0))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        except Exception:
            pass

        try:
            WebDriverWait(driver, random.uniform(8, 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc, div.col-md-12.py-4"))
            )
        except Exception:
            screenshot_path = os.path.join(DOWNLOAD_DIR, f"error_file_{index}.png")
            driver.save_screenshot(screenshot_path)
            logging.error(f"Main content not found at {full_url} - saved screenshot {screenshot_path}")
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
        file_path = os.path.join(DOWNLOAD_DIR, f"{index + 325 + 1}_{doc_id}.txt")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

        logging.info(f"Saved txt: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Error saving document TXT {index}: {e}")
        if driver:
            driver.save_screenshot(os.path.join(DOWNLOAD_DIR, f"error_file_{index}.png"))
        return False
    finally:
        if driver:
            driver.quit()


def main():
    with open('./link_downloads/file_link_download_baocao_full.txt', 'r', encoding='utf-8') as file:
        download_urls = [
            line.strip()
            for line in file
            if line.strip().startswith("https://thuvienphapluat.vn/")
        ]

    logging.info(f"Total {len(download_urls)} links found in {FIELD}.txt")

    max_workers = 1
    start_index = 0
    batch_size = 1

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

        delay = random.uniform(5, 8)
        logging.info(f"Sleeping {delay:.2f}s between batches...")
        time.sleep(delay)

    logging.info("All TXT content saved.")


# ======= Entry Point =======
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
