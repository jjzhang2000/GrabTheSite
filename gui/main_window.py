"""主窗口模块

GUI应用程序的主窗口，包含：
- URL输入面板
- 高级配置选项卡
- 插件配置选项卡
- 日志显示面板
- 控制按钮
"""

import tkinter as tk
import threading
import customtkinter as ctk

# 设置CustomTkinter主题
ctk.set_appearance_mode("system")  # 跟随系统主题
ctk.set_default_color_theme("blue")  # 设置默认颜色主题

# 禁用控制台日志输出（必须在导入其他模块之前）
from logger import disable_console_output
disable_console_output()

from gui.config_panels import URLPanel, AdvancedConfigPanel, PluginConfigPanel, save_config_to_yaml
from gui.log_panel import LogPanel
from utils.i18n import gettext as _, register_language_change_callback, init_i18n
from config import load_config


class MainWindow(ctk.CTk):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 根据配置初始化语言
        try:
            config = load_config()
            i18n_config = config.get('i18n', {})
            lang = i18n_config.get('lang', 'zh_CN')
            init_i18n(lang)
        except Exception:
            init_i18n('zh_CN')  # 默认中文
        
        self.title(_("GrabTheSite - 网站抓取工具"))
        self.geometry("750x800")
        self.minsize(650, 700)
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建选项卡视图
        self.tab_view = ctk.CTkTabview(self.main_frame, corner_radius=8)
        self.tab_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建基本配置选项卡
        self.basic_tab = self.tab_view.add(_('基本配置'))
        # 创建URL面板
        self.url_panel = URLPanel(self.basic_tab)
        self.url_panel.pack(fill=tk.X, padx=10, pady=10)
        
        # 创建高级配置选项卡
        self.advanced_tab = self.tab_view.add(_('高级配置'))
        # 创建高级配置面板
        self.advanced_config_panel = AdvancedConfigPanel(self.advanced_tab)
        self.advanced_config_panel.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        
        # 创建日志选项卡
        self.log_tab = self.tab_view.add(_('日志'))
        # 创建日志面板
        self.log_panel = LogPanel(self.log_tab)
        self.log_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 设置日志处理器，将日志输出到GUI
        import logging
        self.log_panel.setup_logger_handler()  # 设置根logger
        # 也为各个模块设置
        self.log_panel.setup_logger_handler('grab_the_site')
        self.log_panel.setup_logger_handler('crawler.crawl_site')
        self.log_panel.setup_logger_handler('crawler.downloader')
        
        # 创建底部框架（用于按钮）
        self.bottom_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0), padx=5)
        
        # 创建开始抓取按钮
        self.start_button = ctk.CTkButton(self.bottom_frame, text=_('开始抓取'), command=self.on_start, font=ctk.CTkFont(size=12))
        self.start_button.pack(side=tk.LEFT, padx=(10, 15), pady=10)
        
        # 创建停止按钮
        self.stop_button = ctk.CTkButton(self.bottom_frame, text=_('停止'), command=self.on_stop, state=tk.DISABLED, font=ctk.CTkFont(size=12))
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15), pady=10)
        
        # 创建退出按钮
        self.exit_button = ctk.CTkButton(self.bottom_frame, text=_('退出'), command=self.on_exit, font=ctk.CTkFont(size=12))
        self.exit_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # 抓取状态
        self.is_crawling = False
        self.stop_event = threading.Event()  # 用于通知抓取线程停止
        self.crawl_thread = None  # 抓取线程引用
        
        # 注册语言切换回调
        register_language_change_callback(self._update_ui_texts)
        
        # 设置窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
    
    def _update_ui_texts(self):
        """更新界面文本（语言切换后调用）"""
        # 重新导入gettext以确保使用最新的翻译
        from utils.i18n import gettext as _
        
        # 更新窗口标题
        self.title(_("GrabTheSite - 网站抓取工具"))
        
        # 更新选项卡文本
        self.tab_view._tab_names = {
            0: _('基本配置'),
            1: _('高级配置'),
            2: _('日志')
        }
        self.tab_view._update_tabs()
        
        # 更新按钮文本
        self.start_button.config(text=_("开始抓取"))
        self.stop_button.config(text=_("停止"))
        self.exit_button.config(text=_("退出"))
        
        # 更新URL面板文本
        self.url_panel.url_label.config(text=_("目标URL:"))
    
    def on_start(self):
        """开始抓取按钮点击事件"""
        import threading
        
        # 检查当前线程数
        thread_count = threading.active_count()
        self.log_panel.add_log(_("当前活跃线程数: {}").format(thread_count))
        
        # 如果线程数异常，警告用户
        if thread_count > 20:
            self.log_panel.add_log(_("警告: 线程数过多 ({})，建议重启程序").format(thread_count))
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_crawling = True
        self.stop_event.clear()  # 清除停止标志
        
        # 获取配置
        config = {
            "url": self.url_panel.get_url(),
            **self.url_panel.get_config(),
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
        
        # 重新设置日志处理器（确保在多次抓取后能正常工作）
        self.log_panel.setup_logger_handler()  # 根 logger
        self.log_panel.setup_logger_handler('grab_the_site')
        self.log_panel.setup_logger_handler('crawler.crawl_site')
        self.log_panel.setup_logger_handler('crawler.downloader')
        
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
                
                # 调用主抓取函数，传递stop_event
                grab_main(args_list, self.stop_event)
                
                # 记录完成日志
                self.log_panel.add_log(_("抓取完成!"))
            except Exception as e:
                # 记录错误日志
                self.log_panel.add_log(_("错误: {}").format(str(e)))
            finally:
                # 抓取结束（正常完成或被停止），重置UI状态
                # 注意：这里不调用on_stop，因为on_stop会等待线程结束，可能导致死锁
                if self.is_crawling:
                    self.is_crawling = False
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
        
        # 启动抓取线程
        self.crawl_thread = threading.Thread(target=crawl_thread)
        self.crawl_thread.daemon = True
        self.crawl_thread.start()
    
    def on_stop(self):
        """停止按钮点击事件"""
        if not self.is_crawling:
            return  # 如果没有正在抓取，直接返回
        
        # 设置停止标志，通知抓取线程
        self.stop_event.set()
        
        # 记录停止日志
        self.log_panel.add_log(_("正在停止抓取..."))
        
        # 等待抓取线程结束（最多等待5秒）
        if self.crawl_thread:
            self.crawl_thread.join(timeout=5)
            if self.crawl_thread.is_alive():
                self.log_panel.add_log(_("警告: 抓取线程未能及时停止"))
        
        # 重置状态
        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_panel.add_log(_("抓取已停止"))
    
    def on_exit(self):
        """退出按钮点击事件"""
        import logging
        
        # 如果正在抓取，先发送停止信号
        if self.is_crawling:
            self.log_panel.add_log(_("正在停止抓取并退出..."))
            self.stop_event.set()
        
        # 无论是否正在抓取，都确保抓取线程已结束
        if self.crawl_thread and self.crawl_thread.is_alive():
            self.log_panel.add_log(_("等待抓取线程结束..."))
            
            # 等待抓取线程结束，最多等待10秒
            wait_time = 0
            max_wait = 10
            while self.crawl_thread and self.crawl_thread.is_alive() and wait_time < max_wait:
                self.update()  # 保持UI响应
                import time
                time.sleep(0.2)
                wait_time += 0.2
            
            # 如果线程仍在运行，强制终止
            if self.crawl_thread and self.crawl_thread.is_alive():
                self.log_panel.add_log(_("警告: 抓取线程未能及时停止"))
        
        # 清空所有队列，释放阻塞的线程
        self.log_panel.add_log(_("正在清空队列..."))
        try:
            # 导入并清空爬虫队列
            from crawler.crawl_site import CrawlSite
            # 注意：这里无法直接访问队列，但守护线程会在主程序退出时自动终止
            pass
        except:
            pass
        
        # 关闭所有日志处理器，释放文件锁
        self.log_panel.add_log(_("正在清理资源..."))
        from logger import close_all_loggers
        close_all_loggers()
        
        # 销毁窗口
        self.destroy()
        
        # 给守护线程一点时间自行终止
        import time
        time.sleep(0.5)
        
        # 强制终止整个进程（包括所有线程）
        # 注意：os._exit 不会执行清理操作，但会立即终止所有线程
        import os
        os._exit(0)
    

