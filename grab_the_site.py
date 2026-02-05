#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GrabTheSite 主脚本
初始版本原型0
"""

import os
from config import TARGET_URL, MAX_DEPTH, MAX_FILES, OUTPUT_DIR
from crawler.crawl_site import CrawlSite
from crawler.save_site import SaveSite
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("开始抓取网站...")
    
    # 创建抓取器实例
    crawler = CrawlSite(TARGET_URL, MAX_DEPTH, MAX_FILES, OUTPUT_DIR)
    
    # 抓取网站，获取暂存页面
    pages = crawler.crawl_site()
    
    # 创建保存器实例
    saver = SaveSite(TARGET_URL, OUTPUT_DIR, crawler.static_resources)
    
    # 保存页面到磁盘
    saver.save_site(pages)
    
    logger.info("抓取完成！")


if __name__ == "__main__":
    main()
