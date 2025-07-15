import re

log_file_path = "./log/file_link_download_bomayhanhchinh150-200.txt.log"  # 🔁 Thay bằng đường dẫn thực tế tới file .log

error_pages = []

with open(log_file_path, "r", encoding="utf-8") as file:
    for line in file:
        match = re.search(r"Lỗi tại trang (\d+)", line)
        if match:
            error_pages.append(int(match.group(1)))

print("📄 Các trang lỗi:", error_pages)
