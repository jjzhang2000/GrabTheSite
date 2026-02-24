"""插件管理器模块

插件系统的核心，负责：
- 插件的发现和加载
- 钩子方法的管理和调用
- 插件生命周期管理

注意：Plugin 基类已移至 plugins/base.py
"""

import os
import importlib
import inspect
from typing import Any, Dict, List, Optional, Callable
from logger import setup_logger, _ as _t
from plugins.base import Plugin, HookResult
from plugins.hooks import HookType, HookEvent

# 获取 logger 实例
logger = setup_logger(__name__)

# 插件目录
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')

# 确保 plugins 目录存在
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)


class PluginManager:
    """插件管理器，负责插件的发现、加载、注册和管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化插件管理器

        Args:
            config: 配置对象
        """
        self.config: Optional[Dict[str, Any]] = config
        self.plugins: List[Plugin] = []
        self.enabled_plugins: List[Plugin] = []
        self.plugin_paths: List[str] = []
        self._hook_handlers: Dict[HookType, List[Callable]] = {}

    def discover_plugins(self) -> None:
        """发现插件"""
        # 搜索插件目录
        if os.path.exists(PLUGINS_DIR):
            for item in os.listdir(PLUGINS_DIR):
                plugin_path = os.path.join(PLUGINS_DIR, item)
                if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, '__init__.py')):
                    self.plugin_paths.append(plugin_path)

        logger.info(_t("发现") + f" {len(self.plugin_paths)} " + _t("个插件目录"))

    def load_plugins(self) -> None:
        """加载插件"""
        for plugin_path in self.plugin_paths:
            try:
                # 获取插件模块名
                plugin_name = os.path.basename(plugin_path)
                module_path = f'plugins.{plugin_name}'

                # 导入插件模块
                module = importlib.import_module(module_path)

                # 查找 Plugin 子类
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, Plugin) and cls != Plugin:
                        # 创建插件实例
                        plugin = cls(self.config)
                        # 保存插件的模块名（目录名）
                        plugin.module_name = plugin_name
                        self.plugins.append(plugin)
                        logger.info(_t("加载插件") + f": {plugin.name} (" + _t("模块名") + f": {plugin_name})")
            except Exception as e:
                logger.error(_t("加载插件失败") + f": {plugin_path}, " + _t("错误") + f": {e}")

        logger.info(_t("加载了") + f" {len(self.plugins)} " + _t("个插件"))

    def register_plugin(self, plugin: Plugin) -> None:
        """注册插件

        Args:
            plugin: 插件实例
        """
        if isinstance(plugin, Plugin) and plugin not in self.plugins:
            self.plugins.append(plugin)
            logger.info(_t("注册插件") + f": {plugin.name}")

    def enable_plugins(self, plugin_config: Optional[Dict[str, bool]] = None) -> None:
        """启用插件

        Args:
            plugin_config: 插件配置字典，格式为 {plugin_name: True/False}
                          如果为 None，则启用所有发现的插件（向后兼容）
                          如果为非 None（包括空字典），则只启用明确指定为 True 的插件
        """
        self.enabled_plugins = []

        for plugin in self.plugins:
            module_name = getattr(plugin, 'module_name', None)

            # 确定插件是否启用
            if plugin_config is None:
                # 配置为 None，默认启用所有插件（向后兼容）
                enabled = True
            elif module_name in plugin_config:
                # 插件在配置中明确指定，按配置值启用
                enabled = plugin_config[module_name]
            else:
                # 插件不在配置中，默认禁用（安全配置）
                enabled = False

            if enabled:
                plugin.enabled = True
                result = plugin.initialize()
                if result.success:
                    self.enabled_plugins.append(plugin)
                    logger.info(_t("启用插件") + f": {plugin.name}")
                else:
                    plugin.enabled = False
                    logger.error(_t("启用插件失败") + f": {plugin.name}, " + _t("错误") + f": {result.error}")
            else:
                plugin.enabled = False
                logger.debug(_t("禁用插件") + f": {plugin.name}")

        logger.info(_t("启用了") + f" {len(self.enabled_plugins)} " + _t("个插件"))

    def enable_all_plugins(self) -> None:
        """启用所有已加载的插件"""
        self.enabled_plugins = []

        for plugin in self.plugins:
            plugin.enabled = True
            result = plugin.initialize()
            if result.success:
                self.enabled_plugins.append(plugin)
                logger.info(_t("启用插件") + f": {plugin.name}")
            else:
                plugin.enabled = False
                logger.error(_t("启用插件失败") + f": {plugin.name}, " + _t("错误") + f": {result.error}")

        logger.info(_t("启用了") + f" {len(self.enabled_plugins)} " + _t("个插件"))

    def disable_plugins(self) -> None:
        """禁用所有插件"""
        for plugin in self.plugins:
            if plugin.enabled:
                plugin.cleanup()
            plugin.enabled = False
        self.enabled_plugins = []
        logger.info(_t("禁用所有插件"))

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            Plugin: 插件实例，如果不存在则返回 None
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None

    def call_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> None:
        """调用插件钩子

        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数
        """
        for plugin in self.enabled_plugins:
            if plugin.enabled:
                try:
                    method = getattr(plugin, hook_name, None)
                    if method and callable(method):
                        method(*args, **kwargs)
                except Exception as e:
                    logger.error(_t("调用插件钩子失败") + f": {plugin.name}.{hook_name}, " + _t("错误") + f": {e}")

    def call_hook_with_result(self, hook_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """调用插件钩子并返回结果

        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            dict: 插件名称到返回结果的映射
        """
        results: Dict[str, Any] = {}
        for plugin in self.enabled_plugins:
            if plugin.enabled:
                try:
                    method = getattr(plugin, hook_name, None)
                    if method and callable(method):
                        result = method(*args, **kwargs)
                        results[plugin.name] = result
                except Exception as e:
                    logger.error(_t("调用插件钩子失败") + f": {plugin.name}.{hook_name}, " + _t("错误") + f": {e}")
        return results

    def cleanup(self) -> None:
        """清理插件"""
        for plugin in self.enabled_plugins:
            if plugin.enabled:
                try:
                    plugin.cleanup()
                except Exception as e:
                    logger.error(_t("插件清理失败") + f": {plugin.name}, " + _t("错误") + f": {e}")

        self.plugins = []
        self.enabled_plugins = []
        logger.info(_t("插件管理器清理完成"))

    def get_available_plugins(self) -> List[str]:
        """获取可用的插件列表

        Returns:
            list: 插件模块名（目录名）列表
        """
        # 确保已经发现插件
        if not self.plugin_paths:
            self.discover_plugins()

        # 提取插件模块名
        plugin_names: List[str] = []
        for plugin_path in self.plugin_paths:
            plugin_name = os.path.basename(plugin_path)
            plugin_names.append(plugin_name)

        return plugin_names

    def get_plugin_info(self) -> List[Dict[str, str]]:
        """获取所有插件的信息

        Returns:
            list: 插件信息字典列表
        """
        return [plugin.get_info() for plugin in self.plugins]


# 创建插件管理器实例
plugin_manager = PluginManager()

# 向后兼容：导出 Plugin 类
Plugin = Plugin
