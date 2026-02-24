"""配置数据模型

定义配置相关的数据模型：
- CrawlConfig: 抓取配置
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from utils.config_manager import ConfigValidator, ValidationError


@dataclass
class CrawlConfig:
    """抓取配置

    表示一次抓取任务的配置参数。
    """
    target_url: str
    max_depth: int = 1
    max_files: int = 10
    delay: float = 1.0
    random_delay: bool = True
    threads: int = 4
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    incremental: bool = True
    force_download: bool = False
    exclude_patterns: List[str] = field(default_factory=list)
    output_dir: Optional[str] = None

    def __post_init__(self):
        """初始化后验证"""
        self.validate()
        # 如果没有指定输出目录，根据目标 URL 生成
        if not self.output_dir:
            self.output_dir = self._generate_output_dir()

    def validate(self) -> None:
        """验证配置

        Raises:
            ValidationError: 验证失败时抛出
        """
        # 验证目标 URL
        ConfigValidator.validate_url(self.target_url, "target_url")

        # 验证数值参数
        self.max_depth = ConfigValidator.validate_positive_int(
            self.max_depth, "max_depth"
        )
        self.max_files = ConfigValidator.validate_positive_int(
            self.max_files, "max_files"
        )
        self.threads = ConfigValidator.validate_range(
            ConfigValidator.validate_positive_int(
                self.threads, "threads", allow_zero=False
            ),
            "threads",
            min_val=1,
            max_val=20
        )
        self.delay = ConfigValidator.validate_range(
            self.delay, "delay", min_val=0, max_val=60
        )

    def _generate_output_dir(self) -> str:
        """生成输出目录路径

        Returns:
            str: 输出目录路径
        """
        import os
        parsed = urlparse(self.target_url)
        domain = parsed.netloc
        base_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        return os.path.join(base_dir, domain)

    @property
    def domain(self) -> str:
        """获取目标域名

        Returns:
            str: 域名
        """
        return urlparse(self.target_url).netloc

    @property
    def start_path(self) -> str:
        """获取起始路径

        Returns:
            str: 起始路径
        """
        path = urlparse(self.target_url).path
        if not path.endswith('/'):
            path += '/'
        return path

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            dict: 配置的字典表示
        """
        return {
            "target_url": self.target_url,
            "max_depth": self.max_depth,
            "max_files": self.max_files,
            "delay": self.delay,
            "random_delay": self.random_delay,
            "threads": self.threads,
            "user_agent": self.user_agent,
            "incremental": self.incremental,
            "force_download": self.force_download,
            "exclude_patterns": self.exclude_patterns,
            "output_dir": self.output_dir,
            "domain": self.domain,
            "start_path": self.start_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlConfig':
        """从字典创建配置

        Args:
            data: 配置字典

        Returns:
            CrawlConfig: 配置对象
        """
        return cls(
            target_url=data.get('target_url', ''),
            max_depth=data.get('max_depth', 1),
            max_files=data.get('max_files', 10),
            delay=data.get('delay', 1.0),
            random_delay=data.get('random_delay', True),
            threads=data.get('threads', 4),
            user_agent=data.get(
                'user_agent',
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
            incremental=data.get('incremental', True),
            force_download=data.get('force_download', False),
            exclude_patterns=data.get('exclude_patterns', []),
            output_dir=data.get('output_dir'),
        )

    @classmethod
    def from_config_manager(cls, config_manager) -> 'CrawlConfig':
        """从配置管理器创建配置

        Args:
            config_manager: 配置管理器实例

        Returns:
            CrawlConfig: 配置对象
        """
        return cls(
            target_url=config_manager.get('target_url', ''),
            max_depth=config_manager.get('crawl.max_depth', 1),
            max_files=config_manager.get('crawl.max_files', 10),
            delay=config_manager.get('crawl.delay', 1.0),
            random_delay=config_manager.get('crawl.random_delay', True),
            threads=config_manager.get('crawl.threads', 4),
            user_agent=config_manager.get(
                'crawl.user_agent',
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
            incremental=config_manager.get('crawl.incremental', True),
            force_download=config_manager.get('force_download', False),
            exclude_patterns=config_manager.get('exclude_urls', []),
            output_dir=config_manager.get('output.full_path'),
        )
