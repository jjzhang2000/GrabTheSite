"""主窗口模块

GUI应用程序的主窗口，包含：
- URL配置面板
- 高级配置选项卡
- 插件配置选项卡
- 日志显示面板
- 控制按钮
"""

import tkinter as tk
import threading
from tkinter import ttk
from gui.config_panels import URLPanel, AdvancedConfigPanel, save_config_to_yaml
from gui.log_panel import LogPanel
from utils.i18n import gettext as _


class MainWindow(tk.Tk):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.title(_("GrabTheSite - 网站抓取工具"))
        self.geometry("750x800")
        self.minsize(650, 700)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部框架（用于URL和基本配置）
        self.top_frame = ttk.LabelFrame(self.main_frame, text=_("基本配置"), padding="8")
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建URL面板
        self.url_panel = URLPanel(self.top_frame)
        self.url_panel.pack(fill=tk.X)
        
        # 创建中间框架（用于选项卡）
        self.tab_frame = ttk.Notebook(self.main_frame)
        self.tab_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建高级配置选项卡
        self.advanced_tab = ttk.Frame(self.tab_frame)
        self.tab_frame.add(self.advanced_tab, text=_("高级配置"))
        
        # 创建高级配置面板（包含插件配置）
        self.advanced_config_panel = AdvancedConfigPanel(self.advanced_tab)
        self.advanced_config_panel.pack(fill=tk.X, expand=False)
        
        # 创建日志面板（放在选项卡下方，按钮上方）
        self.log_frame = ttk.LabelFrame(self.main_frame, text=_("日志"), padding="5")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_panel = LogPanel(self.log_frame)
        self.log_panel.pack(fill=tk.BOTH, expand=True)
        
        # 设置日志处理器，将日志输出到GUI
        import logging
        self.log_panel.setup_logger_handler()  # 设置根logger
        # 也为 grab_the_site 模块设置
        self.log_panel.setup_logger_handler('grab_the_site')
        
        # 创建底部框架（用于按钮）
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 创建开始抓取按钮
        self.start_button = ttk.Button(self.bottom_frame, text=_("开始抓取"), command=self.on_start)
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # 创建停止按钮
        self.stop_button = ttk.Button(self.bottom_frame, text=_("停止"), command=self.on_stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # 创建退出按钮
        self.exit_button = ttk.Button(self.bottom_frame, text=_("退出"), command=self.on_exit)
        self.exit_button.pack(side=tk.RIGHT)
        
        # 抓取状态
        self.is_crawling = False
        self.stop_event = threading.Event()  # 用于通知抓取线程停止
    
    def on_start(self):
        """开始抓取按钮点击事件"""
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_crawling = True
        self.stop_event.clear()  # 清除停止标志
        
        # 获取配置
        config = {
            "url": self.url_panel.get_url(),
            **self.advanced_config_panel.get_config()
        }
        
        # 保存配置到config.yaml
        save_config_to_yaml(config)
        self.log_panel.add_log(_("配置已保存到 config.yaml"))
        
        # 验证配置
        if not config["url"]:
            self.log_panel.add_log(_("错误: 目标URL不能为空"))
            self.on_stop()
            return
        
        # 记录开始日志
        self.log_panel.add_log(_("开始抓取网站: {}").format(config["url"]))
        
        # 导入抓取模块
        from grab_the_site import main as grab_main
        import threading
        
        # 在单独的线程中执行抓取，避免阻塞GUI
        def crawl_thread():
            try:
                # 调用抓取功能
                self.log_panel.add_log(_("抓取配置已准备就绪"))
                self.log_panel.add_log(_("开始抓取..."))
                
                # 检查是否收到停止信号
                if self.stop_event.is_set():
                    self.log_panel.add_log(_("抓取已被用户取消"))
                    return
                
                # 将配置转换为命令行参数（将snake_case转换为kebab-case）
                args_list = []
                for key, value in config.items():
                    # 将下划线转换为短横线（如max_files -> max-files）
                    arg_name = key.replace('_', '-')
                    if value is True:
                        args_list.append(f"--{arg_name}")
                    elif value is False:
                        continue
                    elif isinstance(value, list):
                        if value:
                            args_list.append(f"--{arg_name}")
                            args_list.extend(value)
                    else:
                        args_list.append(f"--{arg_name}")
                        args_list.append(str(value))
                
                # 调用主抓取函数
                grab_main(args_list)
                
                # 记录完成日志
                self.log_panel.add_log(_("抓取完成!"))
            except Exception as e:
                # 记录错误日志
                self.log_panel.add_log(_("错误: {}").format(str(e)))
            finally:
                # 停止抓取
                self.on_stop()
        
        # 启动抓取线程
        thread = threading.Thread(target=crawl_thread)
        thread.daemon = True
        thread.start()
    
    def on_stop(self):
        """停止按钮点击事件"""
        if not self.is_crawling:
            return  # 如果没有正在抓取，直接返回
        
        # 设置停止标志，通知抓取线程
        self.stop_event.set()
        
        # 启用开始按钮，禁用停止按钮
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_crawling = False
        
        # 记录停止日志
        self.log_panel.add_log(_("正在停止抓取..."))
    
    def on_exit(self):
        """退出按钮点击事件"""
        self.destroy()
    

