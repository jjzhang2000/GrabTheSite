"""配置面板模块

提供GUI配置界面：
- URL输入面板
- 高级配置面板（深度、文件数等）
- 插件配置面板
"""

import json
import os
import tkinter as tk
from tkinter import ttk
from utils.i18n import gettext as _
from config import MAX_DEPTH, MAX_FILES, DELAY, BASE_OUTPUT_DIR

# GUI状态文件路径
GUI_STATE_FILE = "config/gui_state.json"


def load_gui_state():
    """加载GUI状态"""
    if os.path.exists(GUI_STATE_FILE):
        try:
            with open(GUI_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_gui_state(state):
    """保存GUI状态"""
    try:
        os.makedirs(os.path.dirname(GUI_STATE_FILE), exist_ok=True)
        with open(GUI_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_last_url():
    """获取上次使用的URL"""
    state = load_gui_state()
    return state.get('last_url', '')


def set_last_url(url):
    """设置上次使用的URL"""
    state = load_gui_state()
    state['last_url'] = url
    save_gui_state(state)


class URLPanel(ttk.Frame):
    """URL配置面板"""
    
    def __init__(self, parent):
        """初始化URL面板"""
        super().__init__(parent)
        
        # 创建URL标签
        self.url_label = ttk.Label(self, text=_("目标URL:"))
        self.url_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建URL输入框，默认值为上次使用的URL
        self.url_var = tk.StringVar(value=get_last_url())
        self.url_entry = ttk.Entry(self, textvariable=self.url_var, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def get_url(self):
        """获取URL"""
        return self.url_var.get()
    
    def save_url(self):
        """保存当前URL到状态文件"""
        url = self.url_var.get().strip()
        if url:
            set_last_url(url)


class AdvancedConfigPanel(ttk.Frame):
    """高级配置面板"""
    
    def __init__(self, parent):
        """初始化高级配置面板"""
        super().__init__(parent)
        
        # 创建网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # 深度配置
        self.depth_label = ttk.Label(self, text=_('抓取深度:'))
        self.depth_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.depth_var = tk.IntVar(value=MAX_DEPTH)
        self.depth_spinbox = ttk.Spinbox(self, from_=0, to=10, textvariable=self.depth_var, width=10)
        self.depth_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 最大文件数配置
        self.max_files_label = ttk.Label(self, text=_('最大文件数:'))
        self.max_files_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.max_files_var = tk.IntVar(value=MAX_FILES)
        self.max_files_spinbox = ttk.Spinbox(self, from_=1, to=10000, textvariable=self.max_files_var, width=10)
        self.max_files_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 输出目录配置
        self.output_label = ttk.Label(self, text=_('输出目录:'))
        self.output_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.output_var = tk.StringVar(value=BASE_OUTPUT_DIR)
        self.output_entry = ttk.Entry(self, textvariable=self.output_var, width=40)
        self.output_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 延迟配置
        self.delay_label = ttk.Label(self, text=_('请求延迟(秒):'))
        self.delay_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.delay_var = tk.DoubleVar(value=DELAY)
        self.delay_spinbox = ttk.Spinbox(self, from_=0.0, to=10.0, increment=0.1, textvariable=self.delay_var, width=10)
        self.delay_spinbox.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 无随机延迟配置
        self.no_random_delay_var = tk.BooleanVar(value=False)
        self.no_random_delay_checkbutton = ttk.Checkbutton(self, text=_('无随机延迟'), variable=self.no_random_delay_var)
        self.no_random_delay_checkbutton.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 线程数配置
        self.threads_label = ttk.Label(self, text=_('线程数:'))
        self.threads_label.grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.threads_var = tk.IntVar(value=4)
        self.threads_spinbox = ttk.Spinbox(self, from_=1, to=32, textvariable=self.threads_var, width=10)
        self.threads_spinbox.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 生成站点地图配置
        self.sitemap_var = tk.BooleanVar(value=False)
        self.sitemap_checkbutton = ttk.Checkbutton(self, text=_('生成XML站点地图'), variable=self.sitemap_var)
        self.sitemap_checkbutton.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 生成HTML站点地图配置
        self.html_sitemap_var = tk.BooleanVar(value=False)
        self.html_sitemap_checkbutton = ttk.Checkbutton(self, text=_('生成HTML站点地图'), variable=self.html_sitemap_var)
        self.html_sitemap_checkbutton.grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # JS渲染配置
        self.js_rendering_var = tk.BooleanVar(value=False)
        self.js_rendering_checkbutton = ttk.Checkbutton(self, text=_('启用JS渲染'), variable=self.js_rendering_var)
        self.js_rendering_checkbutton.grid(row=10, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # JS超时配置
        self.js_timeout_label = ttk.Label(self, text=_('JS渲染超时(秒):'))
        self.js_timeout_label.grid(row=11, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.js_timeout_var = tk.IntVar(value=30)
        self.js_timeout_spinbox = ttk.Spinbox(self, from_=1, to=300, textvariable=self.js_timeout_var, width=10)
        self.js_timeout_spinbox.grid(row=11, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 语言配置
        self.lang_label = ttk.Label(self, text=_('语言:'))
        self.lang_label.grid(row=12, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.lang_var = tk.StringVar(value='zh_CN')
        self.lang_combobox = ttk.Combobox(self, textvariable=self.lang_var, values=['zh_CN', 'en'], width=10)
        self.lang_combobox.grid(row=12, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 用户代理配置
        self.user_agent_label = ttk.Label(self, text=_('用户代理:'))
        self.user_agent_label.grid(row=13, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.user_agent_var = tk.StringVar(value='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        self.user_agent_entry = ttk.Entry(self, textvariable=self.user_agent_var, width=40)
        self.user_agent_entry.grid(row=13, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 强制下载配置
        self.force_download_var = tk.BooleanVar(value=False)
        self.force_download_checkbutton = ttk.Checkbutton(self, text=_('强制下载所有文件'), variable=self.force_download_var)
        self.force_download_checkbutton.grid(row=14, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def get_config(self):
        """获取所有配置参数"""
        return {
            "depth": self.depth_var.get(),
            "max_files": self.max_files_var.get(),
            "output": self.output_var.get(),
            "delay": self.delay_var.get(),
            "no_random_delay": self.no_random_delay_var.get(),
            "threads": self.threads_var.get(),
            "sitemap": self.sitemap_var.get(),
            "html_sitemap": self.html_sitemap_var.get(),
            "js_rendering": self.js_rendering_var.get(),
            "js_timeout": self.js_timeout_var.get(),
            "lang": self.lang_var.get(),
            "user_agent": self.user_agent_var.get(),
            "force_download": self.force_download_var.get()
        }
    
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