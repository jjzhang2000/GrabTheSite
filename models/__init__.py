"""数据模型模块

提供项目中使用的数据模型：
- CrawlTask: 抓取任务
- Page: 页面数据
- CrawlConfig: 抓取配置
"""

from .crawl_task import CrawlTask, TaskStatus, CrawlResult
from .page import Page
from .config import CrawlConfig

__all__ = [
    "CrawlTask",
    "TaskStatus",
    "CrawlResult",
    "Page",
    "CrawlConfig",
]
