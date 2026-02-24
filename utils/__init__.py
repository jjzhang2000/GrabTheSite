"""工具模块

提供各种辅助功能：国际化、错误处理、状态管理等。
"""

__version__ = "0.1.0"

from .i18n import gettext as _, init_i18n, get_current_lang, get_available_languages
from .plugin_manager import Plugin, PluginManager
from .sitemap_generator import SitemapGenerator
from .error_handler import ErrorHandler, retry
from .state_manager import StateManager
from .rate_limiter import GlobalDelayManager, RateLimiter
from .url_utils import normalize_url, get_domain, get_path, is_same_domain, join_url

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
]
