# 速率限制器模块
"""
提供全局速率限制功能，用于控制请求频率。
"""

import time
import threading
from typing import Optional
from logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """全局速率限制器，使用令牌桶算法实现"""
    
    def __init__(self, rate: float = 1.0, burst: int = 1):
        """初始化速率限制器
        
        Args:
            rate: 每秒允许的请求数
            burst: 突发请求数（桶容量）
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """获取一个令牌，用于发起请求
        
        Args:
            blocking: 是否阻塞等待
            timeout: 阻塞时的最大等待时间（秒）
            
        Returns:
            bool: 是否成功获取令牌
        """
        with self.lock:
            self._add_tokens()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            if not blocking:
                return False
            
            # 计算需要等待的时间
            wait_time = (1 - self.tokens) / self.rate
            if timeout is not None and wait_time > timeout:
                return False
        
        # 在锁外等待
        time.sleep(wait_time)
        
        with self.lock:
            self._add_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def _add_tokens(self):
        """根据时间间隔添加令牌"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now


class GlobalDelayManager:
    """全局延迟管理器，确保多线程间的请求延迟"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, delay: float = 1.0, random_delay: bool = True):
        """单例模式，确保全局只有一个延迟管理器"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, delay: float = 1.0, random_delay: bool = True):
        """初始化延迟管理器
        
        Args:
            delay: 基础延迟时间（秒）
            random_delay: 是否使用随机延迟
        """
        if self._initialized:
            return
            
        self.delay = delay
        self.random_delay = random_delay
        self.last_request_time = 0
        self.lock = threading.Lock()
        self._initialized = True
        logger.debug(f"GlobalDelayManager initialized with delay={delay}, random={random_delay}")
    
    def wait(self):
        """等待适当的延迟时间"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            
            if self.random_delay:
                # 随机延迟：0.5 到 1.5 倍的配置延迟时间
                import random
                delay_time = random.uniform(self.delay * 0.5, self.delay * 1.5)
            else:
                delay_time = self.delay
            
            wait_time = max(0, delay_time - elapsed)
            if wait_time > 0:
                logger.debug(f"Global delay: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例，用于测试"""
        with cls._lock:
            cls._instance = None


# 创建默认的全局延迟管理器实例
default_delay_manager = GlobalDelayManager()
