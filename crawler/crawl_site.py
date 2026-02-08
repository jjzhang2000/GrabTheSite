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
from config import EXCLUDE_LIST, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, ERROR_HANDLING_CONFIG, RESUME_CONFIG, JS_RENDERING_CONFIG
from utils.timestamp_utils import get_file_timestamp, get_remote_timestamp, should_update
from utils.error_handler import ErrorHandler
from utils.state_manager import StateManager
from utils.js_renderer import JSRenderer

# 获取 logger 实例
logger = setup_logger(__name__)


class CrawlSite:
    """网站抓取类，负责抓取网站内容并返回暂存的页面"""
    
    def __init__(self, target_url, max_depth, max_files, output_dir, threads=THREADS, plugin_manager=None, force_download=False):
        """初始化抓取器
        
        Args:
            target_url: 目标URL
            max_depth: 最大深度
            max_files: 最大文件数
            output_dir: 输出目录
            threads: 线程数
            plugin_manager: 插件管理器实例
            force_download: 是否强制重新下载页面
        """
        self.force_download = force_download
        self.target_url = target_url
        self.max_depth = max_depth
        self.max_files = max_files
        self.output_dir = output_dir
        self.threads = threads
        self.plugin_manager = plugin_manager
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
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler(
            retry_count=ERROR_HANDLING_CONFIG.get('retry_count', 3),
            retry_delay=ERROR_HANDLING_CONFIG.get('retry_delay', 2),
            exponential_backoff=ERROR_HANDLING_CONFIG.get('exponential_backoff', True),
            retryable_errors=ERROR_HANDLING_CONFIG.get('retryable_errors', [429, 500, 502, 503, 504]),
            fail_strategy=ERROR_HANDLING_CONFIG.get('fail_strategy', 'log')
        )
        
        # 初始化状态管理器
        self.resume_enabled = RESUME_CONFIG.get('enable', True)
        self.save_interval = RESUME_CONFIG.get('save_interval', 300)
        if self.resume_enabled:
            state_file = RESUME_CONFIG.get('state_file', 'state/grabthesite.json')
            # 如果状态文件路径是相对路径，转换为绝对路径
            if not os.path.isabs(state_file):
                state_file = os.path.join(os.getcwd(), state_file)
            self.state_manager = StateManager(state_file)
            # 从状态管理器加载已访问的URL
            if not self.force_download:
                self.visited_urls.update(self.state_manager.state.get('visited_urls', set()))
        else:
            self.state_manager = None
        
        # 初始化JavaScript渲染器
        self.js_rendering_enabled = JS_RENDERING_CONFIG.get('enable', False)
        self.js_rendering_timeout = JS_RENDERING_CONFIG.get('timeout', 30)
        self.js_renderer = None
        if self.js_rendering_enabled:
            self.js_renderer = JSRenderer(enable=True, timeout=self.js_rendering_timeout)
            # 延迟初始化浏览器，避免在__init__中调用异步代码
            # 浏览器将在首次渲染时自动初始化
        
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
        
        # 检查JavaScript渲染状态
        if self.js_rendering_enabled:
            logger.info(f"JavaScript渲染已启用，超时设置: {self.js_rendering_timeout}秒")
        else:
            logger.info("JavaScript渲染已禁用")
        
        # 检查是否启用断点续传
        if self.resume_enabled and self.state_manager:
            logger.info(f"断点续传已启用，状态文件: {self.state_manager.state_file}")
            logger.info(f"已访问 URL 数量: {len(self.visited_urls)}")
        
        # 添加初始任务到队列
        # 只有当目标URL未被访问过时才添加到队列
        if self.target_url not in self.visited_urls:
            self.queue.put((self.target_url, 0))
        else:
            logger.info(f"目标 URL 已访问过，跳过: {self.target_url}")
        
        # 开始多线程抓取
        logger.info(f"开始多线程抓取，线程数: {self.threads}")
        
        # 创建并启动线程
        workers = []
        for _ in range(self.threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = False  # 设置为非守护线程，确保任务完成
            worker.start()
            workers.append(worker)
        
        # 等待队列中的所有任务完成
        self.queue.join()
        
        # 等待所有线程结束（使用更长的超时时间）
        for worker in workers:
            worker.join(timeout=60)  # 增加到60秒超时，确保任务有足够时间完成
            if worker.is_alive():
                logger.warning("工作线程超时，强制结束")
        
        # 保存最终状态
        if self.resume_enabled and self.state_manager:
            logger.info("保存最终抓取状态...")
            self.state_manager.save_state()
            stats = self.state_manager.get_stats()
            logger.info(f"抓取统计信息:")
            logger.info(f"  总访问 URL 数量: {stats.get('total_urls', 0)}")
            logger.info(f"  已下载文件数量: {stats.get('downloaded_files', 0)}")
            logger.info(f"  失败 URL 数量: {stats.get('failed_urls', 0)}")
        
        # 清理JavaScript渲染器
        if self.js_rendering_enabled and self.js_renderer:
            logger.info("关闭JavaScript渲染器...")
            self.js_renderer.close_sync()
        
        logger.info(f"抓取完成，共下载 {self.downloaded_files} 个页面")
        logger.info(f"暂存页面数量: {len(self.pages)}")
        return self.pages
    
    def _worker(self):
        """工作线程函数"""
        while True:
            # 检查是否达到文件数量限制
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    break
            try:
                url, depth = self.queue.get(block=True, timeout=1)
                task_completed = False
                try:
                    # 检查是否已访问过该URL
                    with self.lock:
                        if url in self.visited_urls:
                            task_completed = True
                            return
                    
                    # 检查是否在排除列表中
                    if self._is_in_exclude_list(url):
                        logger.info(f"URL在排除列表中，跳过: {url}")
                        task_completed = True
                        return
                    
                    # 检查是否在起始目录及其子目录中
                    if not self._is_in_target_directory(url):
                        task_completed = True
                        return
                    
                    # 抓取页面
                    self._crawl_page(url, depth)
                    task_completed = True
                finally:
                    # 确保 task_done() 只被调用一次
                    if task_completed:
                        self.queue.task_done()
                    
            except queue.Empty:
                # 检查是否真的完成了所有任务
                with self.lock:
                    if self.queue.empty() and self.downloaded_files < self.max_files:
                        # 队列空了但还没达到文件限制，继续等待
                        # 给其他线程一些时间来添加新任务
                        time.sleep(0.1)
                        continue
                    else:
                        break
            except (IOError, OSError) as e:
                logger.error(f"文件操作失败: {e}")
            except requests.RequestException as e:
                logger.error(f"网络请求失败: {e}")
    
    def _fetch_page_content(self, url):
        """获取页面内容，使用错误处理器进行重试
        
        Args:
            url: 页面URL
            
        Returns:
            str: 页面内容，如果获取失败返回None
        """
        headers = {'User-Agent': USER_AGENT}
        
        # 尝试使用JavaScript渲染
        if self.js_rendering_enabled and self.js_renderer:
            logger.debug(f"尝试使用JavaScript渲染页面: {url}")
            page_content = self.js_renderer.render_page_sync(url)
            if page_content:
                return page_content
        
        # 使用常规HTTP请求，使用类中配置的错误处理器进行重试
        @self.error_handler.retry
        def _do_request():
            from config import DEFAULT_REQUEST_TIMEOUT
            response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        
        return _do_request()
    
    def _crawl_page(self, url: str, depth: int) -> None:
        """抓取单个页面
        
        该方法是抓取的核心逻辑，包括：
        1. 检查深度和访问状态
        2. 检查文件更新需求
        3. 获取页面内容
        4. 暂存页面（如果需要）
        5. 提取并下载静态资源
        6. 提取页面链接并添加到队列
        
        Args:
            url: 要抓取的页面URL
            depth: 当前抓取深度
        """
        # 检查是否达到深度限制
        if depth > self.max_depth:
            return
        
        # 检查是否已访问过该URL
        with self.lock:
            if url in self.visited_urls:
                return
            # 标记为已访问
            self.visited_urls.add(url)
            # 更新状态管理器
            if self.resume_enabled and self.state_manager:
                self.state_manager.add_visited_url(url)
        
        # 计算本地文件路径
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path:
            path = '/'
        if path.endswith('/'):
            path += 'index.html'
        file_path = os.path.join(self.output_dir, path.lstrip('/'))
        
        # 检查是否需要更新
        local_timestamp = get_file_timestamp(file_path)
        remote_timestamp = get_remote_timestamp(url)
        
        # 检查是否需要下载该页面
        need_download = should_update(remote_timestamp, local_timestamp) or self.force_download
        
        # 如果需要下载，检查是否达到文件数量限制
        if need_download:
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    # 达到文件数量限制，不处理该页面
                    logger.info(f"达到文件数量限制，跳过页面: {url}")
                    return
        
        # 获取网页内容（无论是否需要更新，都需要获取内容来处理链接）
        logger.info(f"抓取页面: {url}")
        
        page_content = self._fetch_page_content(url)
        if not page_content:
            logger.error(f"获取页面内容失败: {url}")
            return
        
        # 调用插件的on_page_crawled钩子
        if self.plugin_manager:
            self.plugin_manager.call_hook("on_page_crawled", url, page_content)
        
        # 如果需要下载，暂存页面内容到内存
        if need_download:
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    # 再次检查文件数量限制，避免竞争条件
                    logger.info(f"达到文件数量限制，跳过页面: {url}")
                    return
                self.pages[url] = page_content
                self.downloaded_files += 1
                # 更新状态管理器
                if self.resume_enabled and self.state_manager:
                    self.state_manager.add_downloaded_file(file_path)
            logger.info(f"暂存页面: {url}")
        else:
            logger.info(f"页面已最新，跳过下载: {url}")
        
        # 检查是否需要保存状态
        if self.resume_enabled and self.state_manager:
            if self.state_manager.should_save(self.save_interval):
                self.state_manager.save_state()
        
        # 解析HTML，提取链接
        soup = BeautifulSoup(page_content, 'html.parser')
        
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
        
        # 多线程下载静态资源
        if static_urls:
            downloader = Downloader(self.output_dir, threads=self.threads, state_manager=self.state_manager)
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
    
    def _is_same_domain(self, url: str) -> bool:
        """检查是否为同域名
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: 是否与目标URL同域名
        """
        target_domain = urlparse(self.target_url).netloc
        current_domain = urlparse(url).netloc
        return target_domain == current_domain
    
    def _is_in_target_directory(self, url: str) -> bool:
        """检查 URL 是否在起始目录及其子目录中
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: URL是否在起始目录及其子目录中
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
