# 插件管理器模块

import os
import importlib
import inspect
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)

# 插件目录
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins')

# 确保 plugins 目录存在
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)


class Plugin:
    """插件基类，所有插件都应该继承自这个类"""
    
    # 插件名称
    name = "Base Plugin"
    
    # 插件描述
    description = "基础插件类"
    
    def __init__(self, config=None):
        """初始化插件
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = setup_logger(self.name)
        self.enabled = True
    
    def on_init(self):
        """插件初始化时调用"""
        self.logger.info(f"插件初始化: {self.name}")
    
    def on_crawl_start(self, crawler):
        """抓取开始时调用
        
        Args:
            crawler: 抓取器实例
        """
        self.logger.info(f"抓取开始: {self.name}")
    
    def on_page_crawled(self, url, page_content):
        """页面抓取完成时调用
        
        Args:
            url: 页面URL
            page_content: 页面内容
        """
        pass
    
    def on_crawl_end(self, pages):
        """抓取结束时调用
        
        Args:
            pages: 抓取的页面字典
        """
        self.logger.info(f"抓取结束: {self.name}")
    
    def on_save_start(self, saver_data):
        """保存开始时调用
        
        Args:
            saver_data: 保存器数据，包含target_url、output_dir和static_resources
        """
        pass
    
    def on_save_site(self, pages):
        """保存站点时调用
        
        Args:
            pages: 抓取的页面字典
        """
        pass
    
    def on_process_links(self, url, html_content):
        """处理链接时调用
        
        Args:
            url: 页面URL
            html_content: 页面内容
        """
        pass
    
    def on_page_saved(self, url, file_path):
        """页面保存完成时调用
        
        Args:
            url: 页面URL
            file_path: 保存的文件路径
        """
        pass
    
    def on_save_end(self, saved_files):
        """保存结束时调用
        
        Args:
            saved_files: 保存的文件列表
        """
        pass
    
    def on_cleanup(self):
        """插件清理时调用"""
        self.logger.info(f"插件清理: {self.name}")


class PluginManager:
    """插件管理器，负责插件的发现、加载、注册和管理"""
    
    def __init__(self, config=None):
        """初始化插件管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.plugins = []
        self.enabled_plugins = []
        self.plugin_paths = []
        
    def discover_plugins(self):
        """发现插件"""
        # 搜索插件目录
        if os.path.exists(PLUGINS_DIR):
            for item in os.listdir(PLUGINS_DIR):
                plugin_path = os.path.join(PLUGINS_DIR, item)
                if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, '__init__.py')):
                    self.plugin_paths.append(plugin_path)
        
        logger.info(f"发现 {len(self.plugin_paths)} 个插件目录")
    
    def load_plugins(self):
        """加载插件"""
        for plugin_path in self.plugin_paths:
            try:
                # 获取插件模块名
                plugin_name = os.path.basename(plugin_path)
                module_path = f'plugins.{plugin_name}'
                
                # 导入插件模块
                module = importlib.import_module(module_path)
                
                # 查找Plugin子类
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, Plugin) and cls != Plugin:
                        # 创建插件实例
                        plugin = cls(self.config)
                        # 保存插件的模块名（目录名）
                        plugin.module_name = plugin_name
                        self.plugins.append(plugin)
                        logger.info(f"加载插件: {plugin.name} (模块名: {plugin_name})")
            except Exception as e:
                logger.error(f"加载插件失败: {plugin_path}, 错误: {e}")
        
        logger.info(f"加载了 {len(self.plugins)} 个插件")
    
    def register_plugin(self, plugin):
        """注册插件
        
        Args:
            plugin: 插件实例
        """
        if isinstance(plugin, Plugin) and plugin not in self.plugins:
            self.plugins.append(plugin)
            logger.info(f"注册插件: {plugin.name}")
    
    def enable_plugins(self, plugin_names=None):
        """启用插件
        
        Args:
            plugin_names: 要启用的插件模块名（目录名）列表，如果为None则启用所有插件
        """
        self.enabled_plugins = []
        
        for plugin in self.plugins:
            if plugin_names is None or getattr(plugin, 'module_name', None) in plugin_names:
                plugin.enabled = True
                self.enabled_plugins.append(plugin)
                plugin.on_init()
                logger.info(f"启用插件: {plugin.name}")
            else:
                plugin.enabled = False
                logger.info(f"禁用插件: {plugin.name}")
        
        logger.info(f"启用了 {len(self.enabled_plugins)} 个插件")
    
    def disable_plugins(self):
        """禁用所有插件"""
        for plugin in self.plugins:
            plugin.enabled = False
        self.enabled_plugins = []
        logger.info("禁用所有插件")
    
    def get_plugin(self, name):
        """获取插件
        
        Args:
            name: 插件名称
            
        Returns:
            Plugin: 插件实例，如果不存在则返回None
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None
    
    def call_hook(self, hook_name, *args, **kwargs):
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
                    logger.error(f"调用插件钩子失败: {plugin.name}.{hook_name}, 错误: {e}")
    
    def cleanup(self):
        """清理插件"""
        for plugin in self.enabled_plugins:
            if plugin.enabled:
                try:
                    plugin.on_cleanup()
                except Exception as e:
                    logger.error(f"插件清理失败: {plugin.name}, 错误: {e}")
        
        self.plugins = []
        self.enabled_plugins = []
        logger.info("插件管理器清理完成")
    
    def get_available_plugins(self):
        """获取可用的插件列表
        
        Returns:
            list: 插件模块名（目录名）列表
        """
        # 确保已经发现插件
        if not self.plugin_paths:
            self.discover_plugins()
        
        # 提取插件模块名
        plugin_names = []
        for plugin_path in self.plugin_paths:
            plugin_name = os.path.basename(plugin_path)
            plugin_names.append(plugin_name)
        
        return plugin_names


# 创建插件管理器实例
plugin_manager = PluginManager()
