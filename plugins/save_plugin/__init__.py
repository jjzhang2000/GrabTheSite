"""保存插件

核心插件，负责将抓取的页面保存到磁盘：
- 处理页面链接转换
- 保存HTML文件
- 创建目录结构
- 下载静态资源文件
"""

import os
import queue
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.plugin_manager import Plugin
from logger import _ as _t


class SavePlugin(Plugin):
    """保存插件，负责保存抓取的页面到磁盘"""
    
    # 插件名称
    name = "Save Plugin"
    
    # 插件描述
    description = "负责保存抓取的页面到磁盘的插件"
    
    def __init__(self, config=None):
        """初始化插件
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.target_url = None
        self.output_dir = None
        self.static_resources = None
        self.saved_files = []
        self.downloaded_resources = set()  # 已下载的资源集合
        self.downloader_lock = threading.Lock()  # 下载器锁
        
        # 资源下载队列和线程控制
        self.resource_queue = queue.Queue()
        self.resource_thread = None
        self.resource_thread_stop = threading.Event()
        
    def on_init(self):
        """插件初始化时调用"""
        super().on_init()
        self.logger.info(_t("保存插件初始化完成"))
    
    def on_download_resource(self, url, output_dir):
        """下载资源文件
        
        使用 Downloader 类下载单个资源文件
        
        Args:
            url: 资源文件URL
            output_dir: 输出目录
            
        Returns:
            str: 下载的文件路径，如果下载失败返回 None
        """
        # 延迟导入以避免循环导入
        from crawler.downloader import Downloader
        
        # 检查是否已经下载过
        with self.downloader_lock:
            if url in self.downloaded_resources:
                # 已下载过，返回文件路径
                parsed_url = urlparse(url)
                path = parsed_url.path
                file_path = os.path.join(output_dir, path.lstrip('/'))
                if os.path.exists(file_path):
                    return file_path
            
        # 使用 Downloader 下载单个文件
        try:
            downloader = Downloader(output_dir, threads=1)
            downloader.add_task(url)
            results = downloader.run()
            
            if results and results[0][1]:
                file_path = results[0][1]
                with self.downloader_lock:
                    self.downloaded_resources.add(url)
                return file_path
        except Exception as e:
            self.logger.error(_t("下载资源失败") + f": {url}, " + _t("错误") + f": {str(e)}")
        
        return None
    
    def on_crawl_end(self, pages):
        """抓取结束时调用，准备保存参数
        
        Args:
            pages: 抓取的页面字典
        """
        self.logger.info(_t("准备保存") + f" {len(pages)} " + _t("个页面"))
    
    def on_save_start(self, saver_data):
        """保存开始时调用
        
        Args:
            saver_data: 保存器数据，包含target_url、output_dir和static_resources
        """
        self.target_url = saver_data.get('target_url')
        self.output_dir = saver_data.get('output_dir')
        self.static_resources = saver_data.get('static_resources', set())
        
        if self.target_url and self.output_dir:
            # 提取起始目录路径
            parsed_target = urlparse(self.target_url)
            self.target_directory = parsed_target.path
            # 确保路径以/结尾
            if not self.target_directory.endswith('/'):
                self.target_directory += '/'
            
            # 启动资源下载线程
            self._start_resource_thread()
            
            self.logger.info(_t("保存插件准备就绪"))
        else:
            self.logger.error(_t("保存插件初始化失败：缺少必要参数"))
    
    def save_site(self, pages):
        """保存抓取的页面到磁盘
        
        Args:
            pages: 暂存的页面内容，键为URL，值为页面内容
            
        Returns:
            list: 保存的文件列表
        """
        # 统一处理所有页面的链接（同时将静态资源加入下载队列）
        self.logger.info(_t("开始统一处理链接，共") + f" {len(pages)} " + _t("个页面"))
        processed_pages = self._process_all_links(pages)
        
        # 将处理后的页面保存到磁盘
        self.logger.info(_t("开始保存页面到磁盘，共") + f" {len(processed_pages)} " + _t("个页面"))
        saved_count = self._save_pages(processed_pages)
        
        # 等待资源下载队列完成
        self.logger.info(_t("等待静态资源下载完成..."))
        self.resource_queue.join()
        
        self.logger.info(_t("保存完成，共保存") + f" {saved_count} " + _t("个页面"))
        return self.saved_files
    
    def _process_all_links(self, pages):
        """统一处理所有页面的链接
        
        Args:
            pages: 暂存的页面内容，键为URL，值为页面内容
        
        Returns:
            dict: 处理后的页面内容，键为URL，值为处理后的HTML内容
        """
        processed_pages = {}
        
        for url, html_content in pages.items():
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 获取当前页面的路径
                base_parsed = urlparse(url)
                base_path = base_parsed.path
                if base_path.endswith('/'):
                    base_path = base_path[:-1]
                
                # 处理所有链接元素
                for link in soup.find_all(['a', 'img', 'link', 'script']):
                    # 处理a标签的href
                    if link.name == 'a':
                        href = link.get('href')
                        if href:
                            full_url = urljoin(url, href)
                            # 检查是否为已下载的页面
                            if full_url in pages:
                                # 转换为相对于当前页面的本地路径
                                local_path = self._url_to_local_path(full_url, base_path)
                                link['href'] = local_path
                            else:
                                # 检查是否在起始目录及其子目录中
                                if self._is_same_domain(full_url) and self._is_in_target_directory(full_url):
                                    # 未下载的同域且在目标目录中的链接，保留为绝对URL
                                    link['href'] = full_url
                                # 其他链接保持不变
                        
                    # 处理img、link、script标签的src或href
                    elif link.name in ['img', 'link', 'script']:
                        src = link.get('src') or link.get('href')
                        if src:
                            full_url = urljoin(url, src)
                            # 检查是否为已记录的静态资源
                            if full_url in self.static_resources:
                                # 将资源加入下载队列
                                with self.downloader_lock:
                                    if full_url not in self.downloaded_resources:
                                        self.resource_queue.put(full_url)
                                
                                # 构建静态资源的本地路径
                                parsed_url = urlparse(full_url)
                                path = parsed_url.path
                                # 如果路径以/结尾，移除
                                if path.endswith('/'):
                                    path = path[:-1]
                                # 转换为相对于当前页面的本地路径
                                # 从base_path中提取当前目录的层级
                                base_parts = base_path.lstrip('/').split('/')
                                base_parts = [part for part in base_parts if part]
                                # 从path中提取路径部分
                                static_parts = path.lstrip('/').split('/')
                                static_parts = [part for part in static_parts if part]
                                # 找到相同的前缀
                                common_prefix = []
                                for i, (base_part, static_part) in enumerate(zip(base_parts, static_parts)):
                                    if base_part == static_part:
                                        common_prefix.append(base_part)
                                    else:
                                        break
                                # 计算相对路径
                                up_count = len(base_parts) - len(common_prefix)
                                down_parts = static_parts[len(common_prefix):]
                                relative_parts = ['..'] * up_count + down_parts
                                relative_path = '/'.join(relative_parts)
                                if not relative_path:
                                    relative_path = '.'
                                # 更新链接
                                if link.get('src'):
                                    link['src'] = relative_path
                                if link.get('href'):
                                    link['href'] = relative_path
                            else:
                                # 检查是否为同域名
                                if self._is_same_domain(full_url):
                                    # 未下载的同域静态资源，保留为绝对URL
                                    if link.get('src'):
                                        link['src'] = full_url
                                    if link.get('href'):
                                        link['href'] = full_url
                                # 其他链接保持不变
                
                processed_pages[url] = str(soup)
                self.logger.info(_t("处理链接完成") + f": {url}")
                
            except (IOError, OSError, ValueError) as e:
                self.logger.error(_t("处理链接失败") + f": {url}, " + _t("错误") + f": {str(e)}")
                # 如果处理失败，使用原始内容
                processed_pages[url] = html_content
        
        return processed_pages
    
    def _save_pages(self, processed_pages):
        """将处理后的页面保存到磁盘
        
        Args:
            processed_pages: 处理后的页面内容，键为URL，值为处理后的HTML内容
        
        Returns:
            int: 保存的页面数量
        """
        saved_count = 0
        
        for url, html_content in processed_pages.items():
            try:
                # 获取文件路径
                file_path = self._get_file_path(url)
                
                # 创建目录结构
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                saved_count += 1
                self.saved_files.append((url, file_path))
                self.logger.info(_t("保存页面") + f": {file_path}")
                
            except (IOError, OSError) as e:
                self.logger.error(_t("保存页面失败") + f": {url}, " + _t("错误") + f": {str(e)}")
        
        return saved_count
    
    def _get_file_path(self, url):
        """获取文件保存路径，保留原网站的目录结构"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 如果路径为空，设置为/
        if not path:
            path = '/'
        
        # 如果路径以/结尾，添加index.html
        if path.endswith('/'):
            path += 'index.html'
        # 如果路径没有文件名，添加index.html
        elif not os.path.basename(path):
            path += 'index.html'
        # 如果路径没有扩展名，添加.html
        elif '.' not in os.path.basename(path):
            path += '.html'
        
        # 构建完整文件路径，保留目录结构
        file_path = os.path.join(self.output_dir, path.lstrip('/'))
        
        # 创建目录结构
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        return file_path
    
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
    
    def _url_to_local_path(self, url, base_path):
        """将URL转换为本地路径
        
        Args:
            url: 原始URL
            base_path: 当前页面的基础路径
            
        Returns:
            本地路径（相对于当前页面）
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 如果路径以/结尾，添加index.html
        if path.endswith('/'):
            path += 'index.html'
        # 如果路径没有文件名，添加index.html
        elif not os.path.basename(path):
            path += 'index.html'
        
        # 移除开头的/，得到绝对路径
        absolute_path = path.lstrip('/')
        
        # 从base_path中提取当前目录的层级
        # 例如，如果base_path是/rb/photography，那么当前目录是photography
        # 我们需要计算相对于当前目录的路径
        
        # 移除base_path开头的/，并分割成目录列表
        base_parts = base_path.lstrip('/').split('/')
        # 移除空字符串
        base_parts = [part for part in base_parts if part]
        
        # 移除absolute_path开头的与base_path相同的部分
        absolute_parts = absolute_path.split('/')
        
        # 找到相同的前缀
        common_prefix = []
        for i, (base_part, abs_part) in enumerate(zip(base_parts, absolute_parts)):
            if base_part == abs_part:
                common_prefix.append(base_part)
            else:
                break
        
        # 计算相对路径
        # 向上返回的目录数
        up_count = len(base_parts) - len(common_prefix)
        # 向下的路径部分
        down_parts = absolute_parts[len(common_prefix):]
        
        # 构建相对路径
        relative_parts = ['..'] * up_count + down_parts
        relative_path = '/'.join(relative_parts)
        
        # 如果相对路径为空，返回当前目录
        if not relative_path:
            relative_path = '.'
        
        return relative_path
    
    def _start_resource_thread(self):
        """启动资源下载线程"""
        self.resource_thread_stop.clear()
        self.resource_thread = threading.Thread(target=self._resource_worker)
        self.resource_thread.daemon = False
        self.resource_thread.start()
        self.logger.info(_t("资源下载线程已启动"))
    
    def _stop_resource_thread(self):
        """停止资源下载线程"""
        if self.resource_thread:
            self.logger.info(_t("等待资源下载完成..."))
            self.resource_thread_stop.set()
            self.resource_thread.join(timeout=300)
            if self.resource_thread.is_alive():
                self.logger.warning(_t("资源下载线程超时"))
    
    def _resource_worker(self):
        """资源下载线程函数
        
        独立线程处理资源文件下载，避免阻塞页面保存
        """
        self.logger.info(_t("资源下载线程开始工作"))
        
        while not self.resource_thread_stop.is_set():
            try:
                # 从队列获取资源URL，超时1秒
                static_url = self.resource_queue.get(block=True, timeout=1)
                
                # 检查是否已经下载过
                with self.downloader_lock:
                    if static_url in self.downloaded_resources:
                        self.resource_queue.task_done()
                        continue
                
                # 下载资源
                file_path = self.on_download_resource(static_url, self.output_dir)
                
                if file_path:
                    with self.downloader_lock:
                        self.downloaded_resources.add(static_url)
                    self.logger.info(_t("静态资源下载完成") + f": {static_url}")
                else:
                    self.logger.debug(_t("静态资源未下载") + f": {static_url}")
                
                self.resource_queue.task_done()
                
            except queue.Empty:
                # 队列为空，继续循环检查停止信号
                continue
            except Exception as e:
                self.logger.error(_t("资源下载失败") + f": {e}")
                try:
                    self.resource_queue.task_done()
                except:
                    pass
        
        # 处理队列中剩余的任务（非阻塞方式）
        while not self.resource_queue.empty():
            try:
                static_url = self.resource_queue.get(block=False)
                
                # 检查是否已经下载过
                with self.downloader_lock:
                    if static_url in self.downloaded_resources:
                        self.resource_queue.task_done()
                        continue
                
                # 下载资源
                file_path = self.on_download_resource(static_url, self.output_dir)
                
                if file_path:
                    with self.downloader_lock:
                        self.downloaded_resources.add(static_url)
                    self.logger.info(_t("静态资源下载完成") + f": {static_url}")
                
                self.resource_queue.task_done()
                
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(_t("资源下载失败") + f": {e}")
                try:
                    self.resource_queue.task_done()
                except:
                    pass
        
        self.logger.info(_t("资源下载线程已停止"))
    
    def on_save_end(self, saved_files):
        """保存结束时调用
        
        Args:
            saved_files: 保存的文件列表
        """
        # 停止资源下载线程
        self._stop_resource_thread()
        self.logger.info(_t("保存插件工作完成") + f", {_('共保存')} {len(saved_files)} {_('个文件')}")


# 创建插件实例
plugin = SavePlugin()
