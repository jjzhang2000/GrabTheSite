"""主窗口基类模块

提供 MainWindow 和 PdfMainWindow 的公共基类，消除重复代码。
"""

import tkinter as tk
import threading
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List

# 禁用控制台日志输出（必须在导入其他模块之前）
from logger import disable_console_output
disable_console_output()

from gui.config_panels import BasicConfigPanel, AdvancedConfigPanel, save_config_to_yaml
from gui.log_panel import LogPanel
from utils.i18n import gettext as _, register_language_change_callback, init_i18n
from config import load_config


class BaseMainWindow(tk.Tk, ABC):
    """主窗口基类

    提供 MainWindow 和 PdfMainWindow 的公共功能：
    - 窗口初始化和配置
    - 基本配置面板
    - 高级配置面板
    - 日志面板
    - 控制按钮
    - 线程管理
    - 语言切换支持
    """

    def __init__(self, title: str, geometry: str, min_size: tuple = (650, 700)):
        """初始化主窗口

        Args:
            title: 窗口标题
            geometry: 窗口大小
            min_size: 最小窗口大小 (width, height)
        """
        super().__init__()

        # 根据配置初始化语言
        self._init_i18n()

        # 设置窗口属性
        self.title(_(title))
        self.geometry(geometry)
        self.minsize(*min_size)

        # 创建主框架
        self._create_main_frame()

        # 创建基本配置面板
        self._create_basic_config_panel()

        # 创建特定配置面板（子类实现）
        self._create_specific_config_panel()

        # 创建高级配置面板
        self._create_advanced_config_panel()

        # 创建日志面板
        self._create_log_panel()

        # 创建底部按钮
        self._create_bottom_buttons()

        # 抓取状态
        self.is_crawling = False
        self.stop_event = threading.Event()
        self.crawl_thread = None

        # 注册语言切换回调
        register_language_change_callback(self._update_ui_texts)

        # 设置窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _init_i18n(self) -> None:
        """初始化国际化"""
        try:
            config = load_config()
            i18n_config = config.get('i18n', {})
            lang = i18n_config.get('lang', 'zh_CN')
            init_i18n(lang)
        except Exception:
            init_i18n('zh_CN')  # 默认中文

    def _create_main_frame(self) -> None:
        """创建主框架"""
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def _create_basic_config_panel(self) -> None:
        """创建基本配置面板"""
        self.top_frame = ttk.LabelFrame(self.main_frame, text=_("基本配置"), padding="8")
        self.top_frame.pack(fill=tk.X, pady=(0, 10))

        self.basic_config_panel = BasicConfigPanel(self.top_frame)
        self.basic_config_panel.pack(fill=tk.X)

    def _create_advanced_config_panel(self) -> None:
        """创建高级配置面板"""
        self.advanced_frame = ttk.LabelFrame(self.main_frame, text=_("高级配置"), padding="8")
        self.advanced_frame.pack(fill=tk.X, pady=(0, 10))

        self.advanced_config_panel = AdvancedConfigPanel(self.advanced_frame)
        self.advanced_config_panel.pack(fill=tk.X, expand=False)

    def _create_log_panel(self) -> None:
        """创建日志面板"""
        self.log_frame = ttk.LabelFrame(self.main_frame, text=_("日志"), padding="5")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_panel = LogPanel(self.log_frame)
        self.log_panel.pack(fill=tk.BOTH, expand=True)

        # 设置日志处理器
        self._setup_log_handlers()

    @abstractmethod
    def _setup_log_handlers(self) -> None:
        """设置日志处理器（子类实现）"""
        pass

    @abstractmethod
    def _create_specific_config_panel(self) -> None:
        """创建特定配置面板（子类实现）"""
        pass

    def _create_bottom_buttons(self) -> None:
        """创建底部按钮"""
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # 创建开始按钮
        self.start_button = ttk.Button(
            self.bottom_frame,
            text=self._get_start_button_text(),
            command=self.on_start
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))

        # 创建停止按钮
        self.stop_button = ttk.Button(
            self.bottom_frame,
            text=_("停止"),
            command=self.on_stop,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))

        # 创建退出按钮
        self.exit_button = ttk.Button(
            self.bottom_frame,
            text=_("退出"),
            command=self.on_exit
        )
        self.exit_button.pack(side=tk.RIGHT)

    @abstractmethod
    def _get_start_button_text(self) -> str:
        """获取开始按钮文本（子类实现）"""
        pass

    def _update_ui_texts(self) -> None:
        """更新界面文本（语言切换后调用）"""
        from utils.i18n import gettext as _

        # 更新窗口标题
        self.title(_(self._get_window_title()))

        # 更新标签框架文本
        self.top_frame.config(text=_("基本配置"))
        self.advanced_frame.config(text=_("高级配置"))
        self.log_frame.config(text=_("日志"))

        # 更新按钮文本
        self.start_button.config(text=_(self._get_start_button_text()))
        self.stop_button.config(text=_("停止"))
        self.exit_button.config(text=_("退出"))

        # 更新特定组件文本
        self._update_specific_ui_texts()

    @abstractmethod
    def _get_window_title(self) -> str:
        """获取窗口标题（子类实现）"""
        pass

    @abstractmethod
    def _update_specific_ui_texts(self) -> None:
        """更新特定组件文本（子类实现）"""
        pass

    def _get_base_config(self) -> Dict[str, Any]:
        """获取基本配置"""
        return {
            **self.basic_config_panel.get_config(),
            **self.advanced_config_panel.get_config()
        }

    def on_start(self) -> None:
        """开始抓取按钮点击事件"""
        # 检查当前线程数
        thread_count = threading.active_count()
        self.log_panel.add_log(_("当前活跃线程数: {}").format(thread_count))

        # 如果线程数异常，警告用户
        if thread_count > 20:
            self.log_panel.add_log(_("警告: 线程数过多 ({}), 建议重启程序").format(thread_count))

        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_crawling = True
        self.stop_event.clear()

        # 获取配置
        config = self._get_config()

        # 保存配置
        save_config_to_yaml(config)
        self.log_panel.add_log(_("配置已保存到 config.yaml"))

        # 验证配置
        if not config.get("url"):
            self.log_panel.add_log(_("错误: 目标URL不能为空"))
            self.on_stop()
            return

        # 记录开始日志
        self.log_panel.add_log(_("开始抓取网站: {}").format(config["url"]))

        # 设置日志处理器
        self._setup_log_handlers()

        # 启动抓取线程
        self._start_crawl_thread(config)

    @abstractmethod
    def _get_config(self) -> Dict[str, Any]:
        """获取完整配置（子类实现）"""
        pass

    @abstractmethod
    def _start_crawl_thread(self, config: Dict[str, Any]) -> None:
        """启动抓取线程（子类实现）"""
        pass

    def _create_crawl_thread(self, target: Callable, args: tuple = ()) -> threading.Thread:
        """创建抓取线程

        Args:
            target: 线程目标函数
            args: 线程参数

        Returns:
            threading.Thread: 创建的线程
        """
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        return thread

    def _run_crawl(self, crawl_func: Callable, args_list: List[str], success_msg: str) -> None:
        """运行抓取

        Args:
            crawl_func: 抓取函数
            args_list: 命令行参数列表
            success_msg: 成功消息
        """
        try:
            self.log_panel.add_log(_("抓取配置已准备就绪"))
            self.log_panel.add_log(_("命令行参数: {}").format(' '.join(args_list)))
            self.log_panel.add_log(_("开始抓取..."))

            if self.stop_event.is_set():
                self.log_panel.add_log(_("抓取已被用户取消"))
                return

            crawl_func(args_list, self.stop_event)
            self.log_panel.add_log(_(success_msg))
        except Exception as e:
            self.log_panel.add_log(_("错误: {}").format(str(e)))
        finally:
            if self.is_crawling:
                self.is_crawling = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)

    def _convert_config_to_args(self, config: Dict[str, Any]) -> List[str]:
        """将配置转换为命令行参数

        Args:
            config: 配置字典

        Returns:
            List[str]: 命令行参数列表
        """
        args_list = []
        for key, value in config.items():
            arg_name = key.replace('_', '-')
            if value is True:
                args_list.append(f"--{arg_name}")
            elif value is False:
                continue
            elif isinstance(value, list):
                if value:
                    args_list.append(f"--{arg_name}")
                    args_list.extend(value)
            elif isinstance(value, (str, int, float)):
                args_list.append(f"--{arg_name}")
                # 语言参数需要保持大小写
                if key == 'lang':
                    args_list.append(str(value))
                else:
                    args_list.append(str(value))
            # 忽略其他类型（如字典、None等）
        return args_list

    def on_stop(self) -> None:
        """停止按钮点击事件"""
        if not self.is_crawling:
            return

        self.stop_event.set()
        self.log_panel.add_log(_("正在停止抓取..."))

        if self.crawl_thread:
            self.crawl_thread.join(timeout=5)
            if self.crawl_thread.is_alive():
                self.log_panel.add_log(_("警告: 抓取线程未能及时停止"))

        self.is_crawling = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_panel.add_log(_("抓取已停止"))

    def on_exit(self) -> None:
        """退出按钮点击事件"""
        import sys

        if self.is_crawling:
            self.log_panel.add_log(_("正在停止抓取并退出..."))
            self.stop_event.set()

        if self.crawl_thread and self.crawl_thread.is_alive():
            self.log_panel.add_log(_("等待抓取线程结束..."))
            self.crawl_thread.join(timeout=5)
            if self.crawl_thread.is_alive():
                self.log_panel.add_log(_("警告: 抓取线程未能及时停止"))

        self.log_panel.add_log(_("正在清理资源..."))
        from logger import close_all_loggers
        close_all_loggers()

        self.destroy()
        sys.exit(0)
