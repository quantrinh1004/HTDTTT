import os

def count_files_starting_with_new(folder_path):
    count = 0
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)) and filename.startswith("new1"):
            count += 1
    return count

# Ví dụ sử dụng
folder_path = "./download_bomayhanhchinh"  # thay bằng đường dẫn thật
num_files = count_files_starting_with_new(folder_path)
print(f"Số file bắt đầu bằng 'new1': {num_files}")
