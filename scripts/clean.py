import os
import shutil

def clean_previous_downloads(project_dir=None):
    """
    清理之前的下载记录和文件
    """
    # 如果没有指定目录，使用默认目录
    project_dir = project_dir or "/root/amtb_project"
    print(f"清理目录: {project_dir}")
    
    print("开始清理之前的下载记录...")
    
    # 1. 删除downloads目录
    downloads_dir = os.path.join(project_dir, "downloads")
    if os.path.exists(downloads_dir):
        print("删除downloads目录...")
        shutil.rmtree(downloads_dir)
    
    # 2. 删除failed_codes.txt
    failed_codes_file = os.path.join(project_dir, "failed_codes.txt")
    if os.path.exists(failed_codes_file):
        print("删除failed_codes.txt...")
        os.remove(failed_codes_file)
    
    # 3. 清理lecture_numbers.md中的下载记录
    lecture_numbers_file = os.path.join(project_dir, "lecture_numbers.md")
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
    
    print("清理完成！准备开始新的下载...\n")

if __name__ == "__main__":
    # 可以在这里指定要清理的目录
    project_dir = "/root/amtb_project"  # 可以根据需要修改这个路径
    clean_previous_downloads(project_dir) 