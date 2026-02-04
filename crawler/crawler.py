# 核心抓取模块

from config import TARGET_URL, MAX_DEPTH, MAX_FILES, OUTPUT_DIR
from crawler.crawl_site import CrawlSite
from crawler.save_site import SaveSite
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


class SiteCrawler:
    """网站爬虫类，整合抓取和保存功能"""
    
    def __init__(self):
        """初始化爬虫"""
        self.target_url = TARGET_URL
        self.max_depth = MAX_DEPTH
        self.max_files = MAX_FILES
        self.output_dir = OUTPUT_DIR
    
    def crawl(self):
        """开始抓取"""
        # 创建抓取器实例
        crawler = CrawlSite(self.target_url, self.max_depth, self.max_files, self.output_dir)
        
        # 抓取网站，获取暂存页面
        pages = crawler.crawl_site()
        
        # 创建保存器实例
        saver = SaveSite(self.target_url, self.output_dir, crawler.static_resources)
        
        # 保存页面到磁盘
        saver.save_site(pages)

