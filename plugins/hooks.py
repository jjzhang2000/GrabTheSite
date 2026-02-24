"""插件钩子定义模块

定义插件系统的钩子类型和事件：
- HookType: 钩子类型枚举
- HookEvent: 钩子事件数据类
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


class HookType(Enum):
    """钩子类型枚举

    定义插件系统支持的所有钩子类型。
    """
    # 生命周期钩子
    ON_INIT = "on_init"                    # 插件初始化
    ON_CLEANUP = "on_cleanup"              # 插件清理

    # 抓取钩子
    ON_CRAWL_START = "on_crawl_start"      # 抓取开始
    ON_PAGE_CRAWLED = "on_page_crawled"    # 页面抓取完成
    ON_DOWNLOAD_RESOURCE = "on_download_resource"  # 下载资源
    ON_CRAWL_END = "on_crawl_end"          # 抓取结束

    # 保存钩子
    ON_SAVE_START = "on_save_start"        # 保存开始
    ON_SAVE_SITE = "on_save_site"          # 保存站点
    ON_PROCESS_LINKS = "on_process_links"  # 处理链接
    ON_PAGE_SAVED = "on_page_saved"        # 页面保存完成
    ON_SAVE_END = "on_save_end"            # 保存结束


@dataclass
class HookEvent:
    """钩子事件

    表示一个钩子调用的事件。

    Attributes:
        hook_type: 钩子类型
        data: 事件数据
        timestamp: 事件发生时间
        source: 事件来源
    """
    hook_type: HookType
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 事件数据的字典表示
        """
        return {
            "hook_type": self.hook_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "source": self.source,
        }


# 钩子优先级
class HookPriority(Enum):
    """钩子优先级

    定义钩子方法的执行优先级。
    """
    HIGHEST = 0     # 最高优先级，最先执行
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通优先级（默认）
    LOW = 3         # 低优先级
    LOWEST = 4      # 最低优先级，最后执行


# 钩子装饰器
def hook(hook_type: HookType, priority: HookPriority = HookPriority.NORMAL):
    """钩子装饰器

    用于标记方法为钩子方法。

    Args:
        hook_type: 钩子类型
        priority: 钩子优先级

    Returns:
        装饰器函数
    """
    def decorator(func):
        func._hook_type = hook_type
        func._hook_priority = priority
        return func
    return decorator


# 钩子方法签名定义（用于类型提示）
from typing import Protocol, runtime_checkable


@runtime_checkable
class OnCrawlStartHook(Protocol):
    """抓取开始钩子接口"""

    def on_crawl_start(self, crawler: Any) -> None:
        """抓取开始时调用

        Args:
            crawler: 抓取器实例
        """
        ...


@runtime_checkable
class OnPageCrawledHook(Protocol):
    """页面抓取完成钩子接口"""

    def on_page_crawled(self, url: str, page_content: str) -> None:
        """页面抓取完成时调用

        Args:
            url: 页面 URL
            page_content: 页面内容
        """
        ...


@runtime_checkable
class OnCrawlEndHook(Protocol):
    """抓取结束钩子接口"""

    def on_crawl_end(self, pages: Dict[str, str]) -> None:
        """抓取结束时调用

        Args:
            pages: 抓取的页面字典
        """
        ...


@runtime_checkable
class OnSaveStartHook(Protocol):
    """保存开始钩子接口"""

    def on_save_start(self, saver_data: Dict[str, Any]) -> None:
        """保存开始时调用

        Args:
            saver_data: 保存器数据
        """
        ...


@runtime_checkable
class OnPageSavedHook(Protocol):
    """页面保存完成钩子接口"""

    def on_page_saved(self, url: str, file_path: str) -> None:
        """页面保存完成时调用

        Args:
            url: 页面 URL
            file_path: 保存的文件路径
        """
        ...


@runtime_checkable
class OnSaveEndHook(Protocol):
    """保存结束钩子接口"""

    def on_save_end(self, saved_files: list) -> None:
        """保存结束时调用

        Args:
            saved_files: 保存的文件列表
        """
        ...
