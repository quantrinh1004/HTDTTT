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

field = "bomayhanhchinh"
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
        logging.FileHandler(log_file, mode="a", encoding="utf-8")
    ]
)

# ==================== Hàm xử lý CAPTCHA ====================
def handle_captcha_auto(driver):
    logging.info("✅ CAPTCHA.")
    try:
        captcha_img = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.XPATH, '//img[contains(@src, "/RegistImage.aspx")]'))
        )
        captcha_src = captcha_img.get_attribute("src")
        if not captcha_src.startswith("http"):
            captcha_src = f"https://thuvienphapluat.vn{captcha_src}"

        session_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        headers = {'User-Agent': driver.execute_script("return navigator.userAgent;")}
        img_data = requests.get(captcha_src, cookies=session_cookies, headers=headers).content

        img = Image.open(BytesIO(img_data)).convert("L")
        img = img.resize((img.size[0]*2, img.size[1]*2))
        img = img.point(lambda x: 0 if x < 140 else 255, '1')  # làm nét

        captcha_text = pytesseract.image_to_string(img, config='--psm 7 digits').strip()
        logging.info(f"🤖 CAPTCHA OCR: {captcha_text}")

        driver.find_element(By.ID, "ctl00_Content_txtSecCode").clear()
        driver.find_element(By.ID, "ctl00_Content_txtSecCode").send_keys(captcha_text)
        driver.find_element(By.ID, "ctl00_Content_CheckButton").click()
        time.sleep(3)
    except TimeoutException:
        logging.info("✅ Không có CAPTCHA.")
    except Exception as e:
        logging.warning(f"⚠️ Lỗi xử lý CAPTCHA: {e}")

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # ❗ Có thể bỏ nếu muốn thấy trình duyệt
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
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


# ==================== Cookie ====================
cookies = [
    {'name': 'cf_clearance', 'value': 'YSl_wE2XeCyG7Wi5ZKHANEFZihvV.OL0EDjnWbFkyV0-1752030951-1.2.1.1-HDW0ABCa8.4J4CU2Yxh3DCfUJdwpkpRFIIzbw4WNCxF8c206AnVEJsRHPjsTTy0.8BLJpC.vjeSY0aPXkB3VHfVC8V4hK0ASe_11tzFVJw6cYmp1YSW2lzV_oecB9jvyBWOgSC7zC11UPNtGIfT3F5l_kZMm3rhExBEfdCgXQuZdhvd1B_VlDOG98gQwyewbuSPG71IYa7FhC35yDmC64wXcPG5zYqgyzpMWmmhhLq0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'x1nureejgpaxyy3av4qzzzau', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '6A5483D68FC937A9135B357CAA8F8FA85746EBE366A91C07FCD36DE091839971C67CD3AFA8EBB293BEA0838DE4D9FB7E9C784F1A70A557EC9F0789DFD2F6C90E3FB248938A36D1ADF932D7C8CCF16EBD5988883C81FB5E3B4A12AB71328D06A33FFD388DEA3D2402A3E6D32BDE1E1B472ADA0762D087C0A1A818BC0ABAE99F3BF4EAAD7608CE246966D0A3C0248E8132CDE95D9AA2BBB09C6E219F1F9156D0A10F8A112F555081CFDBBE5A8C28869416AACBA1AEE08127B88323CC1F3DA02BB18EC6DC28E542AD260DD93AEF', 'domain': 'thuvienphapluat.vn'},
    {'name': 'dl_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtYzU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
]

#index + 1
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = None
    try:
        driver = create_driver()
        base_url = "https://thuvienphapluat.vn"
        driver.get(base_url)
        delay1 = random.uniform(2, 4)
        logging.info(f"⏳ Waiting {delay1:.2f}s for user emulation...")
        time.sleep(delay1)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning(f"Could not add cookie: {e}")
        
        # handle_captcha_auto(driver)
        driver.refresh()

        full_url = f"{url}" if url.startswith("http") else f"{base_url}{url}"
        driver.get(full_url)

        delay = random.uniform(3, 6)
        logging.info(f"⏳ Waiting {delay:.2f}s for user emulation...")
        time.sleep(delay)

        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        except Exception:
            pass

        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc, div.col-md-12.py-4"))
            )
        except Exception:
            screenshot_path = f"{download_dir}/error_file_{index + 1 + random.uniform(1, 1000)}.png"
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
        file_path = os.path.join(download_dir, f"new_{doc_id}.txt")
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
    with open('./link_downloads/bomayhanhchinh.txt', 'r', encoding='utf-8') as file:
        download_urls = [
            line.strip()
            for line in file
            if line.strip().startswith("https://thuvienphapluat.vn/")
        ]

    logging.info(f"Total {len(download_urls)} links found in {field}.txt")

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
                    res = future.result()
                except Exception as e:
                    logging.error(f"Failed to process {url}: {e}")

        delay = random.uniform(3, 5)
        logging.info(f"⏳ {delay:.2f}s between batches...")
        time.sleep(delay)

    logging.info("All TXT content saved.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")