"""示例插件

演示插件开发的基本结构：
- 页面计数功能
- 插件生命周期管理
"""

from utils.plugin_manager import Plugin
from logger import _ as _t


class ExamplePlugin(Plugin):
    """示例插件，展示插件的基本结构和使用方法"""
    
    # 插件名称
    name = "Example Plugin"
    
    # 插件描述
    description = "示例插件，实现页面计数器功能"
    
    def __init__(self, config=None):
        """初始化插件
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.page_count = 0
        self.crawled_pages = []
    
    def on_init(self):
        """插件初始化时调用"""
        super().on_init()
        self.logger.info(_t("示例插件初始化完成"))
    
    def on_crawl_start(self, crawler):
        """抓取开始时调用
        
        Args:
            crawler: 抓取器实例
        """
        super().on_crawl_start(crawler)
        self.logger.info(_t("开始抓取，初始化页面计数器"))
        self.page_count = 0
        self.crawled_pages = []
    
    def on_page_crawled(self, url, page_content):
        """页面抓取完成时调用
        
        Args:
            url: 页面URL
            page_content: 页面内容
        """
        self.page_count += 1
        self.crawled_pages.append(url)
        if self.page_count % 5 == 0:
            self.logger.info(_t("已抓取") + f" {self.page_count} " + _t("个页面"))
    
    def on_crawl_end(self, pages):
        """抓取结束时调用
        
        Args:
            pages: 抓取的页面字典
        """
        super().on_crawl_end(pages)
        self.logger.info(_t("抓取结束，共抓取") + f" {self.page_count} " + _t("个页面"))
        self.logger.info(_t("抓取的页面列表") + f": {self.crawled_pages}")
    
    def on_cleanup(self):
        """插件清理时调用"""
        super().on_cleanup()
        self.logger.info(_t("示例插件清理完成"))
