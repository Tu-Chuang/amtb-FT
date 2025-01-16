import logging
import os
from datetime import datetime
from . import config

def setup_logger(name, log_file=None):
    """
    设置日志记录器
    :param name: 日志记录器名称
    :param log_file: 日志文件路径（可选）
    """
    if log_file is None:
        log_file = config.get_log_file(name)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 创建文件处理器
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)

    # 创建控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 设置格式化器
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 添加处理器
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

# 创建各个服务的日志记录器
crawler_logger = setup_logger('crawler')
monitor_logger = setup_logger('monitor')
notify_logger = setup_logger('notify')

def log_error(logger, error, message=None):
    """
    记录错误信息
    """
    if message:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(str(error)) 