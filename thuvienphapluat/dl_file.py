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
import threading
from bs4 import BeautifulSoup

# Field to name the file
field = "baocao"

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
    # ❗ KHÔNG sử dụng chế độ headless
    chrome_options.add_argument("--headless=new")  # ❌ tắt đi
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")

    # Thêm User-Agent giả lập trình duyệt người thật
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    # Các tham số ngẫu nhiên khác để tránh bị phát hiện bot


# Create download folder
download_dir = "download_" + field
os.makedirs(download_dir, exist_ok=True)

# Cookies login
cookies = [
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '38A6E3DC3B39DBF0DCDC1353236483B060F33F6B0D7E32A02087BAC1F61F5C9D7E195BA66450E3924535FC3180A0392D580B68A996787576AC3D1781E68FFF80EB55841F264D9FBCCF9935998C23B376756DAEA1E2809E3559F77A73F15330192A36590049BFE8F379FEEFB3D8C8CEA112785FF763978611C7427BECC9D721676C2DAFCC3AA8B07F7A70DBAAAFF25D4953EF7143052F609E1352B3A458230EAD869F323D32745E847B183BC2074BB62603371C057CEEA4ED9A193631E2C0C5B5DF57B11737EDE8ADA577291C', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'f1hce3lpyk0gsmkwmoksf401', 'domain': 'thuvienphapluat.vn'}
]

# Thread-local storage for driver instances
thread_local = threading.local()

def get_driver():
    if not hasattr(thread_local, "driver"):
        thread_local.driver = create_driver()
        base_url = "https://thuvienphapluat.vn"
        thread_local.driver.get(base_url)
        for cookie in cookies:
            thread_local.driver.add_cookie(cookie)
        thread_local.driver.refresh()
    return thread_local.driver

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def download_content(url, index):
    driver = get_driver()
    try:
        full_url = f"https://thuvienphapluat.vn{url}" if not url.startswith("http") else url
        driver.get(full_url)
        time.sleep(random.uniform(1.2, 2.7))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab1.contentDoc"))
        )

        content_div = driver.find_element(By.CSS_SELECTOR, "div#tab1.contentDoc")
        html_content = content_div.get_attribute("outerHTML")
        
        soup = BeautifulSoup(html_content, "html.parser")
        inner = soup.find("div", class_="cldivContentDocVn", id="divContentDoc")
        if inner:
            text = inner.get_text(separator="\n", strip=True)
        else:
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
        if driver:
            driver.save_screenshot(f"error_file_{index}.png")
        raise

def main():
    # Read URLs from file
    with open('./link_downloads/file_link_download_baocao_full.txt', 'r', encoding='utf-8') as file:
        download_urls = [
            line.strip()
            for line in file
            if line.strip().startswith("https://thuvienphapluat.vn/")
        ]

    logging.info(f"Total {len(download_urls)} links found in " + field + ".txt")

    # Process URLs in parallel
    max_workers = 5  # Adjust based on system capacity
    start_index = 0 # Change if need
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
        time.sleep(random.uniform(5, 10))

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