import os
from pathlib import Path
from amtb_crawler import AmtbCrawler

def read_lecture_numbers(file_path):
    """读取讲座编号列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        # 过滤掉空行和非讲座编号的行
        return [line.strip() for line in f if line.strip() and not line.startswith('```')]

def main():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    lecture_file = project_root / 'lecture_numbers.md'
    
    if not lecture_file.exists():
        print(f"找不到讲座编号文件: {lecture_file}")
        return
    
    # 读取讲座编号
    lecture_numbers = read_lecture_numbers(lecture_file)
    print(f"总共读取到 {len(lecture_numbers)} 个讲座编号")
    
    if not lecture_numbers:
        print("没有找到有效的讲座编号")
        return
    
    # 创建爬虫实例
    crawler = AmtbCrawler()
    
    try:
        # 处理每个讲座编号
        for i, lecture_no in enumerate(lecture_numbers, 1):
            # 检查是否已完成
            if lecture_no in crawler.progress and crawler.progress[lecture_no]["status"] == "completed":
                print(f"跳过已完成的讲座 ({i}/{len(lecture_numbers)}): {lecture_no}")
                continue
                
            print(f"正在处理第 {i}/{len(lecture_numbers)} 个讲座: {lecture_no}")
            crawler.process_lecture(lecture_no)
            
    except KeyboardInterrupt:
        print("\n用户中断程序，已保存进度")
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        print("正在关闭浏览器...")
        crawler.close()
        print("程序结束")

if __name__ == "__main__":
    main() 