"""日志配置模块

提供统一的日志记录功能：
- 文件日志： RotatingFileHandler，自动轮转
- 控制台日志：StreamHandler
- 支持国际化日志消息
- 程序退出时正确释放资源
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# 日志配置常量
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "grabthesite.log"
DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_ENCODING = 'utf-8'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 控制台输出开关（GUI模式下可关闭）
CONSOLE_OUTPUT_ENABLED = True

# 全局标志：是否已经初始化
_initialized = False
_root_handlers = []


def disable_console_output():
    """禁用控制台日志输出（用于GUI模式）
    
    调用此函数后，所有logger将只输出到文件，不输出到控制台
    """
    global CONSOLE_OUTPUT_ENABLED
    CONSOLE_OUTPUT_ENABLED = False


def _load_logging_config():
    """加载日志配置
    
    Returns:
        dict: 包含日志配置项的字典，如果配置不可用则返回空字典
    """
    try:
        from config import LOGGING_CONFIG
        return LOGGING_CONFIG
    except (ImportError, AttributeError):
        return {}


def _get_log_settings():
    """获取日志设置
    
    Returns:
        tuple: (log_dir, log_file, log_level, console_level, max_bytes, backup_count)
    """
    config = _load_logging_config()
    
    log_file = config.get('file', os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILE))
    log_dir = os.path.dirname(log_file) or DEFAULT_LOG_DIR
    
    level_str = config.get('level', 'INFO')
    log_level = getattr(logging, level_str.upper(), logging.INFO)
    console_level = log_level
    
    max_bytes = config.get('max_bytes', DEFAULT_MAX_BYTES)
    backup_count = config.get('backup_count', DEFAULT_BACKUP_COUNT)
    
    return log_dir, log_file, log_level, console_level, max_bytes, backup_count


# 翻译函数封装，使用 builtins._ 以支持动态语言切换
def _(message):
    """翻译函数，从 builtins 获取实际的翻译函数"""
    import builtins
    trans_func = getattr(builtins, '_', None)
    if trans_func and callable(trans_func):
        return trans_func(message)
    return message


def _ensure_root_logger_configured():
    """确保根日志记录器已配置（只执行一次）"""
    global _initialized, _root_handlers
    
    if _initialized:
        return
    
    log_dir, log_file, log_level, console_level, max_bytes, backup_count = _get_log_settings()
    
    # 使用绝对路径
    log_file = os.path.abspath(log_file)
    log_dir = os.path.abspath(log_dir) if log_dir else os.path.dirname(log_file)
    
    # 确保目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置根记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 根记录器设置最低级别
    
    # 清除现有的处理器（避免重复）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except:
            pass
    
    # 创建文件处理器
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=DEFAULT_ENCODING,
            delay=False
        )
        file_handler.setLevel(log_level)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        _root_handlers.append(file_handler)
        
        # 输出日志文件位置
        print(f"[Logger] 日志文件: {log_file} (level={logging.getLevelName(log_level)})", flush=True)
        
    except Exception as e:
        print(f"[Logger Error] 无法创建文件处理器: {e}", flush=True)
        file_handler = None
    
    # 创建控制台处理器
    if CONSOLE_OUTPUT_ENABLED:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        _root_handlers.append(console_handler)
    
    _initialized = True


def setup_logger(name=__name__):
    """设置并返回一个配置好的 logger 实例
    
    Args:
        name: logger 名称，默认使用模块名称
        
    Returns:
        配置好的 logger 实例
    """
    # 确保根记录器已配置
    _ensure_root_logger_configured()
    
    # 获取或创建命名记录器
    logger = logging.getLogger(name)
    
    # 添加翻译方法
    logger._ = _
    
    return logger


def close_all_loggers():
    """关闭所有日志处理器，释放文件锁
    
    在程序退出前调用，确保日志文件被正确关闭
    """
    global _initialized
    
    try:
        # 先刷新所有日志
        logging.shutdown()
        
        # 获取根记录器
        root_logger = logging.getLogger()
        
        # 关闭并移除所有处理器
        for handler in root_logger.handlers[:]:
            try:
                handler.flush()
                handler.close()
            except:
                pass
            finally:
                root_logger.removeHandler(handler)
        
        # 清理命名记录器的处理器
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers[:]:
                try:
                    handler.flush()
                    handler.close()
                except:
                    pass
                finally:
                    logger.removeHandler(handler)
        
        _initialized = False
        print("[Logger] 日志资源已清理", flush=True)
        
    except Exception as e:
        print(f"[Logger Error] 清理日志时出错: {e}", flush=True)


# 确保程序退出时清理日志
import atexit
atexit.register(close_all_loggers)

# 创建默认 logger 实例
default_logger = setup_logger()
