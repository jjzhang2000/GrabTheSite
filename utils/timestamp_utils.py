# 时间戳工具函数

import os
import time
import requests
from email.utils import parsedate_to_datetime
from logger import setup_logger
from config import ERROR_HANDLING_CONFIG, USER_AGENT
from utils.error_handler import ErrorHandler, retry

# 获取 logger 实例
logger = setup_logger(__name__)

# 创建错误处理器实例
error_handler = ErrorHandler(
    retry_count=ERROR_HANDLING_CONFIG.get('retry_count', 3),
    retry_delay=ERROR_HANDLING_CONFIG.get('retry_delay', 2),
    exponential_backoff=ERROR_HANDLING_CONFIG.get('exponential_backoff', True),
    retryable_errors=ERROR_HANDLING_CONFIG.get('retryable_errors', [429, 500, 502, 503, 504]),
    fail_strategy=ERROR_HANDLING_CONFIG.get('fail_strategy', 'log')
)


def get_file_timestamp(file_path):
    """获取本地文件的修改时间
    
    Args:
        file_path: 文件路径
    
    Returns:
        float: 文件的修改时间戳，文件不存在返回 0
    """
    if os.path.exists(file_path):
        try:
            return os.path.getmtime(file_path)
        except (IOError, OSError) as e:
            logger.error(f"获取文件时间戳失败: {file_path}, 错误: {e}")
            return 0
    return 0


@retry()
def get_remote_timestamp(url):
    """获取远程文件的 Last-Modified 时间
    
    Args:
        url: 文件 URL
    
    Returns:
        float: 远程文件的修改时间戳，获取失败返回 0
    """
    # 发送 HEAD 请求，只获取头部信息
    headers = {
        'User-Agent': USER_AGENT
    }
    from config import DEFAULT_REQUEST_TIMEOUT
    response = requests.head(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, allow_redirects=True)
    
    # 检查响应状态码
    if response.status_code != 200:
        logger.debug(f"获取远程文件头部失败: {url}, 状态码: {response.status_code}")
        return 0
    
    # 获取 Last-Modified 头
    last_modified = response.headers.get('Last-Modified')
    if not last_modified:
        logger.debug(f"远程文件无 Last-Modified 头: {url}")
        return 0
    
    # 解析时间格式
    last_modified_date = parsedate_to_datetime(last_modified)
    # 转换为时间戳
    return time.mktime(last_modified_date.timetuple())


def should_update(remote_timestamp, local_timestamp):
    """比较远程和本地时间戳，判断是否需要更新
    
    Args:
        remote_timestamp: 远程文件的时间戳
        local_timestamp: 本地文件的时间戳
    
    Returns:
        bool: True 表示需要更新，False 表示不需要更新
    """
    # 如果远程时间戳为 0，需要更新（可能是获取失败或文件不存在）
    if remote_timestamp == 0:
        return True
    
    # 如果本地时间戳为 0，需要更新（文件不存在）
    if local_timestamp == 0:
        return True
    
    # 远程时间戳大于本地时间戳，需要更新
    return remote_timestamp > local_timestamp
