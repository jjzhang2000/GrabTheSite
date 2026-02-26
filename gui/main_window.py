"""主窗口模块

GUI应用程序的主窗口，继承自 BaseMainWindow。
"""

from typing import Dict, Any

from gui.base_main_window import BaseMainWindow


class MainWindow(BaseMainWindow):
    """主窗口类"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__(
            title="GrabTheSite - 网站抓取工具",
            geometry="750x800",
            min_size=(650, 700)
        )

    def _create_specific_config_panel(self) -> None:
        """创建特定配置面板（MainWindow 不需要额外配置）"""
        pass

    def _setup_log_handlers(self) -> None:
        """设置日志处理器"""
        self.log_panel.setup_logger_handler()  # 根 logger
        self.log_panel.setup_logger_handler('grab_the_site')
        self.log_panel.setup_logger_handler('crawler.crawl_site')
        self.log_panel.setup_logger_handler('crawler.downloader')

    def _get_start_button_text(self) -> str:
        """获取开始按钮文本"""
        return "开始抓取"

    def _get_window_title(self) -> str:
        """获取窗口标题"""
        return "GrabTheSite - 网站抓取工具"

    def _update_specific_ui_texts(self) -> None:
        """更新特定组件文本（MainWindow 没有特定组件）"""
        pass

    def _get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._get_base_config()

    def _save_specific_config(self) -> None:
        """保存特定配置（MainWindow 没有特定配置）"""
        pass

    def _start_crawl_thread(self, config: Dict[str, Any]) -> None:
        """启动抓取线程"""
        from grab_the_site import main as grab_main

        def crawl_thread():
            args_list = self._convert_config_to_args(config)
            self._run_crawl(grab_main, args_list, "抓取完成!")

        self.crawl_thread = self._create_crawl_thread(crawl_thread)
        self.crawl_thread.start()
