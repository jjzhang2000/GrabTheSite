"""URL 过滤器模块

负责 URL 过滤逻辑：
- 同域名检查
- 目标目录检查
- 排除列表检查
"""

import fnmatch
from urllib.parse import urlparse
from typing import List


class URLFilter:
    """URL 过滤器"""

    def __init__(self, target_url: str, exclude_patterns: List[str] = None):
        """初始化 URL 过滤器

        Args:
            target_url: 目标 URL，用于确定域名和起始目录
            exclude_patterns: 排除模式列表（支持通配符）
        """
        self.target_url: str = target_url
        self.exclude_patterns: List[str] = exclude_patterns or []

        # 提取目标域名
        parsed_target = urlparse(target_url)
        self.target_domain: str = parsed_target.netloc

        # 提取并标准化起始目录路径（确保以/结尾）
        self.target_directory: str = parsed_target.path
        if not self.target_directory.endswith('/'):
            self.target_directory += '/'

        # 处理排除列表
        self.processed_exclude_patterns: List[str] = self._process_exclude_patterns()

    def _process_exclude_patterns(self) -> List[str]:
        """处理排除模式列表

        保留原始模式（支持通配符），同时支持普通URL的标准化处理。

        Returns:
            处理后的排除模式列表
        """
        processed = []
        for pattern in self.exclude_patterns:
            # 检查是否包含通配符
            if '*' in pattern or '?' in pattern:
                # 保留通配符模式，不进行标准化
                processed.append(pattern)
            else:
                # 普通URL，进行标准化处理
                parsed_url = urlparse(pattern)
                path = parsed_url.path
                if not path.endswith('/'):
                    path += '/'
                full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
                processed.append(full_url)
        return processed

    def is_same_domain(self, url: str) -> bool:
        """检查是否为同域名

        Args:
            url: 要检查的 URL

        Returns:
            bool: 是否与目标 URL 同域名
        """
        current_domain = urlparse(url).netloc
        return self.target_domain == current_domain

    def is_in_target_directory(self, url: str) -> bool:
        """检查 URL 是否在起始目录及其子目录中

        Args:
            url: 要检查的 URL

        Returns:
            bool: URL 是否在起始目录及其子目录中
        """
        url_path = urlparse(url).path

        # 确保 url_path 以/结尾，以便正确比较
        if not url_path.endswith('/'):
            url_path += '/'

        # 检查 url_path 是否以 target_directory 开头
        return url_path.startswith(self.target_directory)

    def is_excluded(self, url: str) -> bool:
        """检查 URL 是否在排除列表中

        支持通配符(*)匹配，例如:
        - *.php* 匹配所有包含.php的URL
        - */admin/* 匹配所有包含/admin/的URL

        Args:
            url: 要检查的 URL

        Returns:
            bool: URL 是否在排除列表中
        """
        for pattern in self.processed_exclude_patterns:
            # 检查是否包含通配符
            if '*' in pattern or '?' in pattern:
                # 使用 fnmatch 进行通配符匹配
                if fnmatch.fnmatch(url, pattern):
                    return True
                # 也尝试匹配 URL 的路径部分
                url_path = urlparse(url).path
                if fnmatch.fnmatch(url_path, pattern):
                    return True
                # 尝试匹配 URL 的各种变体
                if fnmatch.fnmatch(url, f"*{pattern}*"):
                    return True
            else:
                # 普通字符串匹配
                if url.startswith(pattern):
                    return True
        return False

    def should_crawl(self, url: str) -> bool:
        """检查 URL 是否应该被抓取

        综合检查：同域名、在目标目录中、不在排除列表中

        Args:
            url: 要检查的 URL

        Returns:
            bool: 是否应该被抓取
        """
        if not self.is_same_domain(url):
            return False
        if not self.is_in_target_directory(url):
            return False
        if self.is_excluded(url):
            return False
        return True
