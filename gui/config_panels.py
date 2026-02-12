"""配置面板模块

提供GUI配置界面：
- URL输入面板
- 高级配置面板（深度、文件数等）
- 插件配置面板
"""

import os
import tkinter as tk
from tkinter import ttk
import yaml
from utils.i18n import gettext as _
from config import MAX_DEPTH, MAX_FILES, DELAY, BASE_OUTPUT_DIR, USER_CONFIG_FILE, load_config


def save_config_to_yaml(config):
    """保存配置到config.yaml
    
    Args:
        config: 配置字典，包含 url, depth, max_files 等
    """
    try:
        # 加载现有配置
        existing_config = {}
        if os.path.exists(USER_CONFIG_FILE):
            try:
                with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}
            except Exception:
                existing_config = {}
        
        # 构建新的配置结构
        new_config = existing_config.copy()
        
        # 更新 target_url
        if 'url' in config and config['url']:
            new_config['target_url'] = config['url']
        
        # 更新 crawl 配置
        if 'crawl' not in new_config:
            new_config['crawl'] = {}
        if 'depth' in config:
            new_config['crawl']['max_depth'] = config['depth']
        if 'max_files' in config:
            new_config['crawl']['max_files'] = config['max_files']
        if 'delay' in config:
            new_config['crawl']['delay'] = config['delay']
        if 'no_random_delay' in config:
            new_config['crawl']['random_delay'] = not config['no_random_delay']
        if 'threads' in config:
            new_config['crawl']['threads'] = config['threads']
        if 'user_agent' in config:
            new_config['crawl']['user_agent'] = config['user_agent']
        
        # 更新 output 配置
        if 'output' not in new_config:
            new_config['output'] = {}
        if 'output' in config:
            new_config['output']['base_dir'] = config['output']
        if 'sitemap' in config:
            if 'sitemap' not in new_config['output']:
                new_config['output']['sitemap'] = {}
            new_config['output']['sitemap']['enable'] = config['sitemap']
        if 'html_sitemap' in config:
            if 'sitemap' not in new_config['output']:
                new_config['output']['sitemap'] = {}
            new_config['output']['sitemap']['enable_html'] = config['html_sitemap']
        
        # 更新 js_rendering 配置
        if 'js_rendering' not in new_config:
            new_config['js_rendering'] = {}
        if 'js_rendering' in config:
            new_config['js_rendering']['enable'] = config['js_rendering']
        if 'js_timeout' in config:
            new_config['js_rendering']['timeout'] = config['js_timeout']
        
        # 更新 i18n 配置
        if 'i18n' not in new_config:
            new_config['i18n'] = {}
        if 'lang' in config:
            new_config['i18n']['lang'] = config['lang']
        
        # 保存到文件
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


class URLPanel(ttk.Frame):
    """URL配置面板"""
    
    def __init__(self, parent, config=None):
        """初始化URL面板
        
        Args:
            parent: 父窗口
            config: 配置字典，如果为None则从配置文件加载
        """
        super().__init__(parent)
        
        # 获取配置
        if config is None:
            config = load_config()
        
        # 创建URL标签
        self.url_label = ttk.Label(self, text=_("目标URL:"))
        self.url_label.pack(side=tk.LEFT, padx=(5, 5))
        
        # 创建URL输入框，默认值为配置文件中的target_url
        initial_url = config.get('target_url', '')
        self.url_var = tk.StringVar(value=initial_url)
        self.url_entry = ttk.Entry(self, textvariable=self.url_var, width=55)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    def get_url(self):
        """获取URL"""
        return self.url_var.get()


class AdvancedConfigPanel(ttk.Frame):
    """高级配置面板"""
    
    def __init__(self, parent, config=None):
        """初始化高级配置面板
        
        Args:
            parent: 父窗口
            config: 配置字典，如果为None则从配置文件加载
        """
        super().__init__(parent)
        
        # 获取配置
        if config is None:
            config = load_config()
        
        crawl_config = config.get('crawl', {})
        output_config = config.get('output', {})
        sitemap_config = output_config.get('sitemap', {})
        i18n_config = config.get('i18n', {})
        
        # 创建网格布局 - 第0列是标签，第1列是输入框，第2列是额外选项
        self.grid_columnconfigure(0, weight=0, minsize=100)  # 标签列固定宽度
        self.grid_columnconfigure(1, weight=0)  # 输入框列
        self.grid_columnconfigure(2, weight=1)  # 剩余空间
        
        # 深度配置
        self.depth_label = ttk.Label(self, text=_('抓取深度:'))
        self.depth_label.grid(row=0, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.depth_var = tk.IntVar(value=crawl_config.get('max_depth', MAX_DEPTH))
        self.depth_spinbox = ttk.Spinbox(self, from_=0, to=10, textvariable=self.depth_var, width=8)
        self.depth_spinbox.grid(row=0, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 最大文件数配置
        self.max_files_label = ttk.Label(self, text=_('最大文件数:'))
        self.max_files_label.grid(row=1, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.max_files_var = tk.IntVar(value=crawl_config.get('max_files', MAX_FILES))
        self.max_files_spinbox = ttk.Spinbox(self, from_=1, to=10000, textvariable=self.max_files_var, width=8)
        self.max_files_spinbox.grid(row=1, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 输出目录配置（输入框 + 浏览按钮）
        self.output_label = ttk.Label(self, text=_('输出目录:'))
        self.output_label.grid(row=2, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.output_var = tk.StringVar(value=output_config.get('base_dir', BASE_OUTPUT_DIR))
        self.output_entry = ttk.Entry(self, textvariable=self.output_var, width=25)
        self.output_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 浏览按钮
        self.browse_button = ttk.Button(self, text=_('浏览...'), command=self._browse_output_dir, width=8)
        self.browse_button.grid(row=2, column=2, sticky=tk.W, padx=3, pady=5)
        
        # 延迟配置 + 无随机延迟（同一行显示）
        self.delay_label = ttk.Label(self, text=_('请求延迟(秒):'))
        self.delay_label.grid(row=3, column=0, sticky=tk.W, padx=3, pady=5)
        
        # 延迟输入框（宽度缩小，放在左侧）
        self.delay_var = tk.DoubleVar(value=crawl_config.get('delay', DELAY))
        self.delay_spinbox = ttk.Spinbox(self, from_=0.0, to=10.0, increment=0.1, textvariable=self.delay_var, width=6)
        self.delay_spinbox.grid(row=3, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 无随机延迟复选框（放在同一行右侧）
        random_delay = crawl_config.get('random_delay', True)
        self.no_random_delay_var = tk.BooleanVar(value=not random_delay)
        self.no_random_delay_checkbutton = ttk.Checkbutton(self, text=_('无随机延迟'), variable=self.no_random_delay_var)
        self.no_random_delay_checkbutton.grid(row=3, column=2, sticky=tk.W, padx=3, pady=5)
        
        # 线程数配置
        self.threads_label = ttk.Label(self, text=_('线程数:'))
        self.threads_label.grid(row=4, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.threads_var = tk.IntVar(value=crawl_config.get('threads', 4))
        self.threads_spinbox = ttk.Spinbox(self, from_=1, to=32, textvariable=self.threads_var, width=6)
        self.threads_spinbox.grid(row=4, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 生成站点地图配置（XML和HTML并列显示）
        self.sitemap_var = tk.BooleanVar(value=sitemap_config.get('enable', False))
        self.sitemap_checkbutton = ttk.Checkbutton(self, text=_('生成XML站点地图'), variable=self.sitemap_var)
        self.sitemap_checkbutton.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=3, pady=5)
        
        # 生成HTML站点地图配置（与XML并列）
        self.html_sitemap_var = tk.BooleanVar(value=sitemap_config.get('enable_html', False))
        self.html_sitemap_checkbutton = ttk.Checkbutton(self, text=_('生成HTML站点地图'), variable=self.html_sitemap_var)
        self.html_sitemap_checkbutton.grid(row=5, column=2, sticky=tk.W, padx=3, pady=5)
        
        # 语言配置
        self.lang_label = ttk.Label(self, text=_('语言:'))
        self.lang_label.grid(row=6, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.lang_var = tk.StringVar(value=i18n_config.get('lang', 'zh_CN'))
        self.lang_combobox = ttk.Combobox(self, textvariable=self.lang_var, values=['zh_CN', 'en'], width=8)
        self.lang_combobox.grid(row=6, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 用户代理配置
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.user_agent_label = ttk.Label(self, text=_('用户代理:'))
        self.user_agent_label.grid(row=7, column=0, sticky=tk.W, padx=3, pady=5)
        
        self.user_agent_var = tk.StringVar(value=crawl_config.get('user_agent', default_ua))
        self.user_agent_entry = ttk.Entry(self, textvariable=self.user_agent_var, width=35)
        self.user_agent_entry.grid(row=7, column=1, columnspan=2, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 强制下载配置（不从配置文件读取，默认为False）
        self.force_download_var = tk.BooleanVar(value=False)
        self.force_download_checkbutton = ttk.Checkbutton(self, text=_('强制下载所有文件'), variable=self.force_download_var)
        self.force_download_checkbutton.grid(row=8, column=0, columnspan=3, sticky=tk.W, padx=3, pady=5)
        
        # 插件配置（放在高级配置面板中）
        self._init_plugin_config()
    
    def _init_plugin_config(self):
        """初始化插件配置区域"""
        # 插件配置标签框架
        self.plugin_frame = ttk.LabelFrame(self, text=_('插件配置'), padding="5")
        self.plugin_frame.grid(row=9, column=0, columnspan=3, sticky=tk.W+tk.E, padx=3, pady=(15, 5))
        
        # 存储插件复选框变量
        self.plugin_vars = {}
        
        # 获取插件列表
        try:
            from utils.plugin_manager import PluginManager
            plugin_manager = PluginManager()
            plugins = plugin_manager.get_available_plugins()
        except Exception:
            # 如果获取插件列表失败，使用默认插件
            plugins = ['save_plugin', 'example_plugin']
        
        # 为每个插件创建复选框（默认启用 save_plugin）
        for i, plugin in enumerate(plugins):
            var = tk.BooleanVar(value=(plugin == 'save_plugin'))
            self.plugin_vars[plugin] = var
            cb = ttk.Checkbutton(
                self.plugin_frame, 
                text=plugin, 
                variable=var
            )
            cb.pack(side=tk.LEFT, padx=5, pady=2)
    
    def _browse_output_dir(self):
        """浏览选择输出目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.output_var.get() or '.')
        if directory:
            self.output_var.set(directory)
    
    def get_config(self):
        """获取所有配置参数（JS渲染相关配置从config.yaml读取，不在GUI中设置）"""
        return {
            "depth": self.depth_var.get(),
            "max_files": self.max_files_var.get(),
            "output": self.output_var.get(),
            "delay": self.delay_var.get(),
            "no_random_delay": self.no_random_delay_var.get(),
            "threads": self.threads_var.get(),
            "sitemap": self.sitemap_var.get(),
            "html_sitemap": self.html_sitemap_var.get(),
            "lang": self.lang_var.get(),
            "user_agent": self.user_agent_var.get(),
            "force_download": self.force_download_var.get(),
            "plugins": self.get_plugin_config()
        }
    
    def get_plugin_config(self):
        """获取插件配置"""
        return {name: var.get() for name, var in self.plugin_vars.items()}
    
    # 保留一些常用的getter方法，以便向后兼容
    def get_depth(self):
        """获取抓取深度"""
        return self.depth_var.get()
    
    def get_max_files(self):
        """获取最大文件数"""
        return self.max_files_var.get()
    
    def get_output(self):
        """获取输出目录"""
        return self.output_var.get()


class PluginConfigPanel(ttk.Frame):
    """插件配置面板"""
    
    def __init__(self, parent):
        """初始化插件配置面板"""
        super().__init__(parent)
        
        # 插件列表框架
        self.plugin_list_frame = ttk.LabelFrame(self, text=_('插件配置'), padding="10")
        self.plugin_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 存储插件复选框变量
        self.plugin_vars = {}
        
        # 填充插件列表
        self._populate_plugin_list()
    
    def _populate_plugin_list(self):
        """填充插件列表"""
        # 从插件管理器获取实际的插件列表
        try:
            from utils.plugin_manager import PluginManager
            plugin_manager = PluginManager()
            plugins = plugin_manager.get_available_plugins()
        except Exception:
            # 如果获取插件列表失败，使用默认插件
            plugins = ['save_plugin', 'example_plugin']
        
        # 为每个插件创建复选框（默认启用 save_plugin）
        for plugin in plugins:
            var = tk.BooleanVar(value=(plugin == 'save_plugin'))
            self.plugin_vars[plugin] = var
            cb = ttk.Checkbutton(
                self.plugin_list_frame, 
                text=plugin, 
                variable=var
            )
            cb.pack(anchor=tk.W, padx=5, pady=2)
    
    def get_plugin_config(self):
        """获取插件配置
        
        Returns:
            dict: 插件配置字典，格式为 {plugin_name: True/False}
        """
        return {name: var.get() for name, var in self.plugin_vars.items()}