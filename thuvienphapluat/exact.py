import os
import re

def extract_and_save_links(log_text: str, field: str):
    # Trích xuất link từ log
    pattern = r"✅ Đã lấy link: (https?://[^\s]+)"
    links = re.findall(pattern, log_text)

    # Đường dẫn file
    output_file = f"file_link_download_{field}.txt"
    download_dir = "link_downloads"
    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, output_file)

    # Ghi link vào file
    with open(output_path, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

    print(f"✅ Đã lưu {len(links)} link vào: {output_path}")

field = "bomayhanhchinh1_50"

with open("log/file_link_download_bomayhanhchinh1_50page.txt.log", "r", encoding="utf-8") as f:
    log_content = f.read()

extract_and_save_links(log_content, field)
