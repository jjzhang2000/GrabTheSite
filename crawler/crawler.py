# 核心抓取模块

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import TARGET_URL, MAX_DEPTH, MAX_FILES, OUTPUT_DIR
from crawler.downloader import download_file


class SiteCrawler:
    """网站爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.target_url = TARGET_URL
        self.max_depth = MAX_DEPTH
        self.max_files = MAX_FILES
        self.output_dir = OUTPUT_DIR
        self.downloaded_files = 0
        self.visited_urls = set()
        self.to_visit_urls = set()  # 待访问的URL集合
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
    def crawl(self):
        """开始抓取"""
        print(f"开始抓取网站: {self.target_url}")
        print(f"保存路径: {self.output_dir}")
        print(f"最大深度: {self.max_depth}")
        print(f"最大文件数: {self.max_files}")
        
        # 开始递归抓取
        self._crawl_page(self.target_url, 0)
        
        print(f"抓取完成，共下载 {self.downloaded_files} 个文件")
    
    def _crawl_page(self, url, depth):
        """递归抓取页面"""
        # 检查是否达到深度限制
        if depth > self.max_depth:
            return
        
        # 检查是否已访问过该URL
        if url in self.visited_urls:
            return
        
        # 检查是否达到文件数量限制
        if self.downloaded_files >= self.max_files:
            return
        
        try:
            # 标记为已访问
            self.visited_urls.add(url)
            
            # 获取网页内容
            print(f"抓取页面: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            # 处理HTML中的链接，替换为本地链接
            html_content = self._process_links(response.text, url)
            
            # 保存HTML文件
            file_path = self._get_file_path(url)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.downloaded_files += 1
            print(f"保存文件: {file_path}")
            
            # 解析HTML，提取链接
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有链接
            links = soup.find_all(['a', 'img', 'link', 'script'])
            
            # 先处理所有图片、脚本和样式表链接
            for link in links:
                if link.name in ['img', 'link', 'script']:
                    src = link.get('src') or link.get('href')
                    if src:
                        full_url = urljoin(url, src)
                        # 只下载同域名的静态资源
                        if self._is_same_domain(full_url):
                            download_file(full_url, self.output_dir)
                            # 静态资源不计入下载总数限制
                            # self.downloaded_files += 1
            
            # 然后处理页面链接
            for link in links:
                if link.name == 'a':
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        # 只抓取同域名的链接，并且深度小于最大深度
                        if self._is_same_domain(full_url) and depth < self.max_depth:
                            # 检查是否达到文件数量限制
                            if self.downloaded_files >= self.max_files:
                                break
                            self._crawl_page(full_url, depth + 1)
                            
        except Exception as e:
            print(f"抓取失败: {url}, 错误: {str(e)}")
    
    def _get_file_path(self, url):
        """获取文件保存路径，保留原网站的目录结构"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 如果路径以/结尾，添加index.html
        if path.endswith('/'):
            path += 'index.html'
        # 如果路径没有文件名（以/结尾但没有文件名），添加index.html
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
    
    def _collect_urls(self, url, depth):
        """收集所有待访问的URL
        
        Args:
            url: 当前URL
            depth: 当前深度
        """
        # 检查是否达到深度限制
        if depth > self.max_depth:
            return
        
        # 检查是否已访问过该URL
        if url in self.visited_urls:
            return
        
        # 检查是否已在待访问列表中
        if url in self.to_visit_urls:
            return
        
        # 检查是否达到文件数量限制
        if len(self.to_visit_urls) >= self.max_files:
            return
        
        try:
            # 标记为已访问
            self.visited_urls.add(url)
            
            # 添加到待访问列表
            self.to_visit_urls.add(url)
            
            # 获取网页内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析HTML，提取链接
            if depth < self.max_depth:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取所有链接，包括a标签和静态资源标签
                links = soup.find_all(['a', 'img', 'link', 'script'])
                
                for link in links:
                    # 检查是否达到文件数量限制
                    if len(self.to_visit_urls) >= self.max_files:
                        break
                    
                    # 处理a标签的href
                    if link.name == 'a':
                        href = link.get('href')
                        if href:
                            full_url = urljoin(url, href)
                            # 只抓取同域名的链接
                            if self._is_same_domain(full_url):
                                self._collect_urls(full_url, depth + 1)
                    
                    # 处理img、link、script标签的src或href
                    elif link.name in ['img', 'link', 'script']:
                        src = link.get('src') or link.get('href')
                        if src:
                            full_url = urljoin(url, src)
                            # 只抓取同域名的静态资源
                            if self._is_same_domain(full_url):
                                # 检查是否已在待访问列表中
                                if full_url not in self.to_visit_urls:
                                    self.to_visit_urls.add(full_url)
                            
        except Exception as e:
            print(f"收集URL失败: {url}, 错误: {str(e)}")
    
    def _process_links(self, html_content, base_url):
        """处理HTML中的链接，替换为本地链接
        
        Args:
            html_content: HTML内容
            base_url: 基础URL
            
        Returns:
            处理后的HTML内容
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取当前页面的路径
            base_parsed = urlparse(base_url)
            base_path = base_parsed.path
            if base_path.endswith('/'):
                base_path = base_path[:-1]
            
            # 处理所有链接元素
            for link in soup.find_all(['a', 'img', 'link', 'script']):
                # 处理a标签的href
                if link.name == 'a':
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        # 只处理同域名的链接
                        if self._is_same_domain(full_url):
                            # 构建本地文件路径
                            full_local_path = self._get_file_path(full_url)
                            # 检查本地文件是否存在且是一个文件（不是目录）
                            if os.path.isfile(full_local_path):
                                # 如果文件存在，转换为相对于当前页面的本地路径并更新链接
                                local_path = self._url_to_local_path(full_url, base_path)
                                link['href'] = local_path
                            else:
                                # 如果文件不存在，保留原始链接
                                pass
                
                # 处理img、link、script标签的src或href
                elif link.name in ['img', 'link', 'script']:
                    src = link.get('src') or link.get('href')
                    if src:
                        full_url = urljoin(base_url, src)
                        # 只处理同域名的静态资源
                        if self._is_same_domain(full_url):
                            # 构建静态资源的本地文件路径
                            # 静态资源的路径处理与页面不同，不需要添加.html扩展名
                            parsed_url = urlparse(full_url)
                            path = parsed_url.path
                            # 如果路径以/结尾，移除
                            if path.endswith('/'):
                                path = path[:-1]
                            # 构建完整文件路径
                            full_local_path = os.path.join(self.output_dir, path.lstrip('/'))
                            # 检查本地文件是否存在且是一个文件（不是目录）
                            if os.path.isfile(full_local_path):
                                # 如果文件存在，转换为相对于当前页面的本地路径并更新链接
                                # 生成相对路径
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
                                # 如果文件不存在，保留原始链接
                                pass
            
            return str(soup)
            
        except Exception as e:
            print(f"处理链接失败: {str(e)}")
            return html_content
    
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
