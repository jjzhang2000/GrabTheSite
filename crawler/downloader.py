"""文件下载模块

多线程文件下载器：
- 支持并发下载
- 断点续传支持
- 全局速率限制
"""

import os
import time
import random
import threading
import queue
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse
from logger import setup_logger, _ as _t
from config import DELAY, RANDOM_DELAY, THREADS, ERROR_HANDLING_CONFIG, USER_AGENT
from utils.timestamp_utils import get_file_timestamp, get_remote_timestamp, should_update
from utils.error_handler import ErrorHandler, retry
from utils.state_manager import StateManager
from utils.rate_limiter import GlobalDelayManager

# 创建 session，禁用连接池线程
_download_session = requests.Session()
_download_session.headers.update({'Connection': 'close'})
_download_adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
_download_session.mount('http://', _download_adapter)
_download_session.mount('https://', _download_adapter)

# 获取 logger 实例
logger = setup_logger(__name__)


class Downloader:
    """文件下载器，用于多线程下载静态资源"""
    
    def __init__(self, output_dir, threads=THREADS, state_manager=None):
        """初始化下载器
        
        Args:
            output_dir: 输出目录
            threads: 线程数
            state_manager: 状态管理器实例，用于断点续传
        """
        self.output_dir = output_dir
        self.threads = threads
        self.queue = queue.Queue()
        self.results = []
        self.lock = threading.Lock()
        self.state_manager = state_manager
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler(
            retry_count=ERROR_HANDLING_CONFIG.get('retry_count', 3),
            retry_delay=ERROR_HANDLING_CONFIG.get('retry_delay', 2),
            exponential_backoff=ERROR_HANDLING_CONFIG.get('exponential_backoff', True),
            retryable_errors=ERROR_HANDLING_CONFIG.get('retryable_errors', [429, 500, 502, 503, 504]),
            fail_strategy=ERROR_HANDLING_CONFIG.get('fail_strategy', 'log')
        )
        
        # 初始化全局延迟管理器
        self.delay_manager = GlobalDelayManager(DELAY, RANDOM_DELAY)
    
    def add_task(self, url):
        """添加下载任务
        
        Args:
            url: 文件URL
        """
        self.queue.put(url)
    
    def _worker(self):
        """工作线程函数"""
        while not self.queue.empty():
            try:
                url = self.queue.get(block=False)
                result = self._download_file(url)
                with self.lock:
                    self.results.append((url, result))
            except queue.Empty:
                break
            except Exception as e:
                logger.error(_t("线程工作失败") + f": {e}")
            finally:
                self.queue.task_done()
    
    @retry()
    def _download_file(self, url):
        """下载单个文件
        
        Args:
            url: 文件URL
        
        Returns:
            str: 下载的文件路径，如果下载失败返回None
        """
        logger.info(_t("下载文件") + f": {url}")
        
        # 解析URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 获取文件名
        filename = os.path.basename(path)
        
        # 如果没有文件名，跳过
        if not filename:
            logger.info(_t("跳过，无文件名") + f": {url}")
            return None
        
        # 构建保存路径，保留目录结构
        file_path = os.path.join(self.output_dir, path.lstrip('/'))
        
        # 检查状态管理器，避免重复下载
        if self.state_manager and self.state_manager.is_file_downloaded(file_path):
            logger.info(_t("文件已下载，跳过") + f": {url}")
            return file_path
        
        # 创建目录结构
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 检查是否需要更新
        local_timestamp = get_file_timestamp(file_path)
        remote_timestamp = get_remote_timestamp(url)
        
        if not should_update(remote_timestamp, local_timestamp):
            logger.info(_t("文件已最新，跳过下载") + f": {url}")
            # 更新状态管理器
            if self.state_manager:
                self.state_manager.add_downloaded_file(file_path)
            return file_path
        
        # 使用全局延迟管理器
        self.delay_manager.wait()
        
        # 下载文件
        headers = {
            'User-Agent': USER_AGENT
        }
        from config import DEFAULT_REQUEST_TIMEOUT, DEFAULT_CHUNK_SIZE
        response = _download_session.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()  # 检查HTTP错误
        
        # 保存文件
        CHUNK_SIZE = 8192  # 8KB chunks
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        
        logger.info(_t("保存文件") + f": {file_path}")
        
        # 更新状态管理器
        if self.state_manager:
            self.state_manager.add_downloaded_file(file_path)
        
        return file_path
    
    def run(self):
        """运行多线程下载
        
        Returns:
            list: 下载结果列表，每个元素是(url, file_path)元组
        """
        logger.info(_t("开始多线程下载，线程数") + f": {self.threads}")
        
        # 创建并启动线程
        workers = []
        for i in range(self.threads):
            worker = threading.Thread(target=self._worker, name=f"DownloaderWorker-{i}")
            worker.daemon = True  # 改为守护线程，避免线程泄漏
            worker.start()
            workers.append(worker)
        
        # 等待所有线程完成
        self.queue.join()
        
        # 等待所有线程结束
        for worker in workers:
            worker.join()
        
        logger.info(_t("多线程下载完成，共处理") + f" {len(self.results)} " + _t("个文件"))
        return self.results


def download_file(url, output_dir):
    """下载单个文件
    
    Args:
        url: 文件URL
        output_dir: 输出目录
    
    Returns:
        str: 下载的文件路径，如果下载失败返回None
    """
    downloader = Downloader(output_dir, threads=1)
    downloader.add_task(url)
    results = downloader.run()
    return results[0][1] if results else None


def add_delay():
    """添加延迟，避免对目标服务器造成过大压力
    
    支持固定延迟和随机延迟两种模式
    """
    if DELAY > 0:
        if RANDOM_DELAY:
            # 随机延迟：0.5 到 1.5 倍的配置延迟时间
            delay_time = random.uniform(DELAY * 0.5, DELAY * 1.5)
            logger.debug(_t("添加随机延迟") + f": {delay_time:.2f} " + _t("秒"))
        else:
            # 固定延迟
            delay_time = DELAY
            logger.debug(_t("添加固定延迟") + f": {delay_time:.2f} " + _t("秒"))
        
        time.sleep(delay_time)
