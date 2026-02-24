"""链接提取器模块

负责从页面中提取链接：
- 提取页面链接
- 提取静态资源链接
- 链接规范化
"""

from typing import List, Set, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from utils.url_utils import normalize_url


class LinkExtractor:
    """链接提取器"""

    def __init__(self):
        """初始化链接提取器"""
        pass

    def extract_links(self, html: str, base_url: str) -> Tuple[List[str], Set[str]]:
        """从 HTML 中提取链接

        提取页面链接和静态资源链接。

        Args:
            html: HTML 内容
            base_url: 基础 URL，用于解析相对链接

        Returns:
            tuple: (页面链接列表, 静态资源链接集合)
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 提取所有标签
        tags = soup.find_all(['a', 'img', 'link', 'script'])

        page_links: List[str] = []
        static_resources: Set[str] = set()

        for tag in tags:
            if tag.name == 'a':
                # 页面链接
                href = tag.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    normalized_url = normalize_url(full_url)
                    page_links.append(normalized_url)
            else:
                # 静态资源
                src = tag.get('src') or tag.get('href')
                if src:
                    full_url = urljoin(base_url, src)
                    normalized_url = normalize_url(full_url)
                    static_resources.add(normalized_url)

        return page_links, static_resources

    def extract_page_links(self, html: str, base_url: str) -> List[str]:
        """从 HTML 中提取页面链接（仅 a 标签）

        Args:
            html: HTML 内容
            base_url: 基础 URL

        Returns:
            页面链接列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for tag in soup.find_all('a', href=True):
            href = tag.get('href')
            if href:
                full_url = urljoin(base_url, href)
                normalized_url = normalize_url(full_url)
                links.append(normalized_url)

        return links

    def extract_static_resources(self, html: str, base_url: str) -> Set[str]:
        """从 HTML 中提取静态资源链接

        Args:
            html: HTML 内容
            base_url: 基础 URL

        Returns:
            静态资源链接集合
        """
        soup = BeautifulSoup(html, 'html.parser')
        resources: Set[str] = set()

        # 图片
        for tag in soup.find_all('img', src=True):
            full_url = urljoin(base_url, tag.get('src'))
            resources.add(normalize_url(full_url))

        # CSS
        for tag in soup.find_all('link', href=True):
            if tag.get('rel') == ['stylesheet']:
                full_url = urljoin(base_url, tag.get('href'))
                resources.add(normalize_url(full_url))

        # JavaScript
        for tag in soup.find_all('script', src=True):
            full_url = urljoin(base_url, tag.get('src'))
            resources.add(normalize_url(full_url))

        return resources
