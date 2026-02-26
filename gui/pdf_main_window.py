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

    def _save_specific_config(self) -> None:
        """保存特定配置（PDF配置）"""
        self.pdf_config_panel.save_config()

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

        # 从配置文件加载默认值
        self._load_config()

        # 创建界面
        self._create_widgets()

        # 注册语言切换回调
        from utils.i18n import register_language_change_callback
        register_language_change_callback(self._update_ui_texts)

    def _load_config(self):
        """从配置文件加载PDF配置"""
        from app_config import load_config

        config = load_config()
        pdf_config = config.get("pdf", {})

        # 获取页面配置
        page_config = pdf_config.get("page", {})
        margin_config = page_config.get("margin", {})

        # 创建PDF配置变量，使用配置文件中的值或默认值
        self.pdf_filename_var = tk.StringVar(
            value=pdf_config.get("output_filename", "site.pdf")
        )
        self.pdf_format_var = tk.StringVar(
            value=page_config.get("format", "A4")
        )
        # 边距使用统一值（取上边距）
        default_margin = margin_config.get("top", 20)
        self.pdf_margin_var = tk.IntVar(value=default_margin)

    def _create_widgets(self):
        """创建界面组件 - 单行布局，标签左对齐"""
        # 单行：文件名、格式、边距
        row = ttk.Frame(self)
        row.pack(fill=tk.X, pady=5)

        # 文件名
        self.filename_label = ttk.Label(row, text=_("文件名:"))
        self.filename_label.pack(side=tk.LEFT, padx=(5, 3))
        self.filename_entry = ttk.Entry(row, textvariable=self.pdf_filename_var, width=15)
        self.filename_entry.pack(side=tk.LEFT, padx=(0, 15))

        # 格式
        self.format_label = ttk.Label(row, text=_("格式:"))
        self.format_label.pack(side=tk.LEFT, padx=(0, 3))
        self.format_combo = ttk.Combobox(
            row,
            textvariable=self.pdf_format_var,
            values=["A4", "Letter", "Legal"],
            width=8,
            state="readonly"
        )
        self.format_combo.pack(side=tk.LEFT, padx=(0, 15))

        # 边距
        self.margin_label = ttk.Label(row, text=_("边距(mm):"))
        self.margin_label.pack(side=tk.LEFT, padx=(0, 3))
        self.margin_spinbox = ttk.Spinbox(
            row,
            from_=0,
            to=50,
            textvariable=self.pdf_margin_var,
            width=5
        )
        self.margin_spinbox.pack(side=tk.LEFT, padx=(0, 0))

    def _update_ui_texts(self):
        """更新界面文本"""
        self.filename_label.config(text=_("文件名:"))
        self.format_label.config(text=_("格式:"))
        self.margin_label.config(text=_("边距(mm):"))

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

    def save_config(self):
        """保存PDF配置到config.yaml"""
        import yaml
        from app_config import USER_CONFIG_FILE

        try:
            # 读取现有配置
            existing_config = {}
            if USER_CONFIG_FILE and __import__('os').path.exists(USER_CONFIG_FILE):
                with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}

            # 更新PDF配置
            if "pdf" not in existing_config:
                existing_config["pdf"] = {}
            if "page" not in existing_config["pdf"]:
                existing_config["pdf"]["page"] = {}
            if "margin" not in existing_config["pdf"]["page"]:
                existing_config["pdf"]["page"]["margin"] = {}

            # 保存配置值
            existing_config["pdf"]["output_filename"] = self.pdf_filename_var.get()
            existing_config["pdf"]["page"]["format"] = self.pdf_format_var.get()
            margin = self.pdf_margin_var.get()
            existing_config["pdf"]["page"]["margin"]["top"] = margin
            existing_config["pdf"]["page"]["margin"]["bottom"] = margin
            existing_config["pdf"]["page"]["margin"]["left"] = margin
            existing_config["pdf"]["page"]["margin"]["right"] = margin

            # 写入文件
            with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, allow_unicode=True, sort_keys=False)

            return True
        except Exception as e:
            print(f"保存PDF配置失败: {e}")
            return False
