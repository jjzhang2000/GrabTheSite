"""插件系统模块

支持通过插件扩展工具功能。
"""

__version__ = "0.1.0"

from plugins.base import Plugin, HookResult
from plugins.hooks import (
    HookType,
    HookEvent,
    HookPriority,
    hook,
    OnCrawlStartHook,
    OnPageCrawledHook,
    OnCrawlEndHook,
    OnSaveStartHook,
    OnPageSavedHook,
    OnSaveEndHook,
)

__all__ = [
    "Plugin",
    "HookResult",
    "HookType",
    "HookEvent",
    "HookPriority",
    "hook",
    "OnCrawlStartHook",
    "OnPageCrawledHook",
    "OnCrawlEndHook",
    "OnSaveStartHook",
    "OnPageSavedHook",
    "OnSaveEndHook",
]
