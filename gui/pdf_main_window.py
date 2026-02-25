"""PDF 主窗口模块

PDFtheSite GUI应用程序的主窗口，继承自 BaseMainWindow。
与 MainWindow 的区别：
- 调用 pdf_the_site.py 而不是 grab_the_site.py
- 添加 PDF 配置选项
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from gui.base_main_window import BaseMainWindow


class PdfMainWindow(BaseMainWindow):
    """PDF 主窗口类"""

    def __init__(self):
        """初始化 PDF 主窗口"""
        super().__init__(
            title="PDFtheSite - 网站抓取到PDF",
            geometry="750x850",
            min_size=(650, 750)
        )

    def _create_specific_config_panel(self) -> None:
        """创建 PDF 配置面板"""
        self.pdf_frame = ttk.LabelFrame(self.main_frame, text=_("PDF配置"), padding="8")
        self.pdf_frame.pack(fill=tk.X, pady=(0, 10))

        self.pdf_config_panel = PdfConfigPanel(self.pdf_frame)
        self.pdf_config_panel.pack(fill=tk.X)

    def _setup_log_handlers(self) -> None:
        """设置日志处理器"""
        self.log_panel.setup_logger_handler()  # 根 logger
        self.log_panel.setup_logger_handler('pdf_the_site')
        self.log_panel.setup_logger_handler('crawler.crawl_site')
        self.log_panel.setup_logger_handler('crawler.downloader')
        self.log_panel.setup_logger_handler('plugins.pdf_plugin')

    def _get_start_button_text(self) -> str:
        """获取开始按钮文本"""
        return "抓取到PDF"

    def _get_window_title(self) -> str:
        """获取窗口标题"""
        return "PDFtheSite - 网站抓取到PDF"

    def _update_specific_ui_texts(self) -> None:
        """更新特定组件文本"""
        self.pdf_frame.config(text=_("PDF配置"))

    def _get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            **self._get_base_config(),
            **self.pdf_config_panel.get_config()
        }

    def _start_crawl_thread(self, config: Dict[str, Any]) -> None:
        """启动抓取线程"""
        from pdf_the_site import main_entry as pdf_main

        def crawl_thread():
            args_list = self._convert_config_to_args(config)
            self._run_crawl(pdf_main, args_list, "PDF生成完成!")

        self.crawl_thread = self._create_crawl_thread(crawl_thread)
        self.crawl_thread.start()


class PdfConfigPanel(ttk.Frame):
    """PDF 配置面板"""

    def __init__(self, parent):
        """初始化 PDF 配置面板

        Args:
            parent: 父容器
        """
        super().__init__(parent)

        # 创建PDF配置变量
        self.pdf_filename_var = tk.StringVar(value="site.pdf")
        self.pdf_format_var = tk.StringVar(value="A4")
        self.pdf_margin_var = tk.IntVar(value=20)

        # 创建界面
        self._create_widgets()

        # 注册语言切换回调
        from utils.i18n import register_language_change_callback
        register_language_change_callback(self._update_ui_texts)

    def _create_widgets(self):
        """创建界面组件"""
        # 第一行：文件名和格式
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text=_("文件名:")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row1, textvariable=self.pdf_filename_var, width=20).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row1, text=_("格式:")).pack(side=tk.LEFT, padx=(0, 5))
        format_combo = ttk.Combobox(row1, textvariable=self.pdf_format_var, values=["A4", "Letter", "Legal"], width=10, state="readonly")
        format_combo.pack(side=tk.LEFT)

        # 第二行：边距
        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text=_("边距(mm):")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Spinbox(row2, from_=0, to=50, textvariable=self.pdf_margin_var, width=8).pack(side=tk.LEFT)

    def _update_ui_texts(self):
        """更新界面文本"""
        # 更新标签文本
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for label in child.winfo_children():
                    if isinstance(label, ttk.Label):
                        current_text = label.cget("text")
                        if "文件名" in current_text or "filename" in current_text.lower():
                            label.config(text=_("文件名:"))
                        elif "格式" in current_text or "format" in current_text.lower():
                            label.config(text=_("格式:"))
                        elif "边距" in current_text or "margin" in current_text.lower():
                            label.config(text=_("边距(mm):"))

    def get_config(self) -> Dict[str, Any]:
        """获取PDF配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "pdf_filename": self.pdf_filename_var.get(),
            "pdf_format": self.pdf_format_var.get(),
            "pdf_margin": self.pdf_margin_var.get()
        }
