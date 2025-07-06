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

# ========== CẤU HÌNH ==============
field = "baocao"
download_dir = "download_" + field
os.makedirs(download_dir, exist_ok=True)

log_file = f"Save_{field}.log"
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
    chrome_options.add_argument("--headless=new")  # ❌ tắt đi
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    return webdriver.Chrome(options=chrome_options)

cookies = [
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '2B446C9AF93B0CD776F9A0688136B1ECBF31D5921E3536C6993DDF96F240D87F31FA33DF1115FBC769052CEB5E16AAA15ED4D5B1C6672A19A91E5909A549A0338AC98E0CC1FCD04478D3BD114344B2344D9C7FDBA1CADF6358ED1C3D0DCE552AF85DBEBD90D3145C40C4D20A2B8BDC344C7037C9152851266E87EDFB1ED43DC828114C7C2416C00DA4914845312110AB4199ECD01782D9F064AD214D90275CA8B948A5FF2E00E6D0A3A1AC4090DC976D7039443BF613BB4B61C9778A5FE375DBEEED2316AFC765E9DD51C3B3', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'emh2we0xj4zmy2kcdxyxrf2t', 'domain': 'thuvienphapluat.vn'}
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
                logging.warning(f"Không thể add cookie: {e}")
        driver.refresh()

        full_url = f"{url}" if url.startswith("http") else f"{base_url}{url}"
        driver.get(full_url)

        # 💤 Delay ngẫu nhiên để tránh bị chặn
        delay = random.uniform(3, 6)
        logging.info(f"⏳ Chờ {delay:.2f}s giả lập người dùng...")
        time.sleep(delay)

        # Nếu gặp Cloudflare, lưu HTML lỗi
        if "cloudflare" in driver.page_source.lower() or "checking your browser" in driver.page_source.lower():
            with open(f"{download_dir}/cloudflare_{index}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.error(f"🔥 Cloudflare blocking at {full_url} (index {index})")
            return False

        # Chờ nội dung chính
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc, div.col-md-12.py-4"))
            )
        except Exception:
            logging.error(f"❌ Không tìm thấy nội dung chính ở {full_url}")
            driver.save_screenshot(f"{download_dir}/error_file_{index}.png")
            return False

        # Lấy nội dung
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
        file_path = os.path.join(download_dir, f"{index + 1120}_{doc_id}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)

        logging.info(f"✅ Saved txt: {file_path}")
        return True

    except Exception as e:
        logging.error(f"❌ Error saving document TXT {index}: {e}")
        if driver is not None:
            driver.save_screenshot(f"{download_dir}/error_file_{index}.png")
        return False
    finally:
        if driver is not None:
            driver.quit()

def main():
    # Đọc danh sách URL
    with open('./link_downloads/file_link_download_baocao_full.txt', 'r', encoding='utf-8') as file:
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

        # Delay giữa các batch để giảm nguy cơ bị chặn
        delay = random.uniform(5, 12)
        logging.info(f"⏳ Nghỉ {delay:.2f}s giữa các batch...")
        time.sleep(delay)

    logging.info("🎉 All TXT content saved.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")