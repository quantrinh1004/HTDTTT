import logging
import time
import os
import random
import requests
from io import BytesIO
from PIL import Image
import pytesseract

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ==================== Cấu hình ====================
field = "bomayhanhchinh150-200-fileerror"
start_page = 150
total_pages = 51
output_file = f"file_link_download_{field}.txt"
download_dir = "link_downloads"

# ==================== Logging setup ====================
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, output_file + "_4page.log")

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

# ==================== Cookie ====================
cookies = [
    {'name': 'cf_clearance', 'value': 'YSl_wE2XeCyG7Wi5ZKHANEFZihvV.OL0EDjnWbFkyV0-1752030951-1.2.1.1-HDW0ABCa8.4J4CU2Yxh3DCfUJdwpkpRFIIzbw4WNCxF8c206AnVEJsRHPjsTTy0.8BLJpC.vjeSY0aPXkB3VHfVC8V4hK0ASe_11tzFVJw6cYmp1YSW2lzV_oecB9jvyBWOgSC7zC11UPNtGIfT3F5l_kZMm3rhExBEfdCgXQuZdhvd1B_VlDOG98gQwyewbuSPG71IYa7FhC35yDmC64wXcPG5zYqgyzpMWmmhhLq0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'ASP.NET_SessionId', 'value': 'x1nureejgpaxyy3av4qzzzau', 'domain': 'thuvienphapluat.vn'},
    {'name': 'thuvienphapluatnew', 'value': '6A5483D68FC937A9135B357CAA8F8FA85746EBE366A91C07FCD36DE091839971C67CD3AFA8EBB293BEA0838DE4D9FB7E9C784F1A70A557EC9F0789DFD2F6C90E3FB248938A36D1ADF932D7C8CCF16EBD5988883C81FB5E3B4A12AB71328D06A33FFD388DEA3D2402A3E6D32BDE1E1B472ADA0762D087C0A1A818BC0ABAE99F3BF4EAAD7608CE246966D0A3C0248E8132CDE95D9AA2BBB09C6E219F1F9156D0A10F8A112F555081CFDBBE5A8C28869416AACBA1AEE08127B88323CC1F3DA02BB18EC6DC28E542AD260DD93AEF', 'domain': 'thuvienphapluat.vn'},
    {'name': 'dl_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtYzU0', 'domain': 'thuvienphapluat.vn'},
    {'name': 'lg_user', 'value': '0=c5aGJtZE1ZVzVRYUhWdmJtY3NURTRzVkhKMVpRPTU0', 'domain': 'thuvienphapluat.vn'},
]

# ==================== Hàm xử lý CAPTCHA ====================
def handle_captcha_auto(driver):
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

# ==================== Start Crawling ====================
try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(random.uniform(6, 9))

    base_url = "https://thuvienphapluat.vn"
    driver.get(base_url)

    for cookie in cookies:
        driver.add_cookie(cookie)

    download_urls = []
    pages = [168, 173, 185, 188]

    for page_number in pages:
        try:
            logging.info(f"➡️ page error before: {page_number}")
            page_url = f"https://thuvienphapluat.vn/page/searchlegal.aspx?keyword=&area=0&match=True&type=0&status=1&signer=0&sort=1&lan=1&scan=0&org=0&fields=15&chlbg=09/07/1945&chlend=09/07/2035&page={page_number}"
            logging.info(f"➡️ Đang truy cập: {page_url}")
            driver.get(page_url)

            delay = random.uniform(4, 8)
            logging.info(f"⏳ Chờ {delay:.2f}s giả lập người dùng...")
            time.sleep(delay)


            handle_captcha_auto(driver)  # <-- CHÈN TỰ ĐỘNG XỬ LÝ CAPTCHA Ở ĐÂY

            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            # time.sleep(random.uniform(0.5, 1.5))
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            # time.sleep(random.uniform(1, 3))

            logging.info(f"🧭 Tiêu đề trang: {driver.title}")

            WebDriverWait(driver, 8).until(
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
                    logging.warning("⚠️ Một thẻ <a> không có href.")

        except Exception as e:
            logging.error(f"❌ Lỗi tại trang {page_number}: {e}")
            with open(f"log/error_page_{page_number}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, output_file)

    with open(file_path, "a", encoding="utf-8") as f:
        for url in download_urls:
            f.write(url + "\n")

    logging.info(f"🎉 Hoàn tất! Tổng cộng {len(download_urls)} link đã lưu vào {file_path}")
    time.sleep(3)

except Exception as e:
    logging.critical(f"🚨 Lỗi nghiêm trọng: {e}")

finally:
    if 'driver' in locals():
        driver.quit()
