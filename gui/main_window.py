# 主窗口模块

import tkinter as tk
from tkinter import ttk
from gui.config_panels import URLPanel, AdvancedConfigPanel, PluginConfigPanel
from gui.log_panel import LogPanel
from utils.i18n import gettext as _


class MainWindow(tk.Tk):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.title(_("GrabTheSite - 网站抓取工具"))
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部框架（用于URL和基本配置）
        self.top_frame = ttk.LabelFrame(self.main_frame, text=_("基本配置"), padding="10")
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建URL面板
        self.url_panel = URLPanel(self.top_frame)
        self.url_panel.pack(fill=tk.X)
        
        # 创建中间框架（用于选项卡）
        self.tab_frame = ttk.Notebook(self.main_frame)
        self.tab_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建高级配置选项卡
        self.advanced_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.advanced_tab, text=_("高级配置"))
        
        # 创建高级配置面板
        self.advanced_config_panel = AdvancedConfigPanel(self.advanced_tab)
        self.advanced_config_panel.pack(fill=tk.BOTH, expand=True)
        
        # 创建插件配置选项卡
        self.plugin_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.plugin_tab, text=_("插件配置"))
        
        # 创建插件配置面板
        self.plugin_config_panel = PluginConfigPanel(self.plugin_tab)
        self.plugin_config_panel.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志选项卡
        self.log_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.log_tab, text=_("日志"))
        
        # 创建日志面板
        self.log_panel = LogPanel(self.log_tab)
        self.log_panel.pack(fill=tk.BOTH, expand=True)
        
        # 创建底部框架（用于按钮）
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建开始抓取按钮
        self.start_button = ttk.Button(self.bottom_frame, text=_("开始抓取"), command=self.on_start)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 创建停止按钮
        self.stop_button = ttk.Button(self.bottom_frame, text=_("停止"), command=self.on_stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 创建退出按钮
        self.exit_button = ttk.Button(self.bottom_frame, text=_("退出"), command=self.on_exit)
        self.exit_button.pack(side=tk.RIGHT)
        
        # 抓取状态
        self.is_crawling = False
    
    def on_start(self):
        """开始抓取按钮点击事件"""
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_crawling = True
        
        # 获取配置
        config = {
            "url": self.url_panel.get_url(),
            "depth": self.advanced_config_panel.get_depth(),
            "max_files": self.advanced_config_panel.get_max_files(),
            "output": self.advanced_config_panel.get_output(),
            "delay": self.advanced_config_panel.get_delay(),
            "no_random_delay": self.advanced_config_panel.get_no_random_delay(),
            "threads": self.advanced_config_panel.get_threads(),
            "sitemap": self.advanced_config_panel.get_sitemap(),
            "html_sitemap": self.advanced_config_panel.get_html_sitemap(),
            "resume": self.advanced_config_panel.get_resume(),
            "state_file": self.advanced_config_panel.get_state_file(),
            "js_rendering": self.advanced_config_panel.get_js_rendering(),
            "js_timeout": self.advanced_config_panel.get_js_timeout(),
            "lang": self.advanced_config_panel.get_lang(),
            "user_agent": self.advanced_config_panel.get_user_agent(),
            "plugins": self.plugin_config_panel.get_enabled_plugins(),
            "no_plugins": self.plugin_config_panel.get_no_plugins(),
            "force_download": self.advanced_config_panel.get_force_download()
        }
        
        # 验证配置
        if not config["url"]:
            self.log_panel.add_log(_("错误: 目标URL不能为空"))
            self.on_stop()
            return
        
        # 记录开始日志
        self.log_panel.add_log(_("开始抓取网站: {}").format(config["url"]))
        
        # 这里将调用抓取功能
        # 由于抓取是耗时操作，应该在单独的线程中执行
        # 为了简化示例，这里只记录日志
        self.log_panel.add_log(_("抓取配置已准备就绪"))
        self.log_panel.add_log(_("模拟抓取过程..."))
        
        # 模拟抓取完成
        self.after(2000, self.simulate_crawl_complete)
    
    def on_stop(self):
        """停止按钮点击事件"""
        # 启用开始按钮，禁用停止按钮
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_crawling = False
        
        # 记录停止日志
        self.log_panel.add_log(_("抓取已停止"))
    
    def on_exit(self):
        """退出按钮点击事件"""
        self.destroy()
    
    def simulate_crawl_complete(self):
        """模拟抓取完成"""
        if self.is_crawling:
            self.log_panel.add_log(_("抓取完成!"))
            self.on_stop()
