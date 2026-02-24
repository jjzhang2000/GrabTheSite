"""页面获取器模块

负责获取页面内容：
- HTTP 请求获取
- JavaScript 渲染
- 错误处理和重试
"""

from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from logger import setup_logger, _ as _t
from config import USER_AGENT, ERROR_HANDLING_CONFIG, JS_RENDERING_CONFIG, DEFAULT_REQUEST_TIMEOUT
from utils.error_handler import ErrorHandler

# 获取 logger 实例
logger = setup_logger(__name__)

# 创建 session，禁用连接池线程
_session = requests.Session()
# 禁用 keep-alive，避免后台线程
_session.headers.update({'Connection': 'close'})
# 限制连接池大小
adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
_session.mount('http://', adapter)
_session.mount('https://', adapter)

# 导入 Playwright JS 渲染器
try:
    from utils.js_renderer_playwright import get_js_renderer, close_js_renderer
    JS_RENDERER_AVAILABLE = True
except ImportError:
    JS_RENDERER_AVAILABLE = False
    logger.warning(_t("JavaScript 渲染器不可用"))


class Fetcher:
    """页面获取器"""

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        js_rendering_enabled: bool = True,
        js_timeout: int = 30,
        error_handler: Optional[ErrorHandler] = None
    ):
        """初始化页面获取器

        Args:
            user_agent: User-Agent 字符串
            js_rendering_enabled: 是否启用 JavaScript 渲染
            js_timeout: JavaScript 渲染超时时间（秒）
            error_handler: 错误处理器实例
        """
        self.user_agent: str = user_agent
        self.js_rendering_enabled: bool = js_rendering_enabled and JS_RENDERER_AVAILABLE
        self.js_timeout: int = js_timeout
        self.error_handler: ErrorHandler = error_handler or ErrorHandler(
            retry_count=ERROR_HANDLING_CONFIG.get('retry_count', 3),
            retry_delay=ERROR_HANDLING_CONFIG.get('retry_delay', 2),
            exponential_backoff=ERROR_HANDLING_CONFIG.get('exponential_backoff', True),
            retryable_errors=ERROR_HANDLING_CONFIG.get('retryable_errors', [429, 500, 502, 503, 504]),
            fail_strategy=ERROR_HANDLING_CONFIG.get('fail_strategy', 'log')
        )

    def fetch(self, url: str) -> Optional[str]:
        """获取页面内容

        首先尝试 JavaScript 渲染（如果启用），然后尝试常规 HTTP 请求。

        Args:
            url: 页面 URL

        Returns:
            str: 页面内容，如果获取失败返回 None
        """
        # 尝试使用 JavaScript 渲染
        if self.js_rendering_enabled:
            content = self._fetch_with_js(url)
            if content:
                return content

        # 使用常规 HTTP 请求
        return self._fetch_with_http(url)

    def _fetch_with_js(self, url: str) -> Optional[str]:
        """使用 JavaScript 渲染获取页面内容

        Args:
            url: 页面 URL

        Returns:
            str: 页面内容，如果获取失败返回 None
        """
        if not JS_RENDERER_AVAILABLE:
            return None

        logger.debug(_t("尝试使用 JavaScript 渲染页面") + f": {url}")

        try:
            js_renderer = get_js_renderer(enable=True, timeout=self.js_timeout)
            if js_renderer:
                page_content = js_renderer.render_page(url, timeout=self.js_timeout + 10)
                if page_content:
                    return page_content
        except Exception as e:
            logger.warning(_t("JavaScript 渲染失败") + f": {e}")

        return None

    def _fetch_with_http(self, url: str) -> Optional[str]:
        """使用 HTTP 请求获取页面内容

        Args:
            url: 页面 URL

        Returns:
            str: 页面内容，如果获取失败返回 None
        """
        headers = {'User-Agent': self.user_agent}

        @self.error_handler.retry
        def _do_request():
            response = _session.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text

        try:
            return _do_request()
        except Exception as e:
            logger.error(_t("HTTP 请求失败") + f": {url}, {e}")
            return None

    def close(self) -> None:
        """关闭获取器，释放资源"""
        if self.js_rendering_enabled and JS_RENDERER_AVAILABLE:
            try:
                close_js_renderer()
                logger.info(_t("JavaScript 渲染器已关闭"))
            except Exception as e:
                logger.warning(_t("关闭 JavaScript 渲染器失败") + f": {e}")
