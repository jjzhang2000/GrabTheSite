"""浏览器管理器模块

提供 Playwright 浏览器的统一管理和复用：
- 单例模式管理浏览器实例
- 页面池管理
- 自动资源清理
"""

import os
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from logger import setup_logger, _ as _t

logger = setup_logger(__name__)


class BrowserManager:
    """浏览器管理器

    使用单例模式管理 Playwright 浏览器实例，实现浏览器复用。
    """

    _instance: Optional['BrowserManager'] = None
    _initialized: bool = False

    def __new__(cls) -> 'BrowserManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if BrowserManager._initialized:
            return

        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page_pool: Dict[str, Page] = {}
        self._config: Dict[str, Any] = {}
        self._browser_path: Optional[str] = None

        BrowserManager._initialized = True

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """初始化浏览器管理器

        Args:
            config: 配置字典

        Returns:
            bool: 初始化是否成功
        """
        if self._browser is not None:
            return True

        self._config = config or {}

        try:
            self._playwright = sync_playwright().start()

            # 查找系统浏览器
            self._browser_path = self._find_system_browser()

            if self._browser_path:
                logger.info(_t("使用系统浏览器") + f": {self._browser_path}")
                self._browser = self._playwright.chromium.launch(
                    executable_path=self._browser_path
                )
            else:
                logger.info(_t("使用 Playwright 内置浏览器"))
                self._browser = self._playwright.chromium.launch()

            # 创建共享上下文
            self._context = self._browser.new_context()

            logger.info(_t("浏览器管理器初始化成功"))
            return True

        except Exception as e:
            logger.error(_t("浏览器管理器初始化失败") + f": {e}")
            self.cleanup()
            return False

    def _find_system_browser(self) -> Optional[str]:
        """查找系统安装的浏览器

        Returns:
            str: 浏览器可执行文件路径，如果未找到返回 None
        """
        possible_paths = [
            # Microsoft Edge
            os.path.expandvars(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            # Google Chrome
            os.path.expandvars(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            # Chromium
            os.path.expandvars(r"C:\Program Files\Chromium\Application\chrome.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def get_page(self, page_id: str = "default") -> Optional[Page]:
        """获取页面

        如果页面不存在，创建新页面。

        Args:
            page_id: 页面标识符

        Returns:
            Page: Playwright 页面对象
        """
        if not self.initialize():
            return None

        if page_id not in self._page_pool:
            self._page_pool[page_id] = self._context.new_page()
            logger.debug(_t("创建新页面") + f": {page_id}")

        return self._page_pool[page_id]

    def release_page(self, page_id: str) -> None:
        """释放页面

        Args:
            page_id: 页面标识符
        """
        if page_id in self._page_pool:
            try:
                self._page_pool[page_id].close()
            except Exception as e:
                logger.warning(_t("关闭页面失败") + f": {page_id}, {e}")
            del self._page_pool[page_id]
            logger.debug(_t("释放页面") + f": {page_id}")

    def cleanup(self) -> None:
        """清理资源"""
        # 关闭所有页面
        for page_id, page in list(self._page_pool.items()):
            try:
                page.close()
            except Exception:
                pass
        self._page_pool.clear()

        # 关闭上下文
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        # 关闭浏览器
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        # 停止 Playwright
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        logger.info(_t("浏览器管理器已清理"))

    def __enter__(self) -> 'BrowserManager':
        """上下文管理器入口"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.cleanup()


# 全局浏览器管理器实例
_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """获取全局浏览器管理器实例

    Returns:
        BrowserManager: 浏览器管理器实例
    """
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


def close_browser_manager() -> None:
    """关闭全局浏览器管理器"""
    global _browser_manager
    if _browser_manager is not None:
        _browser_manager.cleanup()
        _browser_manager = None
