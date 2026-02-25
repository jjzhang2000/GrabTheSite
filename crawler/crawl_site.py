"""网站抓取模块

核心抓取逻辑，负责：
1. 多线程抓取网页
2. 链接提取和转换
3. 静态资源URL收集（供save插件下载）
4. 增量更新支持
5. 断点续传支持

注意：此模块现在使用拆分后的组件：
- URLFilter: URL 过滤
- LinkExtractor: 链接提取
- Fetcher: 页面获取
"""

import os
import queue
import random
import threading
import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from app_config import DELAY, EXCLUDE_LIST, RANDOM_DELAY, THREADS
from crawler.fetcher import Fetcher
from crawler.link_extractor import LinkExtractor
from crawler.url_filter import URLFilter
from logger import _ as _t
from logger import setup_logger
from utils.plugin_manager import PluginManager
from utils.state_manager import StateManager
from utils.timestamp_utils import get_file_timestamp, get_remote_timestamp, should_update
from utils.url_utils import normalize_url

# 获取 logger 实例
logger = setup_logger(__name__)


class CrawlSite:
    """网站抓取类，负责抓取网站内容并返回暂存的页面

    此类现在作为协调器，使用拆分后的组件完成具体任务：
    - URLFilter: URL 过滤逻辑
    - LinkExtractor: 链接提取
    - Fetcher: 页面获取
    """

    def __init__(
        self,
        target_url: str,
        max_depth: int,
        max_files: int,
        output_dir: str,
        threads: int = THREADS,
        plugin_manager: Optional[PluginManager] = None,
        force_download: bool = False,
        stop_event: Optional[threading.Event] = None
    ) -> None:
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
        self.force_download: bool = force_download
        self.stop_event: Optional[threading.Event] = stop_event
        self.target_url: str = target_url
        self.max_depth: int = int(max_depth)
        self.max_files: int = int(max_files)
        self.output_dir: str = output_dir
        self.threads: int = int(threads)
        self.plugin_manager: Optional[PluginManager] = plugin_manager
        self.downloaded_files: int = 0
        self.visited_urls: Set[str] = set()
        self.lock: threading.Lock = threading.Lock()
        # 使用 LifoQueue 实现深度优先搜索（DFS）
        self.queue: queue.LifoQueue = queue.LifoQueue()

        # 页面暂存机制：URL -> 页面内容
        self.pages: Dict[str, str] = {}
        # 页面深度记录：URL -> 下载深度
        self.page_depths: Dict[str, int] = {}
        # 静态资源记录：URL集合（供save插件使用）
        self.static_resources: Set[str] = set()

        # 初始化组件
        self.url_filter: URLFilter = URLFilter(target_url, EXCLUDE_LIST or [])
        self.link_extractor: LinkExtractor = LinkExtractor()
        self.fetcher: Fetcher = Fetcher()

        # 初始化状态管理器（断点续传默认开启）
        self.resume_enabled: bool = True
        self.save_interval: int = 300
        state_file: str = 'logs/grabthesite.json'
        # 如果状态文件路径是相对路径，转换为绝对路径
        if not os.path.isabs(state_file):
            state_file = os.path.join(os.getcwd(), state_file)

        # 每次开始抓取前，删除状态文件以清理之前的记录
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
                logger.info(_t("已清理抓取状态文件") + f": {state_file}")
            except (IOError, OSError) as e:
                logger.warning(_t("清理状态文件失败") + f": {e}")

        self.state_manager: StateManager = StateManager(state_file)
        # 从状态管理器加载已访问的URL
        if not self.force_download:
            self.visited_urls.update(self.state_manager.state.get('visited_urls', set()))

        # 打印排除列表信息
        if self.url_filter.exclude_patterns:
            logger.info(_t("排除列表") + f": {self.url_filter.exclude_patterns}")
        else:
            logger.info(_t("排除列表为空"))

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_site(self) -> Dict[str, str]:
        """开始抓取网站

        Returns:
            dict: 暂存的页面内容，键为URL，值为页面内容
        """
        logger.info(_t("开始抓取网站") + f": {self.target_url}")
        logger.info(_t("保存路径") + f": {self.output_dir}")
        logger.info(_t("最大深度") + f": {self.max_depth}")
        logger.info(_t("最大文件数") + f": {self.max_files}")
        logger.info(_t("线程数") + f": {self.threads}")

        # 检查是否启用断点续传
        if self.resume_enabled and self.state_manager:
            logger.info(_t("断点续传已启用"))
            logger.info(_t("已访问 URL 数量") + f": {len(self.visited_urls)}")

        # 添加初始任务到队列
        if self.target_url not in self.visited_urls:
            self.queue.put((self.target_url, 0))
        else:
            logger.info(_t("目标 URL 已访问过，跳过") + f": {self.target_url}")

        # 开始多线程抓取
        logger.info(_t("开始多线程抓取，线程数") + f": {self.threads}")

        # 创建并启动线程
        workers: List[threading.Thread] = []
        for i in range(self.threads):
            worker = threading.Thread(target=self._worker, name=f"CrawlerWorker-{i}")
            worker.daemon = True
            worker.start()
            workers.append(worker)

        # 等待队列中的所有任务完成
        self.queue.join()

        # 等待所有工作线程结束
        logger.info(_t("等待工作线程结束..."))
        for worker in workers:
            worker.join(timeout=30)
            if worker.is_alive():
                logger.warning(_t("工作线程未能及时结束") + f": {worker.name}")

        # 保存最终状态
        if self.resume_enabled and self.state_manager:
            logger.info(_t("保存最终抓取状态..."))
            self.state_manager.save_state()
            stats = self.state_manager.get_stats()
            logger.info(_t("抓取统计信息:"))
            logger.info("  " + _t("总访问 URL 数量") + f": {stats.get('total_urls', 0)}")
            logger.info("  " + _t("已下载文件数量") + f": {stats.get('downloaded_files', 0)}")
            logger.info("  " + _t("失败 URL 数量") + f": {stats.get('failed_urls', 0)}")

        # 清理资源
        self.fetcher.close()

        logger.info(_t("抓取完成，共下载") + f" {self.downloaded_files} " + _t("个页面"))
        logger.info(_t("暂存页面数量") + f": {len(self.pages)}")
        return self.pages

    def _worker(self) -> None:
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
                        self.queue.task_done()
                        continue
                    except queue.Empty:
                        break

                # 正常获取任务
                url, depth = self.queue.get(block=True, timeout=0.1)
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
                        normalized_url = normalize_url(url)
                        with self.lock:
                            if normalized_url in self.visited_urls:
                                task_completed = True

                    # 检查是否应该抓取该URL
                    if not task_completed and not self.url_filter.should_crawl(url):
                        task_completed = True

                    # 检查是否达到文件数量限制
                    if not task_completed:
                        with self.lock:
                            if self.downloaded_files >= self.max_files:
                                task_completed = True

                    # 抓取页面
                    if not task_completed:
                        self._crawl_page(url, depth)
                        task_completed = True

                except Exception as e:
                    logger.error(_t("抓取页面失败") + f": {url}, " + _t("错误") + f": {e}")
                finally:
                    self.queue.task_done()

                if should_break:
                    break

            except queue.Empty:
                break

    def _crawl_page(self, url: str, depth: int) -> None:
        """抓取单个页面

        Args:
            url: 要抓取的页面URL
            depth: 当前抓取深度
        """
        # 检查是否达到深度限制
        if depth > self.max_depth:
            return

        # 计算本地文件路径
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path:
            path = '/'
        if path.endswith('/'):
            path += 'index.html'
        file_path = os.path.join(self.output_dir, path.lstrip('/'))

        # 规范化URL用于去重检查
        normalized_url = normalize_url(url)

        # 检查是否已访问过该URL
        with self.lock:
            if normalized_url in self.visited_urls:
                return
            self.visited_urls.add(normalized_url)
            if self.resume_enabled and self.state_manager:
                self.state_manager.add_visited_url(normalized_url)

        # 检查是否需要更新
        local_timestamp = get_file_timestamp(file_path)
        remote_timestamp = get_remote_timestamp(url)
        need_download = should_update(remote_timestamp, local_timestamp) or self.force_download

        # 如果需要下载，检查是否达到文件数量限制
        if need_download:
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    logger.info(_t("达到文件数量限制，跳过页面") + f": {url}")
                    return

        # 获取网页内容
        logger.info(_t("抓取页面") + f": {url}")
        page_content = self.fetcher.fetch(url)
        if not page_content:
            logger.error(_t("获取页面内容失败") + f": {url}")
            return

        # 调用插件的 on_page_crawled 钩子
        if self.plugin_manager:
            self.plugin_manager.call_hook("on_page_crawled", url, page_content)

        # 记录页面深度
        with self.lock:
            self.page_depths[url] = depth

        # 如果需要下载，暂存页面内容
        if need_download:
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    logger.info(_t("达到文件数量限制，跳过页面") + f": {url}")
                    return
                self.pages[url] = page_content
                self.downloaded_files += 1
                if self.resume_enabled and self.state_manager:
                    self.state_manager.add_downloaded_file(file_path)
            logger.info(_t("暂存页面") + f": {url}")
        else:
            logger.info(_t("页面已最新，跳过下载") + f": {url}")

        # 检查是否需要保存状态
        if self.resume_enabled and self.state_manager:
            if self.state_manager.should_save(self.save_interval):
                self.state_manager.save_state()

        # 提取链接
        page_links, static_resources = self.link_extractor.extract_links(page_content, url)

        # 过滤并添加静态资源
        for resource_url in static_resources:
            if self.url_filter.should_crawl(resource_url):
                with self.lock:
                    self.static_resources.add(resource_url)

        # 过滤并添加页面链接到队列
        child_urls = []
        for link_url in page_links:
            if (self.url_filter.should_crawl(link_url) and
                depth < self.max_depth):
                normalized_link = normalize_url(link_url)
                with self.lock:
                    if normalized_link not in self.visited_urls:
                        child_urls.append(link_url)

        # 倒序后加入队列（配合 LifoQueue 实现深度优先）
        for child_url in reversed(child_urls):
            with self.lock:
                if self.downloaded_files >= self.max_files:
                    break
            self.queue.put((child_url, depth + 1))

        # 添加延迟
        self._add_delay()

    def _add_delay(self) -> None:
        """添加延迟，避免对目标服务器造成过大压力"""
        if DELAY > 0:
            if RANDOM_DELAY:
                delay_time = random.uniform(DELAY * 0.5, DELAY * 1.5)
                logger.debug(_t("添加随机延迟") + f": {delay_time:.2f} " + _t("秒"))
            else:
                delay_time = DELAY
                logger.debug(_t("添加固定延迟") + f": {delay_time:.2f} " + _t("秒"))
            time.sleep(delay_time)
