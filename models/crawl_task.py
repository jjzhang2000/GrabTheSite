"""抓取任务模型

定义抓取任务相关的数据模型：
- TaskStatus: 任务状态枚举
- CrawlTask: 单个抓取任务
- CrawlResult: 抓取结果
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import time


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 待处理
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 已跳过


@dataclass
class CrawlTask:
    """抓取任务

    表示一个待抓取或已抓取的页面任务。
    """
    url: str                           # 页面 URL
    depth: int = 0                     # 抓取深度
    status: TaskStatus = field(default=TaskStatus.PENDING)  # 任务状态
    error: Optional[str] = None        # 错误信息
    created_at: float = field(default_factory=time.time)    # 创建时间
    started_at: Optional[float] = None  # 开始时间
    completed_at: Optional[float] = None  # 完成时间
    retry_count: int = 0               # 重试次数

    def start(self) -> None:
        """标记任务开始"""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()

    def complete(self) -> None:
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        """标记任务失败

        Args:
            error: 错误信息
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = time.time()

    def skip(self) -> None:
        """标记任务跳过"""
        self.status = TaskStatus.SKIPPED
        self.completed_at = time.time()

    @property
    def duration(self) -> Optional[float]:
        """获取任务执行时长（秒）

        Returns:
            float: 执行时长，如果任务未完成返回 None
        """
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 任务数据的字典表示
        """
        return {
            "url": self.url,
            "depth": self.depth,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "duration": self.duration,
        }


@dataclass
class CrawlStats:
    """抓取统计信息"""
    total_urls: int = 0          # 总 URL 数
    downloaded_files: int = 0    # 已下载文件数
    failed_urls: int = 0         # 失败的 URL 数
    skipped_urls: int = 0        # 跳过的 URL 数
    start_time: float = field(default_factory=time.time)  # 开始时间
    end_time: Optional[float] = None  # 结束时间

    @property
    def duration(self) -> Optional[float]:
        """获取总耗时（秒）

        Returns:
            float: 总耗时，如果未结束返回 None
        """
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def success_rate(self) -> float:
        """获取成功率

        Returns:
            float: 成功率（0-1）
        """
        if self.total_urls == 0:
            return 0.0
        return (self.downloaded_files / self.total_urls) * 100

    def finish(self) -> None:
        """标记抓取结束"""
        self.end_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 统计信息的字典表示
        """
        return {
            "total_urls": self.total_urls,
            "downloaded_files": self.downloaded_files,
            "failed_urls": self.failed_urls,
            "skipped_urls": self.skipped_urls,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "success_rate": self.success_rate,
        }


@dataclass
class CrawlResult:
    """抓取结果

    包含一次完整抓取任务的所有结果数据。
    """
    tasks: List[CrawlTask] = field(default_factory=list)  # 所有任务
    pages: Dict[str, 'Page'] = field(default_factory=dict)  # 页面数据（URL -> Page）
    static_resources: Set[str] = field(default_factory=set)  # 静态资源 URL 集合
    stats: CrawlStats = field(default_factory=CrawlStats)   # 统计信息

    def add_task(self, task: CrawlTask) -> None:
        """添加任务

        Args:
            task: 抓取任务
        """
        self.tasks.append(task)
        self.stats.total_urls += 1

    def add_page(self, page: 'Page') -> None:
        """添加页面

        Args:
            page: 页面数据
        """
        self.pages[page.url] = page
        self.stats.downloaded_files += 1

    def add_static_resource(self, url: str) -> None:
        """添加静态资源

        Args:
            url: 资源 URL
        """
        self.static_resources.add(url)

    def get_failed_tasks(self) -> List[CrawlTask]:
        """获取失败的任务列表

        Returns:
            list: 失败的任务列表
        """
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]

    def get_completed_tasks(self) -> List[CrawlTask]:
        """获取已完成的任务列表

        Returns:
            list: 已完成的任务列表
        """
        return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 结果数据的字典表示
        """
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "pages": {url: page.to_dict() for url, page in self.pages.items()},
            "static_resources": list(self.static_resources),
            "stats": self.stats.to_dict(),
        }
