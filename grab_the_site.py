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
from utils.i18n import init_i18n, gettext as _

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
    
    # JavaScript渲染相关参数
    parser.add_argument(
        "--js-rendering",
        action="store_true",
        help="启用JavaScript渲染"
    )
    
    parser.add_argument(
        "--no-js-rendering",
        action="store_true",
        help="禁用JavaScript渲染"
    )
    
    parser.add_argument(
        "--js-timeout",
        type=int,
        default=None,
        help="JavaScript渲染超时时间（秒）"
    )
    
    # 国际化相关参数
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        help="语言代码，如 'en', 'zh_CN' 等"
    )
    
    # 用户代理相关参数
    parser.add_argument(
        "--user-agent",
        type=str,
        default=None,
        help="自定义用户代理字符串"
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
    
    # 处理JavaScript渲染配置
    if "js_rendering" not in config:
        config["js_rendering"] = {}
    
    # 处理 --js-rendering 和 --no-js-rendering 参数
    if args.js_rendering:
        config["js_rendering"]["enable"] = True
    elif args.no_js_rendering:
        config["js_rendering"]["enable"] = False
    
    # 处理 --js-timeout 参数
    if args.js_timeout is not None:
        config["js_rendering"]["timeout"] = args.js_timeout
    
    # 处理国际化配置
    if "i18n" not in config:
        config["i18n"] = {}
    
    # 处理 --lang 参数
    if args.lang is not None:
        config["i18n"]["lang"] = args.lang
    
    # 处理用户代理配置
    if args.user_agent is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["user_agent"] = args.user_agent
    
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
    
    # 初始化国际化模块
    lang = config.get("i18n", {}).get("lang", "en")
    init_i18n(lang)
    
    # 提取配置参数
    target_url = config["target_url"]
    max_depth = config["crawl"].get("max_depth", 1)
    max_files = config["crawl"].get("max_files", 10)
    output_dir = config["output"].get("full_path", "output")
    
    # 提取延迟相关配置
    delay = config["crawl"].get("delay", 1)
    random_delay = config["crawl"].get("random_delay", True)
    threads = config["crawl"].get("threads", 4)
    user_agent = config["crawl"].get("user_agent", "")
    
    logger.info(_("开始抓取网站..."))
    logger.info(f"{_("目标网站")}: {target_url}")
    logger.info(f"{_("最大深度")}: {max_depth}")
    logger.info(f"{_("最大文件数")}: {max_files}")
    logger.info(f"{_("请求间隔")}: {delay} {_("秒")}")
    logger.info(f"{_("随机延迟")}: {'启用' if random_delay else '禁用'}")
    logger.info(f"{_("线程数")}: {threads}")
    logger.info(f"{_("用户代理")}: {user_agent[:50]}..." if len(user_agent) > 50 else f"{_("用户代理")}: {user_agent}")
    logger.info(f"{_("输出路径")}: {output_dir}")
    
    # 显示断点续传配置
    resume_config = config.get("resume", {})
    resume_enable = resume_config.get("enable", True)
    state_file = resume_config.get("state_file", "state/grabthesite.json")
    logger.info(f"{_("断点续传")}: {'启用' if resume_enable else '禁用'}")
    if resume_enable:
        logger.info(f"{_("状态文件")}: {state_file}")
    
    # 显示JavaScript渲染配置
    js_rendering_config = config.get("js_rendering", {})
    js_rendering_enable = js_rendering_config.get("enable", False)
    js_rendering_timeout = js_rendering_config.get("timeout", 30)
    logger.info(f"{_("JavaScript渲染")}: {'启用' if js_rendering_enable else '禁用'}")
    if js_rendering_enable:
        logger.info(f"{_("渲染超时")}: {js_rendering_timeout}{_("秒")}")
    
    # 显示语言配置
    i18n_config = config.get("i18n", {})
    current_lang = i18n_config.get("lang", "en")
    logger.info(f"{_("当前语言")}: {current_lang}")
    
    # 创建抓取器实例
    crawler = CrawlSite(target_url, max_depth, max_files, output_dir, threads=threads)
    
    # 抓取网站，获取暂存页面
    pages = crawler.crawl_site()
    
    logger.info(_(f"抓取完成，开始保存页面，共 {len(pages)} 个页面"))
    
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
    
    logger.info(_("抓取完成！"))


if __name__ == "__main__":
    main()
