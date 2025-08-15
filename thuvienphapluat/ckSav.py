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

# Cấu hình thư mục lưu
field = "bomayhanhchinh_3"
download_dir = f"download_{field}"
os.makedirs(download_dir, exist_ok=True)

# Log file
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

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ← bạn có thể bỏ dòng này nếu muốn thấy trình duyệt chạy
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# Cookie session
cookies = [
    {'name': 'cf_clearance', 'value': '1pfb3RRJB6VTg3M4qSp6IFuQ3DBImzIocpLMdE13QK4-1753928599-1.2.1.1-XNWJ_o97tqZucifBF.aeGsWsiXAleg3Twv4ChdrpJZ0gd41zM8rzEG4beJlUapIPeK1Yab830N81OKlKjPj7Ux39B1pIRfHL8wRCx9FZVBSM5MWsSuxR_4J0bCxKOUwQZCmtGOHqaKB0ph47O9DySg_kJ4ZJXCaFI305LFcHrMFr2qLegsyp2NohzUMxEmAg4Vx_yb93usHzMhQF8sywf70Msh1e4TLXjEATKAk3z1U', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'uza4evblj1qj1ismazmfjf4h', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '6A5483D68FC937A9135B357CAA8F8FA85746EBE366A91C07FCD36DE091839971C67CD3AFA8EBB293BEA0838DE4D9FB7E9C784F1A70A557EC9F0789DFD2F6C90E3FB248938A36D1ADF932D7C8CCF16EBD5988883C81FB5E3B4A12AB71328D06A33FFD388DEA3D2402A3E6D32BDE1E1B472ADA0762D087C0A1A818BC0ABAE99F3BF4EAAD7608CE246966D0A3C0248E8132CDE95D9AA2BBB09C6E219F1F9156D0A10F8A112F555081CFDBBE5A8C28869416AACBA1AEE08127B88323CC1F3DA02BB18EC6DC28E542AD260DD93AEF', 'domain': 'thuvienphapluat.vn'},
    {'name': 'dl_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtYzU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
]

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = None
    try:
        driver = create_driver()
        base_url = "https://thuvienphapluat.vn"
        driver.get(base_url)
        time.sleep(random.uniform(2, 4))

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.warning(f"Could not add cookie: {e}")

        driver.get(url)
        time.sleep(random.uniform(3, 6))

        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        except Exception:
            pass

        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc, div.col-md-12.py-4"))
            )
        except Exception:
            screenshot_path = f"{download_dir}/error_file_{field}_{index + 828}.png"
            driver.save_screenshot(screenshot_path)
            logging.error(f"❌ Không tìm thấy nội dung chính tại {url} - đã lưu ảnh lỗi {screenshot_path}")
            return False

        try:
            content_div = driver.find_element(By.CSS_SELECTOR, "div#tab1.contentDoc")
        except:
            content_div = driver.find_element(By.CSS_SELECTOR, "div.col-md-12.py-4")

        html_content = content_div.get_attribute("outerHTML")
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        doc_id = url.rstrip("/").split("/")[-1].split(".")[0]
        file_path = os.path.join(download_dir, f"{field}_{index + 828}_{doc_id}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

        logging.info(f"✅ Đã lưu: {file_path}")
        return True

    except Exception as e:
        logging.error(f"❌ Lỗi tải TXT {index}: {e}")
        if driver:
            driver.save_screenshot(f"{download_dir}/error_file_{index}_exception.png")
        return False
    finally:
        if driver:
            driver.quit()
            time.sleep(1)

def main():
    with open('./link_downloads/bomayhanhchinh.txt', 'r', encoding='utf-8') as file:
        download_urls = [line.strip() for line in file if line.strip().startswith("https://")]

    logging.info(f"📄 Tổng cộng {len(download_urls)} liên kết sẽ được xử lý")

    max_workers = 1
    batch_size = 1
    for batch_start in range(0, len(download_urls), batch_size):
        batch_urls = download_urls[batch_start:batch_start + batch_size]
        logging.info(f"📦 Xử lý batch {batch_start} đến {batch_start + len(batch_urls)}")

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
                    logging.error(f"Lỗi không xác định khi tải {url}: {e}")

        delay = random.uniform(3, 5)
        logging.info(f"⏳ Tạm dừng {delay:.2f} giây giữa các batch...")
        time.sleep(delay)

    logging.info("🎉 Hoàn tất tải tất cả văn bản.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"🔥 Lỗi nghiêm trọng: {e}")
