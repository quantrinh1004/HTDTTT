import logging
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ==================== Cấu hình ====================
field = "baocao_full"
start_page = 1
total_pages = 79
output_file = f"file_link_download_{field}.txt"
download_dir = "link_downloads"

# ==================== Logging setup ====================
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, output_file + ".log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    ]
)

# ==================== Chrome Options ====================
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

# ==================== Cookie ====================
cookies = [
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '4C262F512F9A0CB533D38ED63A151092043D27B355189316B43E4DB20816CE30C2E41289113774B996AF26FB95E21374B7CB8ED0D14885DAEE4F01181D277436117255016CBAC63942D4392C4AD1D5A77A8A7B2E31C7A0E4A17FE124C28A33126BE1251365F3F7E6813CD8BEA807375499FE62746CD3F5FE2E0FEA93BC66E09D88F99E15EC08FC4622B3F84558DFA522AA2E35BB8D5A070A1C6024B1B20705A7C1568A6E1FC2522837F7CF1E6A27E00C3F6FF3D87174B5857EB6D69566EDE2A017FECEAA2528E92D884ED712', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'x4khck23viz0ptnhjfk2ji5c', 'domain': 'thuvienphapluat.vn'}
]

# ==================== Start Crawling ====================
try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    base_url = "https://thuvienphapluat.vn"
    driver.get(base_url)

    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

    download_urls = []

    for page_number in range(start_page, total_pages + 1):
        try:
            page_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword=&area=0&match=True&type=46&status=0&signer=0&sort=1&lan=1&scan=0&org=0&fields=&page={page_number}"
            logging.info(f"➡️ Đang truy cập: {page_url}")
            driver.get(page_url)

            # 💤 Delay ngẫu nhiên để tránh bị chặn
            delay = random.uniform(3, 6)
            logging.info(f"⏳ Chờ {delay:.2f}s giả lập người dùng...")
            time.sleep(delay)

            # 📜 Cuộn trang xuống để giả lập người dùng
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            logging.info(f"🧭 Tiêu đề trang: {driver.title}")

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".nqTitle a"))
            )

            links = driver.find_elements(By.CSS_SELECTOR, ".nqTitle a")

            if not links:
                logging.warning(f"⚠️ Trang {page_number} không có liên kết nào.")
                continue

            for link in links:
                href = link.get_attribute("href")
                if href:
                    download_urls.append(href)
                    logging.info(f"✅ Đã lấy link: {href}")
                else:
                    logging.warning("⚠️ Một thẻ <a> không có thuộc tính href.")

        except Exception as e:
            logging.error(f"❌ Lỗi tại trang {page_number}: {e}")
            with open(f"log/error_page_{page_number}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    # ==================== Ghi ra file ====================
    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, output_file)

    with open(file_path, "w", encoding="utf-8") as f:
        for url in download_urls:
            f.write(url + "\n")

    logging.info(f"🎉 Hoàn tất! Tổng cộng {len(download_urls)} link đã lưu vào {file_path}")
    time.sleep(5)

except Exception as e:
    logging.critical(f"🚨 Lỗi nghiêm trọng: {e}")

finally:
    if 'driver' in locals():
        driver.quit()
