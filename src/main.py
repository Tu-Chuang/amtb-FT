import os
import time
from pathlib import Path
from amtb_crawler import AmtbCrawler
import sys
import traceback
import psutil
import gc
from multiprocessing import Process, Queue

def read_lecture_numbers(file_path):
    """读取讲座编号列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        # 读取所有行并过滤
        lines = [line.strip() for line in f.readlines()]
        # 过滤掉空行、markdown标记和非讲座编号的行
        lecture_numbers = []
        for line in lines:
            # 调试输出
            if line and not line.startswith('```'):
                print(f"处理行: {line}")  # 调试信息
            
            if (line 
                and not line.startswith('```') 
                and not line.startswith('#')
                and '-' in line):
                lecture_numbers.append(line)
        
        print("\n读取到的前10个讲座编号:")
        for i, no in enumerate(lecture_numbers[:10]):
            print(f"  {i+1}. {no}")
            
        return lecture_numbers

def print_memory_usage():
    """打印内存使用情况"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"内存使用: {memory_mb:.2f} MB")

def process_lectures(lecture_numbers, start_from_end=False, name="进程"):
    """处理讲座的函数"""
    try:
        crawler = AmtbCrawler()
        # 如果从尾部开始，则反转列表
        if start_from_end:
            lecture_numbers = lecture_numbers[::-1]
        
        total = len(lecture_numbers)
        for i, lecture_no in enumerate(lecture_numbers, 1):
            try:
                print(f"\n[{name}] 进度: {i}/{total} ({i/total*100:.1f}%)")
                print(f"[{name}] 处理讲座: {lecture_no}")
                
                if lecture_no in crawler.progress and crawler.progress[lecture_no]["status"] == "completed":
                    print(f"[{name}] 跳过已完成的讲座: {lecture_no}")
                    continue
                
                crawler.process_lecture(lecture_no)
                
            except Exception as e:
                print(f"[{name}] 处理讲座 {lecture_no} 时出错: {str(e)}")
                traceback.print_exc()
                continue
                
    except Exception as e:
        print(f"[{name}] 进程出错: {str(e)}")
        traceback.print_exc()
    finally:
        if crawler:
            crawler.close()

def main():
    print("程序启动...")
    print_memory_usage()
    
    print("正在检查文件路径...")
    project_root = Path("/root/amtb")
    print(f"项目根目录: {project_root.absolute()}")
    
    lecture_file = project_root / 'src' / 'lecture_numbers.md'
    print(f"讲座编号文件路径: {lecture_file.absolute()}")
    
    if not lecture_file.exists():
        print(f"错误：找不到讲座编号文件: {lecture_file}")
        return
    
    print(f"文件大小: {lecture_file.stat().st_size} 字节")
    
    print("\n正在读取讲座编号...")
    lecture_numbers = read_lecture_numbers(lecture_file)
    print(f"\n成功读取到 {len(lecture_numbers)} 个讲座编号")
    
    if not lecture_numbers:
        print("错误：没有找到有效的讲座编号")
        return
    
    # 确保编号格式正确并排序
    lecture_numbers = [no.strip() for no in lecture_numbers]
    lecture_numbers = [no for no in lecture_numbers if no.count('-') >= 2]
    lecture_numbers.sort()
    
    print("\n准备开始处理讲座...")
    print(f"第一个讲座编号: {lecture_numbers[0]}")
    print(f"最后一个讲座编号: {lecture_numbers[-1]}")
    print(f"前5个讲座编号: {', '.join(lecture_numbers[:5])}")
    
    try:
        # 创建两个进程，分别从头和尾开始处理
        p1 = Process(target=process_lectures, args=(lecture_numbers, False, "正向进程"))
        p2 = Process(target=process_lectures, args=(lecture_numbers, True, "反向进程"))
        
        print("\n启动两个进程...")
        p1.start()
        p2.start()
        
        # 等待进程完成
        p1.join()
        p2.join()
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
        print("正在等待进程结束...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
        traceback.print_exc()
    finally:
        print("\n所有下载任务已完成")
        print_memory_usage()

if __name__ == "__main__":
    main() 