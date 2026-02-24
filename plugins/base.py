"""插件基类模块

定义插件系统的基类和接口：
- Plugin: 插件基类
- HookResult: 钩子返回结果
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from logger import setup_logger, _ as _t


@dataclass
class HookResult:
    """钩子返回结果

    用于表示钩子方法的执行结果。

    Attributes:
        success: 是否成功
        data: 返回数据
        error: 错误信息
    """
    success: bool = True
    data: Any = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Any = None) -> 'HookResult':
        """创建成功的结果

        Args:
            data: 返回数据

        Returns:
            HookResult: 成功的结果
        """
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'HookResult':
        """创建失败的结果

        Args:
            error: 错误信息

        Returns:
            HookResult: 失败的结果
        """
        return cls(success=False, error=error)


class Plugin(ABC):
    """插件基类

    所有插件都应该继承自这个类。
    子类可以重写需要的方法，不需要的方法可以忽略。

    Attributes:
        name: 插件名称
        description: 插件描述
        version: 插件版本
        author: 插件作者
    """

    # 插件元数据
    name: str = "Base Plugin"
    description: str = "基础插件类"
    version: str = "1.0.0"
    author: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化插件

        Args:
            config: 配置字典
        """
        self.config: Dict[str, Any] = config or {}
        self.logger = setup_logger(self.name)
        self.enabled: bool = True
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """检查插件是否已初始化"""
        return self._initialized

    def initialize(self) -> HookResult:
        """初始化插件

        在插件被启用前调用。

        Returns:
            HookResult: 初始化结果
        """
        try:
            result = self.on_init()
            self._initialized = True
            return result if isinstance(result, HookResult) else HookResult.ok()
        except Exception as e:
            self.logger.error(_t("插件初始化失败") + f": {self.name}, {e}")
            return HookResult.fail(str(e))

    @abstractmethod
    def on_init(self) -> Optional[HookResult]:
        """插件初始化时调用

        子类应该重写此方法进行初始化。

        Returns:
            HookResult: 初始化结果，None 表示成功
        """
        self.logger.info(_t("插件初始化") + f": {self.name}")
        return None

    def on_crawl_start(self, crawler: Any) -> Optional[HookResult]:
        """抓取开始时调用

        Args:
            crawler: 抓取器实例

        Returns:
            HookResult: 执行结果
        """
        self.logger.info(_t("抓取开始") + f": {self.name}")
        return None

    def on_page_crawled(self, url: str, page_content: str) -> Optional[HookResult]:
        """页面抓取完成时调用

        Args:
            url: 页面 URL
            page_content: 页面内容

        Returns:
            HookResult: 执行结果
        """
        pass

    def on_download_resource(self, url: str, output_dir: str) -> Optional[str]:
        """下载资源文件时调用

        插件可以实现此方法来处理资源文件下载。
        返回下载的文件路径表示下载成功，返回 None 表示下载失败或未处理。

        Args:
            url: 资源文件 URL
            output_dir: 输出目录

        Returns:
            str: 下载的文件路径，如果未处理或下载失败返回 None
        """
        return None

    def on_crawl_end(self, pages: Dict[str, str]) -> Optional[HookResult]:
        """抓取结束时调用

        Args:
            pages: 抓取的页面字典，键为 URL，值为页面内容

        Returns:
            HookResult: 执行结果
        """
        self.logger.info(_t("抓取结束") + f": {self.name}")
        return None

    def on_save_start(self, saver_data: Dict[str, Any]) -> Optional[HookResult]:
        """保存开始时调用

        Args:
            saver_data: 保存器数据，包含 target_url、output_dir 和 static_resources

        Returns:
            HookResult: 执行结果
        """
        pass

    def on_save_site(self, pages: Dict[str, str]) -> Optional[HookResult]:
        """保存站点时调用

        Args:
            pages: 抓取的页面字典

        Returns:
            HookResult: 执行结果
        """
        pass

    def on_process_links(self, url: str, html_content: str) -> Optional[str]:
        """处理链接时调用

        Args:
            url: 页面 URL
            html_content: 页面内容

        Returns:
            str: 处理后的 HTML 内容，如果未处理返回 None
        """
        pass

    def on_page_saved(self, url: str, file_path: str) -> Optional[HookResult]:
        """页面保存完成时调用

        Args:
            url: 页面 URL
            file_path: 保存的文件路径

        Returns:
            HookResult: 执行结果
        """
        pass

    def on_save_end(self, saved_files: List[str]) -> Optional[HookResult]:
        """保存结束时调用

        Args:
            saved_files: 保存的文件列表

        Returns:
            HookResult: 执行结果
        """
        pass

    def cleanup(self) -> HookResult:
        """清理插件资源

        在插件被禁用或程序退出时调用。

        Returns:
            HookResult: 清理结果
        """
        try:
            result = self.on_cleanup()
            self._initialized = False
            return result if isinstance(result, HookResult) else HookResult.ok()
        except Exception as e:
            self.logger.error(_t("插件清理失败") + f": {self.name}, {e}")
            return HookResult.fail(str(e))

    def on_cleanup(self) -> Optional[HookResult]:
        """插件清理时调用

        子类应该重写此方法进行资源清理。

        Returns:
            HookResult: 清理结果，None 表示成功
        """
        self.logger.info(_t("插件清理") + f": {self.name}")
        return None

    def get_info(self) -> Dict[str, str]:
        """获取插件信息

        Returns:
            dict: 插件信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "enabled": str(self.enabled),
            "initialized": str(self._initialized),
        }
