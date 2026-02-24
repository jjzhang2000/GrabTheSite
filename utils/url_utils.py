"""URL 工具模块

提供 URL 处理相关的工具函数，包括 URL 规范化、域名提取等。
"""

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
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


def get_domain(url: str) -> str:
    """从 URL 中提取域名

    Args:
        url: 原始 URL

    Returns:
        str: 域名（小写）
    """
    return urlparse(url).netloc.lower()


def get_path(url: str) -> str:
    """从 URL 中提取路径

    Args:
        url: 原始 URL

    Returns:
        str: URL 路径
    """
    return urlparse(url).path


def is_same_domain(url1: str, url2: str) -> bool:
    """检查两个 URL 是否属于同一域名

    Args:
        url1: 第一个 URL
        url2: 第二个 URL

    Returns:
        bool: 是否同一域名
    """
    return get_domain(url1) == get_domain(url2)


def join_url(base: str, url: str) -> str:
    """拼接基础 URL 和相对 URL

    Args:
        base: 基础 URL
        url: 相对 URL

    Returns:
        str: 完整的绝对 URL
    """
    from urllib.parse import urljoin
    return urljoin(base, url)
