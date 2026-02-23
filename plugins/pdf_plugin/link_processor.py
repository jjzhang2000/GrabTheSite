"""链接处理器

处理 HTML 中的链接，标记内部链接和外部链接。
"""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class LinkProcessor:
    """处理 HTML 中的链接"""

    def __init__(self):
        """初始化链接处理器"""
        self.url_to_page_map = {}

    def set_url_to_page_map(self, url_map):
        """设置 URL 到页码的映射

        Args:
            url_map: URL -> 页码 的字典
        """
        self.url_to_page_map = url_map

    def process_links(self, html_content, base_url, all_page_urls):
        """处理 HTML 中的链接

        标记内部链接（在抓取范围内）和外部链接。

        Args:
            html_content: HTML 内容
            base_url: 当前页面 URL
            all_page_urls: 所有页面 URL 集合

        Returns:
            str: 处理后的 HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # 规范化 URL
            normalized_url = self._normalize_url(full_url)

            # 检查是否为内部链接（在抓取范围内）
            if normalized_url in all_page_urls:
                # 标记为内部链接
                link['data-internal-link'] = 'true'
                link['data-target-url'] = normalized_url
            else:
                # 标记为外部链接
                link['data-external-link'] = 'true'

        return str(soup)

    def _normalize_url(self, url):
        """规范化 URL

        统一 URL 格式用于比较：
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
