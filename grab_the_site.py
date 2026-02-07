#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GrabTheSite 主脚本
初始版本原型0
"""

import os
import argparse
from config import load_config, CONFIG
from crawler.crawl_site import CrawlSite
from crawler.save_site import SaveSite
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="GrabTheSite - 网站抓取工具，支持离线浏览"
    )
    
    parser.add_argument(
        "--url", "-u",
        type=str,
        default=None,
        help="目标网站 URL"
    )
    
    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=None,
        help="最大抓取深度"
    )
    
    parser.add_argument(
        "--max-files", "-m",
        type=int,
        default=None,
        help="最大文件数量"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出目录"
    )
    
    parser.add_argument(
        "--delay", "-t",
        type=float,
        default=None,
        help="请求间隔（秒）"
    )
    
    parser.add_argument(
        "--no-random-delay",
        action="store_true",
        help="禁用随机延迟"
    )
    
    parser.add_argument(
        "--threads", "-p",
        type=int,
        default=None,
        help="线程数"
    )
    
    parser.add_argument(
        "--sitemap",
        action="store_true",
        help="生成站点地图"
    )
    
    parser.add_argument(
        "--no-sitemap",
        action="store_true",
        help="不生成站点地图"
    )
    
    parser.add_argument(
        "--html-sitemap",
        action="store_true",
        help="生成 HTML 格式的站点地图"
    )
    
    parser.add_argument(
        "--no-html-sitemap",
        action="store_true",
        help="不生成 HTML 格式的站点地图"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="启用断点续传"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="禁用断点续传"
    )
    
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="状态文件路径"
    )
    
    return parser.parse_args()


def update_config(args):
    """根据命令行参数更新配置
    
    Args:
        args: 解析后的命令行参数
    
    Returns:
        dict: 更新后的配置
    """
    # 加载配置
    config = load_config()
    
    # 更新配置
    if args.url:
        config["target_url"] = args.url
        # 从新的 target_url 中提取域名作为 site_name
        from urllib.parse import urlparse
        parsed_url = urlparse(args.url)
        site_name = parsed_url.netloc
        if "output" not in config:
            config["output"] = {}
        config["output"]["site_name"] = site_name
    
    if args.depth is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["max_depth"] = args.depth
    
    if args.max_files is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["max_files"] = args.max_files
    
    if args.output:
        if "output" not in config:
            config["output"] = {}
        config["output"]["base_dir"] = args.output
        # 重新计算完整输出路径
        if "site_name" in config["output"]:
            config["output"]["full_path"] = os.path.join(
                config["output"]["base_dir"],
                config["output"]["site_name"]
            )
    
    if args.delay is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["delay"] = args.delay
    
    if args.no_random_delay:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["random_delay"] = False
    
    if args.threads is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["threads"] = args.threads
    
    # 处理站点地图配置
    if "sitemap" not in config["output"]:
        config["output"]["sitemap"] = {}
    
    # 处理 --sitemap 和 --no-sitemap 参数
    if args.sitemap:
        config["output"]["sitemap"]["enable"] = True
    elif args.no_sitemap:
        config["output"]["sitemap"]["enable"] = False
    
    # 处理 --html-sitemap 和 --no-html-sitemap 参数
    if args.html_sitemap:
        config["output"]["sitemap"]["enable_html"] = True
    elif args.no_html_sitemap:
        config["output"]["sitemap"]["enable_html"] = False
    
    # 处理断点续传配置
    if "resume" not in config:
        config["resume"] = {}
    
    # 处理 --resume 和 --no-resume 参数
    if args.resume:
        config["resume"]["enable"] = True
    elif args.no_resume:
        config["resume"]["enable"] = False
    
    # 处理 --state-file 参数
    if args.state_file:
        config["resume"]["state_file"] = args.state_file
    
    # 确保完整输出路径被正确计算
    if "output" in config and "base_dir" in config["output"] and "site_name" in config["output"]:
        config["output"]["full_path"] = os.path.join(
            config["output"]["base_dir"],
            config["output"]["site_name"]
        )
    
    return config


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 更新配置
    config = update_config(args)
    
    # 提取配置参数
    target_url = config["target_url"]
    max_depth = config["crawl"].get("max_depth", 1)
    max_files = config["crawl"].get("max_files", 10)
    output_dir = config["output"].get("full_path", "output")
    
    # 提取延迟相关配置
    delay = config["crawl"].get("delay", 1)
    random_delay = config["crawl"].get("random_delay", True)
    threads = config["crawl"].get("threads", 4)
    
    logger.info("开始抓取网站...")
    logger.info(f"目标网站: {target_url}")
    logger.info(f"最大深度: {max_depth}")
    logger.info(f"最大文件数: {max_files}")
    logger.info(f"请求间隔: {delay} 秒")
    logger.info(f"随机延迟: {'启用' if random_delay else '禁用'}")
    logger.info(f"线程数: {threads}")
    logger.info(f"输出路径: {output_dir}")
    
    # 显示断点续传配置
    resume_config = config.get("resume", {})
    resume_enable = resume_config.get("enable", True)
    state_file = resume_config.get("state_file", "state/grabthesite.json")
    logger.info(f"断点续传: {'启用' if resume_enable else '禁用'}")
    if resume_enable:
        logger.info(f"状态文件: {state_file}")
    
    # 创建抓取器实例
    crawler = CrawlSite(target_url, max_depth, max_files, output_dir, threads=threads)
    
    # 抓取网站，获取暂存页面
    pages = crawler.crawl_site()
    
    logger.info(f"抓取完成，开始保存页面，共 {len(pages)} 个页面")
    
    # 创建保存器实例
    saver = SaveSite(target_url, output_dir, crawler.static_resources)
    
    # 保存页面到磁盘
    saver.save_site(pages)
    
    # 生成站点地图
    sitemap_config = config["output"].get("sitemap", {})
    sitemap_enable = sitemap_config.get("enable", False)
    sitemap_html_enable = sitemap_config.get("enable_html", False)
    
    if sitemap_enable:
        from utils.sitemap_generator import SitemapGenerator
        sitemap_generator = SitemapGenerator(target_url, output_dir)
        # 如果 pages 字典不为空，使用 pages（包含本地文件路径和页面内容），否则使用 visited_urls
        sitemap_data = pages if pages else crawler.visited_urls
        sitemap_generator.generate_sitemap(sitemap_data)
    
    # 生成 HTML 格式的站点地图
    if sitemap_html_enable:
        from utils.sitemap_generator import SitemapGenerator
        sitemap_generator = SitemapGenerator(target_url, output_dir)
        # 如果 pages 字典不为空，使用 pages（包含本地文件路径和页面内容），否则使用 visited_urls
        sitemap_data = pages if pages else crawler.visited_urls
        sitemap_generator.generate_html_sitemap(sitemap_data)
    
    logger.info("抓取完成！")


if __name__ == "__main__":
    main()
