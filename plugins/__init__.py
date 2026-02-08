"""插件系统模块

支持通过插件扩展工具功能。
"""

__version__ = "0.1.0"

from utils.plugin_manager import Plugin, PluginManager

__all__ = [
    "Plugin",
    "PluginManager",
]
