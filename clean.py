import os
import shutil
from pathlib import Path

def clean_previous_downloads():
    """
    清理之前的下载记录和文件
    """
    print("开始清理之前的下载记录...")
    
    # 使用固定路径
    base_dir = Path('/root/amtb')
    
    # 1. 删除downloads目录
    downloads_dir = base_dir / "downloads"
    if downloads_dir.exists():
        print("删除downloads目录...")
        shutil.rmtree(downloads_dir)
    
    # 2. 删除failed_codes.txt
    failed_codes_file = base_dir / "failed_codes.txt"
    if failed_codes_file.exists():
        print("删除failed_codes.txt...")
        failed_codes_file.unlink()
        
    # 3. 删除download_log.txt
    log_file = base_dir / "download_log.txt"
    if log_file.exists():
        print("删除download_log.txt...")
        log_file.unlink()
    
    # 4. 清理lecture_numbers.md中的下载记录
    lecture_numbers_file = base_dir / "lecture_numbers.md"
    print("清理lecture_numbers.md中的下载记录...")
    with open(lecture_numbers_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 移除所有注释
    cleaned_lines = []
    for line in lines:
        if line.strip():  # 跳过空行
            cleaned_line = line.split('#')[0].rstrip() + '\n'
            cleaned_lines.append(cleaned_line)
    
    # 写回文件
    with open(lecture_numbers_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print("清理完成！\n")

if __name__ == "__main__":
    clean_previous_downloads() 