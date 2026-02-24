"""工具模块

提供各种辅助功能：国际化、错误处理、状态管理等。
"""

__version__ = "0.1.0"

from .config_manager import ConfigManager, ConfigValidator, get_config, load_config
from .error_handler import ErrorHandler, retry
from .exceptions import (
    ConfigError,
    ConnectionError,
    CrawlError,
    FileAccessError,
    FileError,
    FileNotFoundError,
    GrabTheSiteError,
    HTTPError,
    InvalidURLError,
    JSError,
    NetworkError,
    PluginError,
    PluginHookError,
    PluginLoadError,
    RateLimitError,
    RenderError,
    RetryExhaustedError,
    StateError,
    StateLoadError,
    StateSaveError,
    TaskAlreadyExistsError,
    TaskError,
    TaskNotFoundError,
    TaskStateError,
    TimeoutError,
    URLFilterError,
    URLNotAllowedError,
    ValidationError,
)
from .browser_manager import BrowserManager, get_browser_manager, close_browser_manager
from .http_client import HTTPClient, HTTPClientManager, create_default_client, create_retry_client
from .i18n import get_available_languages, get_current_lang
from .i18n import gettext as _
from .i18n import init_i18n
from .plugin_manager import Plugin, PluginManager
from .rate_limiter import GlobalDelayManager, RateLimiter
from .sitemap_generator import SitemapGenerator
from .state_manager import StateManager
from .url_utils import get_domain, get_path, is_same_domain, join_url, normalize_url

__all__ = [
    "_",
    "init_i18n",
    "get_current_lang",
    "get_available_languages",
    "Plugin",
    "PluginManager",
    "SitemapGenerator",
    "ErrorHandler",
    "retry",
    "StateManager",
    "GlobalDelayManager",
    "RateLimiter",
    "normalize_url",
    "get_domain",
    "get_path",
    "is_same_domain",
    "join_url",
    "ConfigManager",
    "ConfigValidator",
    "ValidationError",
    "load_config",
    "get_config",
    "HTTPClient",
    "HTTPClientManager",
    "create_default_client",
    "create_retry_client",
    # 浏览器管理器
    "BrowserManager",
    "get_browser_manager",
    "close_browser_manager",
    # 异常类
    "GrabTheSiteError",
    "ConfigError",
    "CrawlError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "ConnectionError",
    "HTTPError",
    "RetryExhaustedError",
    "PluginError",
    "PluginLoadError",
    "PluginHookError",
    "RenderError",
    "JSError",
    "FileError",
    "FileNotFoundError",
    "FileAccessError",
    "StateError",
    "StateLoadError",
    "StateSaveError",
    "URLFilterError",
    "InvalidURLError",
    "URLNotAllowedError",
    "TaskError",
    "TaskNotFoundError",
    "TaskAlreadyExistsError",
    "TaskStateError",
]
