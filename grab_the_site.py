#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GrabTheSite 主脚本
初始版本原型0
"""

import os
import sys
from crawler.crawler import SiteCrawler


def main():
    """主函数"""
    print("开始抓取网站...")
    
    # 创建爬虫实例
    crawler = SiteCrawler()
    
    # 开始抓取
    crawler.crawl()
    
    print("抓取完成！")


if __name__ == "__main__":
    main()
