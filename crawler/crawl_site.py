"""网站抓取模块

核心抓取逻辑，负责：
1. 多线程抓取网页
2. 链接提取和转换
3. 静态资源URL收集（供save插件下载）
4. 增量更新支持
5. 断点续传支持
"""

import os
import time
import random
import threading
import queue
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from crawler.downloader import download_file
from logger import setup_logger, _ as _t
from config import EXCLUDE_LIST, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, ERROR_HANDLING_CONFIG, JS_RENDERING_CONFIG
from utils.timestamp_utils import get_file_timestamp, get_remote_timestamp, should_update
from utils.error_handler import ErrorHandler
from utils.state_manager import StateManager
from utils.js_renderer import get_js_renderer, close_js_renderer

# 获取 logger 实例
logger = setup_logger(__name__)


class CrawlSite:
    """网站抓取类，负责抓取网站内容并返回暂存的页面"""
    
    def __init__(self, target_url, max_depth, max_files, output_dir, threads=THREADS, plugin_manager=None, force_download=False, stop_event=None):
        """初始化抓取器
        
        Args:
            target_url: 目标URL
            max_depth: 最大深度
            max_files: 最大文件数
            output_dir: 输出目录
            threads: 线程数
            plugin_manager: 插件管理器实例
            force_download: 是否强制重新下载页面
            stop_event: 停止事件，用于通知抓取线程停止
        """
        self.force_download = force_download
        self.stop_event = stop_event  # 停止事件
        self.target_url = target_url
        self.max_depth = max_depth
        self.max_files = max_files
        self.output_dir = output_dir
        self.threads = threads
        self.plugin_manager = plugin_manager
        self.downloaded_files = 0
        self.visited_urls = set()
        self.lock = threading.Lock()
        # 使用 LifoQueue 实现深度优先搜索（DFS）
        # 这样站点地图可以体现上下级层级关系
        self.queue = queue.LifoQueue()
        
        self.exclude_list = EXCLUDE_LIST or []
        
        # 页面暂存机制：URL -> 页面内容
        self.pages = {}
        # 页面深度记录：URL -> 下载深度
        self.page_depths = {}
        # 静态资源记录：URL集合（供save插件使用）
        self.static_resources = set()
        
        # 提取并标准化起始目录路径（确保以/结尾）
        parsed_target = urlparse(self.target_url)
        self.target_directory = parsed_target.path
        if not self.target_directory.endswith('/'):
            self.target_directory += '/'
        
        # 标准化排除列表URL
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
        
        # 初始化状态管理器（断点续传默认开启）
        self.resume_enabled = True
        self.save_interval = 300
        state_file = 'logs/grabthesite.json'
        # 如果状态文件路径是相对路径，转换为绝对路径
        if not os.path.isabs(state_file):
            state_file = os.path.join(os.getcwd(), state_file)
        
        # 每次开始抓取前，删除状态文件以清理之前的记录
        # 这样可以确保从头开始抓取，而不是基于之前的状态
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
                logger.info(_t("已清理抓取状态文件") + f": {state_file}")
            except (IOError, OSError) as e:
                logger.warning(_t("清理状态文件失败") + f": {e}")
        
        self.state_manager = StateManager(state_file)
        # 从状态管理器加载已访问的URL（状态文件已被清理，从头开始）
        if not self.force_download:
            self.visited_urls.update(self.state_manager.state.get('visited_urls', set()))
        
        # 初始化JavaScript渲染器（使用专用渲染线程）
        self.js_rendering_enabled = JS_RENDERING_CONFIG.get('enable', False)
        self.js_rendering_timeout = JS_RENDERING_CONFIG.get('timeout', 30)
        # 使用全局渲染器实例（延迟初始化）
        
        # 打印排除列表信息
        if self.processed_exclude_list:
            logger.info(_t("排除列表") + f": {self.processed_exclude_list}")
        else:
            logger.info(_t("排除列表为空"))
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def crawl_site(self):
        """开始抓取网站
        
        Returns:
            dict: 暂存的页面内容，键为URL，值为页面内容
        """
        logger.info(_t("开始抓取网站") + f": {self.target_url}")
        logger.info(_t("保存路径") + f": {self.output_dir}")
        logger.info(_t("最大深度") + f": {self.max_depth}")
        logger.info(_t("最大文件数") + f": {self.max_files}")
        logger.info(_t("线程数") + f": {self.threads}")
        
        # 检查JavaScript渲染状态
        if self.js_rendering_enabled:
            logger.info(_t("JavaScript渲染已启用，超时设置") + f": {self.js_rendering_timeout}" + _t("秒"))
        else:
            logger.info(_t("JavaScript渲染已禁用"))
        

        
        # 检查是否启用断点续传
        if self.resume_enabled and self.state_manager:
            logger.info(_t("断点续传已启用，状态文件") + f": {self.state_manager.state_file}")
            logger.info(_t("已访问 URL 数量") + f": {len(self.visited_urls)}")
        
        # 添加初始任务到队列
        # 只有当目标URL未被访问过时才添加到队列
        if self.target_url not in self.visited_urls:
            self.queue.put((self.target_url, 0))
        else:
            logger.info(_t("目标 URL 已访问过，跳过") + f": {self.target_url}")
        
        # 开始多线程抓取
        logger.info(_t("开始多线程抓取，线程数") + f": {self.threads}")
        
        # 创建并启动线程
        workers = []
        for _ in range(self.threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = False  # 设置为非守护线程，确保任务完成
            worker.start()
            workers.append(worker)
        
        # 等待队列中的所有任务完成
        self.queue.join()
        
        # 等待所有工作线程结束（使用更长的超时时间）
        for worker in workers:
            worker.join(timeout=60)  # 增加到60秒超时，确保任务有足够时间完成
            if worker.is_alive():
                logger.warning(_t("工作线程超时，强制结束"))
        

        
        # 保存最终状态
        if self.resume_enabled and self.state_manager:
            logger.info(_t("保存最终抓取状态..."))
            self.state_manager.save_state()
            stats = self.state_manager.get_stats()
            logger.info(_t("抓取统计信息:"))
            logger.info("  " + _t("总访问 URL 数量") + f": {stats.get('total_urls', 0)}")
            logger.info("  " + _t("已下载文件数量") + f": {stats.get('downloaded_files', 0)}")
            logger.info("  " + _t("失败 URL 数量") + f": {stats.get('failed_urls', 0)}")
        
        # 清理JavaScript渲染器
        if self.js_rendering_enabled:
            logger.info(_t("关闭JavaScript渲染器..."))
            close_js_renderer()
        
        logger.info(_t("抓取完成，共下载") + f" {self.downloaded_files} " + _t("个页面"))
        logger.info(_t("暂存页面数量") + f": {len(self.pages)}")
        return self.pages
    
    def _worker(self):
        """工作线程函数"""
        while True:
            # 检查是否收到停止信号
            if self.stop_event and self.stop_event.is_set():
                logger.info(_t("工作线程收到停止信号，正在退出..."))
                break
            
            # 检查是否达到文件数量限制
            reached_limit = False
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    reached_limit = True
            
            try:
                # 如果已达到文件限制，以非阻塞方式清空队列
                if reached_limit:
                    try:
                        url, depth = self.queue.get(block=False)
                        # 直接标记完成，不处理
                        self.queue.task_done()
                        continue
                    except queue.Empty:
                        # 队列已空，可以退出
                        break
                
                # 正常获取任务
                url, depth = self.queue.get(block=True, timeout=0.5)
                task_completed = False
                should_break = False
                
                try:
                    # 检查是否收到停止信号
                    if self.stop_event and self.stop_event.is_set():
                        logger.info(_t("任务处理前收到停止信号，跳过任务"))
                        task_completed = True
                        should_break = True
                    
                    # 检查是否已访问过该URL
                    if not should_break:
                        with self.lock:
                            if url in self.visited_urls:
                                task_completed = True
                    
                    # 检查是否在排除列表中
                    if not task_completed and self._is_in_exclude_list(url):
                        logger.info(_t("URL在排除列表中，跳过") + f": {url}")
                        task_completed = True
                    
                    # 检查是否在起始目录及其子目录中
                    if not task_completed and not self._is_in_target_directory(url):
                        task_completed = True
                    
                    # 检查是否达到文件数量限制（再次检查）
                    if not task_completed:
                        with self.lock:
                            if self.downloaded_files >= self.max_files:
                                task_completed = True
                    
                    # 抓取页面
                    if not task_completed:
                        self._crawl_page(url, depth)
                        task_completed = True
                except (IOError, OSError) as e:
                    logger.error(_t("文件操作失败") + f": {e}")
                except requests.RequestException as e:
                    logger.error(_t("网络请求失败") + f": {e}")
                except Exception as e:
                    logger.error(_t("抓取页面失败") + f": {url}, " + _t("错误") + f": {e}")
                finally:
                    # 确保 task_done() 被调用
                    self.queue.task_done()
                
                # 如果需要退出循环
                if should_break:
                    break
                    
            except queue.Empty:
                # 队列空了，退出
                break
    
    def _fetch_page_content(self, url):
        """获取页面内容，使用错误处理器进行重试
        
        使用专用JS渲染线程，避免多线程竞争导致的线程泄漏。
        
        Args:
            url: 页面URL
            
        Returns:
            str: 页面内容，如果获取失败返回None
        """
        headers = {'User-Agent': USER_AGENT}
        
        # 尝试使用JavaScript渲染（通过专用线程）
        if self.js_rendering_enabled:
            logger.debug(_t("尝试使用JavaScript渲染页面") + f": {url}")
            js_renderer = get_js_renderer(enable=True, timeout=self.js_rendering_timeout)
            if js_renderer:
                page_content = js_renderer.render_page(url, timeout=self.js_rendering_timeout + 10)
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
        
        # 计算本地文件路径（提前计算用于检查文件存在性）
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path:
            path = '/'
        if path.endswith('/'):
            path += 'index.html'
        file_path = os.path.join(self.output_dir, path.lstrip('/'))
        
        # 检查是否已访问过该URL
        with self.lock:
            if url in self.visited_urls:
                return
            # 标记为已访问
            self.visited_urls.add(url)
            # 更新状态管理器
            if self.resume_enabled and self.state_manager:
                self.state_manager.add_visited_url(url)
        
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
                    logger.info(_t("达到文件数量限制，跳过页面") + f": {url}")
                    return
        
        # 获取网页内容（无论是否需要更新，都需要获取内容来处理链接）
        logger.info(_t("抓取页面") + f": {url}")
        
        page_content = self._fetch_page_content(url)
        if not page_content:
            logger.error(_t("获取页面内容失败") + f": {url}")
            return
        
        # 调用插件的on_page_crawled钩子
        if self.plugin_manager:
            self.plugin_manager.call_hook("on_page_crawled", url, page_content)
        
        # 如果需要下载，暂存页面内容到内存
        if need_download:
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    # 再次检查文件数量限制，避免竞争条件
                    logger.info(_t("达到文件数量限制，跳过页面") + f": {url}")
                    return
                self.pages[url] = page_content
                self.page_depths[url] = depth
                self.downloaded_files += 1
                # 更新状态管理器
                if self.resume_enabled and self.state_manager:
                    self.state_manager.add_downloaded_file(file_path)
            logger.info(_t("暂存页面") + f": {url}")
        else:
            logger.info(_t("页面已最新，跳过下载") + f": {url}")
        
        # 检查是否需要保存状态
        if self.resume_enabled and self.state_manager:
            if self.state_manager.should_save(self.save_interval):
                self.state_manager.save_state()
        
        # 解析HTML，提取链接
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # 提取所有链接
        links = soup.find_all(['a', 'img', 'link', 'script'])
        
        # 收集静态资源链接（供save插件下载）
        for link in links:
            if link.name in ['img', 'link', 'script']:
                src = link.get('src') or link.get('href')
                if src:
                    full_url = urljoin(url, src)
                    # 规范化 URL（移除片段，统一格式）
                    full_url = self._normalize_url(full_url)
                    # 只记录同域名且在目标目录中的静态资源
                    if self._is_same_domain(full_url) and self._is_in_target_directory(full_url):
                        with self.lock:
                            self.static_resources.add(full_url)
        
        # 处理页面链接
        # 先收集所有子链接，然后倒序，再用 LifoQueue 实现深度优先且保持原始顺序
        child_urls = []
        for link in links:
            if link.name == 'a':
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    # 只抓取同域名、在起始目录及其子目录中、并且深度小于最大深度的链接
                    if self._is_same_domain(full_url) and self._is_in_target_directory(full_url) and depth < self.max_depth:
                        # 检查是否已访问过该URL
                        with self.lock:
                            if full_url not in self.visited_urls:
                                child_urls.append(full_url)
        
        # 倒序后加入队列（配合 LifoQueue 实现深度优先且保持原始顺序）
        for full_url in reversed(child_urls):
            # 检查是否达到文件数量限制
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    break
            self.queue.put((full_url, depth + 1))
        
        # 添加延迟
        self._add_delay()
    
    def _normalize_url(self, url: str) -> str:
        """规范化 URL
        
        统一 URL 格式，用于比较和去重：
        - 移除 URL 片段（#后面的内容）
        - 统一小写（域名部分）
        
        Args:
            url: 原始 URL
            
        Returns:
            str: 规范化后的 URL
        """
        parsed = urlparse(url)
        # 移除片段，小写化 netloc
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    
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
                logger.debug(_t("添加随机延迟") + f": {delay_time:.2f} " + _t("秒"))
            else:
                # 固定延迟
                delay_time = DELAY
                logger.debug(_t("添加固定延迟") + f": {delay_time:.2f} " + _t("秒"))
            
            time.sleep(delay_time)
