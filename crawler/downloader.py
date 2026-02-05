# 文件下载模块

import os
import time
import random
import threading
import queue
import requests
from urllib.parse import urlparse
from logger import setup_logger
from config import DELAY, RANDOM_DELAY, THREADS

# 获取 logger 实例
logger = setup_logger(__name__)


class Downloader:
    """文件下载器，支持多线程下载"""
    
    def __init__(self, output_dir, threads=THREADS):
        """初始化下载器
        
        Args:
            output_dir: 输出目录
            threads: 线程数
        """
        self.output_dir = output_dir
        self.threads = threads
        self.queue = queue.Queue()
        self.results = []
        self.lock = threading.Lock()
    
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
                logger.error(f"线程工作失败: {e}")
            finally:
                self.queue.task_done()
    
    def _download_file(self, url):
        """下载单个文件
        
        Args:
            url: 文件URL
        
        Returns:
            str: 下载的文件路径，如果下载失败返回None
        """
        try:
            logger.info(f"下载文件: {url}")
            
            # 解析URL
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # 获取文件名
            filename = os.path.basename(path)
            
            # 如果没有文件名，跳过
            if not filename:
                logger.info(f"跳过，无文件名: {url}")
                return None
            
            # 构建保存路径，保留目录结构
            file_path = os.path.join(self.output_dir, path.lstrip('/'))
            
            # 创建目录结构
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 下载文件
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()  # 检查HTTP错误
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"保存文件: {file_path}")
            
            # 添加延迟
            add_delay()
            
            return file_path
            
        except Exception as e:
            logger.error(f"下载失败: {url}, 错误: {str(e)}")
            
            # 添加延迟
            add_delay()
            
            return None
    
    def run(self):
        """运行多线程下载
        
        Returns:
            list: 下载结果列表，每个元素是(url, file_path)元组
        """
        logger.info(f"开始多线程下载，线程数: {self.threads}")
        
        # 创建并启动线程
        workers = []
        for _ in range(self.threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            workers.append(worker)
        
        # 等待所有线程完成
        self.queue.join()
        
        # 等待所有线程结束
        for worker in workers:
            worker.join()
        
        logger.info(f"多线程下载完成，共处理 {len(self.results)} 个文件")
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
            logger.debug(f"添加随机延迟: {delay_time:.2f} 秒")
        else:
            # 固定延迟
            delay_time = DELAY
            logger.debug(f"添加固定延迟: {delay_time:.2f} 秒")
        
        time.sleep(delay_time)
