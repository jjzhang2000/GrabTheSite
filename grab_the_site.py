#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GrabTheSite 主脚本
初始版本原型0
"""

import os
from crawler.crawler import SiteCrawler
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("开始抓取网站...")
    
    # 创建爬虫实例
    crawler = SiteCrawler()
    
    # 开始抓取
    crawler.crawl()
    
    logger.info("抓取完成！")


if __name__ == "__main__":
    main()
