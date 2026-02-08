"""日志配置模块

提供统一的日志记录功能：
- 文件日志： RotatingFileHandler，自动轮转
- 控制台日志：StreamHandler
- 支持国际化日志消息
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# 日志配置常量
LOG_DIR = "logs"
DEFAULT_LOG_FILE = "grabthesite.log"
DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_ENCODING = 'utf-8'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 尝试从配置读取日志文件路径
try:
    from config import LOGGING_CONFIG
    LOG_FILE = LOGGING_CONFIG.get('file', os.path.join(LOG_DIR, "grabthesite.log"))
except ImportError:
    # 配置模块可能尚未初始化，使用默认值
    LOG_FILE = os.path.join(LOG_DIR, "grabthesite.log")

# 创建日志目录
os.makedirs(LOG_DIR, exist_ok=True)

# 尝试导入翻译函数，避免循环导入
try:
    from utils.i18n import gettext as _
except ImportError:
    # 如果导入失败，使用身份函数
    _ = lambda message: message

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
            maxBytes=DEFAULT_MAX_BYTES,
            backupCount=DEFAULT_BACKUP_COUNT,
            encoding=DEFAULT_ENCODING
        )
        file_handler.setLevel(DEFAULT_LOG_LEVEL)
        
        # 创建控制台处理器，用于输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(DEFAULT_CONSOLE_LEVEL)
        
        # 定义日志格式
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到 logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    # 添加翻译方法
    logger._ = _
    
    return logger

# 创建默认 logger 实例
default_logger = setup_logger()
