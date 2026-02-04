# 日志配置模块

import logging
import os
from logging.handlers import RotatingFileHandler

# 日志文件路径
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "grab_the_site.log")

# 创建日志目录
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志系统
def setup_logger(name=__name__):
    """设置并返回一个配置好的 logger 实例
    
    Args:
        name: logger 名称，默认使用模块名称
        
    Returns:
        配置好的 logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置最低日志级别
    
    # 检查是否已经添加了处理器，避免重复添加
    if not logger.handlers:
        # 创建文件处理器，用于写入日志文件
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5  # 最多保留5个备份文件
        )
        file_handler.setLevel(logging.DEBUG)  # 文件日志记录所有级别
        
        # 创建控制台处理器，用于输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
        
        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到 logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 创建默认 logger 实例
default_logger = setup_logger()
