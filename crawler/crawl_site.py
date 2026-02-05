# 网站抓取类

import os
import time
import random
import threading
import queue
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from crawler.downloader import download_file, Downloader
from logger import setup_logger
from config import EXCLUDE_LIST, DELAY, RANDOM_DELAY, THREADS

# 获取 logger 实例
logger = setup_logger(__name__)


class CrawlSite:
    """网站抓取类，负责抓取网站内容并返回暂存的页面"""
    
    def __init__(self, target_url, max_depth, max_files, output_dir, threads=THREADS):
        """初始化抓取器
        
        Args:
            target_url: 目标URL
            max_depth: 最大深度
            max_files: 最大文件数
            output_dir: 输出目录
            threads: 线程数
        """
        self.target_url = target_url
        self.max_depth = max_depth
        self.max_files = max_files
        self.output_dir = output_dir
        self.threads = threads
        self.downloaded_files = 0
        self.visited_urls = set()
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        
        # 从配置中获取排除列表
        self.exclude_list = EXCLUDE_LIST or []
        
        # 页面暂存机制
        self.pages = {}  # 暂存下载的页面内容，键为URL，值为页面内容
        self.static_resources = set()  # 记录已下载的静态资源URL
        
        # 提取起始目录路径
        parsed_target = urlparse(self.target_url)
        self.target_directory = parsed_target.path
        # 确保路径以/结尾
        if not self.target_directory.endswith('/'):
            self.target_directory += '/'
        
        # 处理排除列表，确保每个URL都以/结尾
        self.processed_exclude_list = []
        for url in self.exclude_list:
            parsed_url = urlparse(url)
            path = parsed_url.path
            if not path.endswith('/'):
                path += '/'
            full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
            self.processed_exclude_list.append(full_url)
        
        # 打印排除列表信息
        if self.processed_exclude_list:
            logger.info(f"排除列表: {self.processed_exclude_list}")
        else:
            logger.info("排除列表为空")
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def crawl_site(self):
        """开始抓取网站
        
        Returns:
            dict: 暂存的页面内容，键为URL，值为页面内容
        """
        logger.info(f"开始抓取网站: {self.target_url}")
        logger.info(f"保存路径: {self.output_dir}")
        logger.info(f"最大深度: {self.max_depth}")
        logger.info(f"最大文件数: {self.max_files}")
        logger.info(f"线程数: {self.threads}")
        
        # 添加初始任务到队列
        self.queue.put((self.target_url, 0))
        
        # 开始多线程抓取
        logger.info(f"开始多线程抓取，线程数: {self.threads}")
        
        # 创建并启动线程
        workers = []
        for _ in range(self.threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            workers.append(worker)
        
        # 等待队列处理完成
        self.queue.join()
        
        # 等待所有线程结束
        for worker in workers:
            worker.join()
        
        logger.info(f"抓取完成，共下载 {self.downloaded_files} 个页面")
        return self.pages
    
    def _worker(self):
        """工作线程函数"""
        while not self.queue.empty():
            try:
                url, depth = self.queue.get(block=False)
                # 检查是否达到文件数量限制
                with self.lock:
                    if self.downloaded_files >= self.max_files:
                        self.queue.task_done()
                        break
                # 检查是否已访问过该URL
                with self.lock:
                    if url in self.visited_urls:
                        self.queue.task_done()
                        continue
                # 检查是否在排除列表中
                if self._is_in_exclude_list(url):
                    logger.info(f"URL在排除列表中，跳过: {url}")
                    self.queue.task_done()
                    continue
                # 检查是否在起始目录及其子目录中
                if not self._is_in_target_directory(url):
                    self.queue.task_done()
                    continue
                # 抓取页面
                self._crawl_page(url, depth)
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"线程工作失败: {e}")
            finally:
                try:
                    self.queue.task_done()
                except:
                    pass
    
    def _crawl_page(self, url, depth):
        """抓取页面"""
        # 检查是否达到深度限制
        if depth > self.max_depth:
            return
        
        try:
            # 标记为已访问
            with self.lock:
                if url in self.visited_urls:
                    return
                self.visited_urls.add(url)
            
            # 检查是否达到文件数量限制
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    return
            
            # 获取网页内容
            logger.info(f"抓取页面: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            # 暂存页面内容到内存
            with self.lock:
                self.pages[url] = response.text
                self.downloaded_files += 1
            logger.info(f"暂存页面: {url}")
            
            # 解析HTML，提取链接
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有链接
            links = soup.find_all(['a', 'img', 'link', 'script'])
            
            # 收集静态资源链接
            static_urls = []
            for link in links:
                if link.name in ['img', 'link', 'script']:
                    src = link.get('src') or link.get('href')
                    if src:
                        full_url = urljoin(url, src)
                        # 只下载同域名的静态资源
                        if self._is_same_domain(full_url):
                            static_urls.append(full_url)
            
            # 特别查找并处理 oldlens.jpg 图片
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and 'oldlens.jpg' in src:
                    full_url = urljoin(url, src)
                    if self._is_same_domain(full_url) and full_url not in static_urls:
                        static_urls.append(full_url)
            
            # 多线程下载静态资源
            if static_urls:
                downloader = Downloader(self.output_dir, threads=self.threads)
                for static_url in static_urls:
                    downloader.add_task(static_url)
                results = downloader.run()
                # 记录已下载的静态资源
                with self.lock:
                    for static_url, file_path in results:
                        if file_path:
                            self.static_resources.add(static_url)
            
            # 处理页面链接
            for link in links:
                if link.name == 'a':
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        # 只抓取同域名、在起始目录及其子目录中、并且深度小于最大深度的链接
                        if self._is_same_domain(full_url) and self._is_in_target_directory(full_url) and depth < self.max_depth:
                            # 检查是否达到文件数量限制
                            with self.lock:
                                if self.downloaded_files >= self.max_files:
                                    break
                                # 检查是否已访问过该URL
                                if full_url not in self.visited_urls:
                                    # 添加到队列
                                    self.queue.put((full_url, depth + 1))
            
            # 添加延迟
            self._add_delay()
                            
        except Exception as e:
            logger.error(f"抓取失败: {url}, 错误: {str(e)}")
            
            # 添加延迟
            self._add_delay()
    
    def _is_same_domain(self, url):
        """检查是否为同域名"""
        target_domain = urlparse(self.target_url).netloc
        current_domain = urlparse(url).netloc
        return target_domain == current_domain
    
    def _is_in_target_directory(self, url):
        """检查 URL 是否在起始目录及其子目录中
        
        Args:
            url: 要检查的 URL
            
        Returns:
            布尔值，表示该 URL 是否在起始目录及其子目录中
        """
        parsed_url = urlparse(url)
        url_path = parsed_url.path
        
        # 确保 url_path 以/结尾，以便正确比较
        if not url_path.endswith('/'):
            url_path += '/'
        
        # 检查 url_path 是否以 self.target_directory 开头
        return url_path.startswith(self.target_directory)
    
    def _is_in_exclude_list(self, url):
        """检查 URL 是否在排除列表中或其子目录中
        
        Args:
            url: 要检查的 URL
            
        Returns:
            布尔值，表示该 URL 是否在排除列表中或其子目录中
        """
        for exclude_url in self.processed_exclude_list:
            if url.startswith(exclude_url):
                return True
        return False
    
    def _add_delay(self):
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
