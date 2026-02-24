"""页面数据模型

定义页面相关的数据模型：
- Page: 页面数据
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time


@dataclass
class Page:
    """页面数据

    表示一个已抓取的页面及其相关信息。
    """
    url: str                           # 页面 URL
    content: str                       # 页面内容（HTML）
    depth: int                         # 抓取深度
    title: Optional[str] = None        # 页面标题
    links: List[str] = field(default_factory=list)           # 页面中的链接
    static_resources: List[str] = field(default_factory=list)  # 页面中的静态资源
    fetched_at: float = field(default_factory=time.time)      # 抓取时间
    content_type: Optional[str] = None  # 内容类型
    status_code: Optional[int] = None   # HTTP 状态码
    encoding: Optional[str] = None      # 页面编码

    def __post_init__(self):
        """初始化后处理"""
        # 如果标题为空，尝试从内容中提取
        if not self.title and self.content:
            self.title = self._extract_title()

    def _extract_title(self) -> Optional[str]:
        """从 HTML 内容中提取标题

        Returns:
            str: 页面标题，如果提取失败返回 None
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text(strip=True)
        except Exception:
            pass
        return None

    def add_link(self, url: str) -> None:
        """添加链接

        Args:
            url: 链接 URL
        """
        if url not in self.links:
            self.links.append(url)

    def add_static_resource(self, url: str) -> None:
        """添加静态资源

        Args:
            url: 资源 URL
        """
        if url not in self.static_resources:
            self.static_resources.append(url)

    def get_domain(self) -> str:
        """获取页面域名

        Returns:
            str: 域名
        """
        from urllib.parse import urlparse
        return urlparse(self.url).netloc

    def get_path(self) -> str:
        """获取页面路径

        Returns:
            str: 路径
        """
        from urllib.parse import urlparse
        return urlparse(self.url).path

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 页面数据的字典表示
        """
        return {
            "url": self.url,
            "title": self.title,
            "depth": self.depth,
            "links_count": len(self.links),
            "static_resources_count": len(self.static_resources),
            "fetched_at": self.fetched_at,
            "content_type": self.content_type,
            "status_code": self.status_code,
            "encoding": self.encoding,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """转换为完整字典（包含所有内容）

        Returns:
            dict: 页面数据的完整字典表示
        """
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "depth": self.depth,
            "links": self.links,
            "static_resources": self.static_resources,
            "fetched_at": self.fetched_at,
            "content_type": self.content_type,
            "status_code": self.status_code,
            "encoding": self.encoding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """从字典创建 Page 对象

        Args:
            data: 页面数据字典

        Returns:
            Page: Page 对象
        """
        return cls(
            url=data.get('url', ''),
            content=data.get('content', ''),
            depth=data.get('depth', 0),
            title=data.get('title'),
            links=data.get('links', []),
            static_resources=data.get('static_resources', []),
            fetched_at=data.get('fetched_at', time.time()),
            content_type=data.get('content_type'),
            status_code=data.get('status_code'),
            encoding=data.get('encoding'),
        )
