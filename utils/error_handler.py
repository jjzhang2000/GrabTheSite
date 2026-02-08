"""错误处理模块

提供重试机制和错误处理策略：
- 自动重试失败的操作
- 支持指数退避算法
- 可配置重试策略
"""

import time
import random
import logging
from functools import wraps
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


class ErrorHandler:
    """错误处理器，提供重试机制和错误处理策略"""
    
    def __init__(self, retry_count=3, retry_delay=2, exponential_backoff=True, 
                 retryable_errors=None, fail_strategy='log'):
        """初始化错误处理器
        
        Args:
            retry_count: 重试次数
            retry_delay: 重试间隔（秒）
            exponential_backoff: 是否使用指数退避
            retryable_errors: 可重试的错误类型或状态码列表
            fail_strategy: 失败策略，可选值：'log'（仅记录）, 'skip'（跳过）, 'raise'（抛出异常）
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.retryable_errors = retryable_errors or [429, 500, 502, 503, 504]
        self.fail_strategy = fail_strategy
    
    def retry(self, func):
        """重试装饰器
        
        Args:
            func: 要装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= self.retry_count:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 检查是否是可重试的错误
                    if self._is_retryable_error(e):
                        retries += 1
                        if retries > self.retry_count:
                            # 达到最大重试次数
                            logger.error(f"达到最大重试次数 {self.retry_count}，操作失败: {str(e)}")
                            return self._handle_failure(e, *args, **kwargs)
                        
                        # 计算延迟时间
                        delay = self._calculate_delay(retries)
                        logger.warning(f"操作失败，{delay:.2f}秒后重试 ({retries}/{self.retry_count}): {str(e)}")
                        time.sleep(delay)
                    else:
                        # 不可重试的错误，直接处理
                        logger.error(f"操作失败（不可重试）: {str(e)}")
                        return self._handle_failure(e, *args, **kwargs)
        return wrapper
    
    def _is_retryable_error(self, error):
        """检查错误是否可重试
        
        Args:
            error: 异常对象
            
        Returns:
            bool: 是否可重试
        """
        # 处理 HTTP 错误
        if hasattr(error, 'response') and error.response:
            status_code = error.response.status_code
            return status_code in self.retryable_errors
        
        # 处理网络错误
        error_str = str(error)
        network_errors = ['timeout', 'connection error', 'connection refused', 
                         'network is unreachable', 'name or service not known']
        for net_error in network_errors:
            if net_error in error_str.lower():
                return True
        
        return False
    
    def _calculate_delay(self, retry_count):
        """计算重试延迟时间
        
        Args:
            retry_count: 当前重试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        if self.exponential_backoff:
            # 指数退避：2^retry_count * base_delay
            delay = (2 ** retry_count) * self.retry_delay
        else:
            delay = self.retry_delay
        
        # 添加随机抖动，避免并发请求同时重试
        jitter = random.uniform(0.5, 1.5)
        return delay * jitter
    
    def _handle_failure(self, error, *args, **kwargs):
        """处理失败
        
        Args:
            error: 异常对象
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            失败时的返回值
        """
        if self.fail_strategy == 'raise':
            raise error
        elif self.fail_strategy == 'skip':
            logger.info("跳过失败的操作")
            return None
        else:  # 'log'
            logger.error(f"操作失败: {str(error)}")
            return None


# 创建默认错误处理器实例
default_error_handler = ErrorHandler()


# 便捷的重试装饰器
def retry(retry_count=3, retry_delay=2, exponential_backoff=True, 
          retryable_errors=None, fail_strategy='log'):
    """便捷的重试装饰器
    
    Args:
        retry_count: 重试次数
        retry_delay: 重试间隔（秒）
        exponential_backoff: 是否使用指数退避
        retryable_errors: 可重试的错误类型或状态码列表
        fail_strategy: 失败策略
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        handler = ErrorHandler(
            retry_count=retry_count,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            retryable_errors=retryable_errors,
            fail_strategy=fail_strategy
        )
        return handler.retry(func)
    return decorator