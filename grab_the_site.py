#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GrabTheSite 主脚本

网站抓取工具的命令行入口，负责：
1. 解析命令行参数
2. 加载和合并配置
3. 初始化插件系统
4. 启动抓取流程
5. 生成站点地图
"""

import os
import sys
import argparse
from urllib.parse import urlparse
from config import load_config, CONFIG, TARGET_URL, MAX_DEPTH, MAX_FILES, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, OUTPUT_DIR, I18N_CONFIG, PLUGIN_CONFIG, JS_RENDERING_CONFIG
from crawler.crawl_site import CrawlSite
from logger import setup_logger
from utils.i18n import init_i18n, get_current_lang

# 动态翻译函数，支持运行时语言切换
def _(message):
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)
from utils.plugin_manager import PluginManager
from utils.sitemap_generator import SitemapGenerator

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
    
    # 插件相关参数
    # 格式: --plugins plugin_name:+ 或 --plugins plugin_name:-
    # +: 启用, -: 禁用
    parser.add_argument(
        "--plugins",
        type=str,
        nargs="*",
        default=None,
        help="插件配置，格式: plugin_name:+ 或 plugin_name:- (+启用, -禁用)"
    )
    
    # 抓取相关参数
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="强制重新下载页面"
    )
    
    return parser.parse_args()


def update_config(args):
    """根据命令行参数更新配置
    
    Args:
        args: 解析后的命令行参数
    
    Returns:
        dict: 更新后的配置
    """
    config = load_config()
    
    # 根据命令行参数更新配置
    if args.url:
        config["target_url"] = args.url
        # 从 target_url 中提取域名作为 site_name
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
    
    # 站点地图配置
    if "sitemap" not in config["output"]:
        config["output"]["sitemap"] = {}
    if args.sitemap:
        config["output"]["sitemap"]["enable"] = True
    elif args.no_sitemap:
        config["output"]["sitemap"]["enable"] = False
    if args.html_sitemap:
        config["output"]["sitemap"]["enable_html"] = True
    elif args.no_html_sitemap:
        config["output"]["sitemap"]["enable_html"] = False
    
    # JavaScript渲染配置
    # JavaScript渲染超时配置
    if "js_rendering" not in config:
        config["js_rendering"] = {}
    if args.js_timeout is not None:
        config["js_rendering"]["timeout"] = args.js_timeout
    
    # 国际化配置
    if "i18n" not in config:
        config["i18n"] = {}
    if args.lang is not None:
        config["i18n"]["lang"] = args.lang
    
    # 用户代理配置
    if args.user_agent is not None:
        if "crawl" not in config:
            config["crawl"] = {}
        config["crawl"]["user_agent"] = args.user_agent
    
    # 插件配置
    # 格式: --plugins plugin_name:+ 或 plugin_name:-
    if args.plugins is not None:
        if "plugins" not in config:
            config["plugins"] = {}
        for plugin_setting in args.plugins:
            if ":" in plugin_setting:
                plugin_name, action = plugin_setting.rsplit(":", 1)
                config["plugins"][plugin_name] = (action == "+")
            else:
                # 默认启用
                config["plugins"][plugin_setting] = True
    
    # 计算完整输出路径
    if "output" in config and "base_dir" in config["output"] and "site_name" in config["output"]:
        config["output"]["full_path"] = os.path.join(
            config["output"]["base_dir"],
            config["output"]["site_name"]
        )
    
    return config


def main(args_list=None, stop_event=None):
    """主函数
    
    Args:
        args_list: 可选的参数列表，用于从GUI传递参数
        stop_event: 可选的停止事件，用于通知抓取线程停止
    """
    # 解析命令行参数
    if args_list:
        # 从参数列表解析
        original_argv = sys.argv.copy()
        sys.argv = ['grab_the_site.py'] + args_list
        try:
            args = parse_args()
        finally:
            sys.argv = original_argv
    else:
        # 从命令行解析
        args = parse_args()
    
    # 更新配置
    config = update_config(args)
    
    # 初始化国际化模块（如果尚未通过GUI设置）
    i18n_config = config.get("i18n", I18N_CONFIG)
    config_lang = i18n_config.get("lang", "en")
    # 如果当前语言与配置不同，使用配置语言（GUI已设置时会保持一致）
    current_lang = get_current_lang()
    if current_lang != config_lang:
        init_i18n(config_lang)
    
    # 初始化插件系统
    # 插件配置格式: {plugin_name: True/False}
    # 例如: {'save_plugin': True, 'example_plugin': False}
    plugin_config = config.get("plugins", {})
    
    # 创建插件管理器实例
    plugin_manager = PluginManager(config)
    
    # 发现插件
    plugin_manager.discover_plugins()
    # 加载插件
    plugin_manager.load_plugins()
    # 启用插件（根据配置）
    plugin_manager.enable_plugins(plugin_config)
    
    enabled_count = len(plugin_manager.enabled_plugins)
    logger.info(_("Plugin system") + f": {_('loaded')} {enabled_count} {_('plugins')}")
    
    # 使用导出的配置常量
    target_url = config.get("target_url", TARGET_URL)
    max_depth = config.get("crawl", {}).get("max_depth", MAX_DEPTH)
    max_files = config.get("crawl", {}).get("max_files", MAX_FILES)
    output_dir = config.get("output", {}).get("full_path", OUTPUT_DIR)
    
    # 使用导出的延迟相关配置
    delay = config.get("crawl", {}).get("delay", DELAY)
    random_delay = config.get("crawl", {}).get("random_delay", RANDOM_DELAY)
    threads = config.get("crawl", {}).get("threads", THREADS)
    user_agent = config.get("crawl", {}).get("user_agent", USER_AGENT)
    
    logger.info(_("开始抓取网站..."))
    logger.info(f"{_('目标网站')}: {target_url}")
    logger.info(f"{_('最大深度')}: {max_depth}")
    logger.info(f"{_('最大文件数')}: {max_files}")
    logger.info(f"{_('请求间隔')}: {delay} {_('秒')}")
    logger.info(f"{_('随机延迟')}: {_('Enabled') if random_delay else _('Disabled')}")
    logger.info(f"{_('线程数')}: {threads}")
    logger.info(f"{_('用户代理:')}{user_agent[:50]}..." if len(user_agent) > 50 else f"{_('用户代理:')}{user_agent}")
    logger.info(f"{_('输出路径')}: {output_dir}")
    
    # 显示JavaScript渲染配置
    js_rendering_config = config.get("js_rendering", JS_RENDERING_CONFIG)
    js_rendering_timeout = js_rendering_config.get("timeout", 30)
    logger.info(f"{_('JavaScript渲染')}: {_('Enabled')}")
    
    # 显示语言配置
    logger.info(f"{_("当前语言")}: {current_lang}")
    
    # 创建抓取器实例（始终传递 plugin_manager，内部根据 enabled_plugins 判断）
    has_enabled_plugins = len(plugin_manager.enabled_plugins) > 0
    crawler = CrawlSite(target_url, max_depth, max_files, output_dir, threads=threads, plugin_manager=plugin_manager if has_enabled_plugins else None, force_download=args.force_download, stop_event=stop_event)
    
    # 调用插件的 on_crawl_start 钩子
    if has_enabled_plugins:
        plugin_manager.call_hook("on_crawl_start", crawler)
    
    # 抓取网站，获取暂存页面
    pages = crawler.crawl_site()
    
    # 调用插件的 on_crawl_end 钩子
    if has_enabled_plugins:
        plugin_manager.call_hook("on_crawl_end", pages)
    
    logger.info(_("Crawl completed") + f", {len(pages)} " + _("pages"))
    logger.debug(f"Pages type: {type(pages)}")
    
    # 初始化保存文件列表
    saved_files = []
    
    # 调用插件的 on_save_start 钩子
    if has_enabled_plugins:
        saver_data = {
            'target_url': target_url,
            'output_dir': output_dir,
            'static_resources': crawler.static_resources
        }
        plugin_manager.call_hook("on_save_start", saver_data)
        
        # 查找所有实现了 save_site 方法的插件
        save_plugins = []
        for plugin in plugin_manager.enabled_plugins:
            if hasattr(plugin, 'save_site') and callable(getattr(plugin, 'save_site')):
                save_plugins.append(plugin)
        
        if save_plugins:
            saved_files = []
            for save_plugin in save_plugins:
                logger.info(_("Using save plugin") + f": {save_plugin.name}")
                try:
                    # 使用保存插件保存页面
                    plugin_saved_files = save_plugin.save_site(pages)
                    saved_files.extend(plugin_saved_files)
                    logger.info(_("Save plugin") + f" {save_plugin.name} " + _("completed, saved") + f" {len(plugin_saved_files)} " + _("files"))
                except Exception as e:
                    logger.error(_("Save plugin") + f" {save_plugin.name} " + _("execution failed") + f": {e}")
            
            # 调用插件的 on_save_end 钩子
            plugin_manager.call_hook("on_save_end", saved_files)
            logger.info(_("All save plugins completed, total saved") + f" {len(saved_files)} " + _("files"))
        else:
            logger.warning(_("No save plugin found, no pages saved. Please ensure a plugin implementing save_site method is enabled"))
    else:
        logger.warning(_("Plugin system disabled, cannot save pages. Please enable plugin system to save crawled content"))
    
    # 生成站点地图（只有在页面被保存时才生成，因为站点地图链接指向本地文件）
    sitemap_config = config["output"].get("sitemap", CONFIG["output"]["sitemap"])
    sitemap_enable = sitemap_config.get("enable", False)
    sitemap_html_enable = sitemap_config.get("enable_html", False)
    
    # 检查是否有页面被保存（save_site 是否被执行且有文件保存）
    has_saved_files = len(saved_files) > 0
    
    if has_saved_files:
        if sitemap_enable:
            sitemap_generator = SitemapGenerator(target_url, output_dir)
            # 如果 pages 字典不为空，使用 pages（包含本地文件路径和页面内容），否则使用 visited_urls
            sitemap_data = pages if pages else crawler.visited_urls
            sitemap_generator.generate_sitemap(sitemap_data)
        
        # 生成 HTML 格式的站点地图
        if sitemap_html_enable:
            sitemap_generator = SitemapGenerator(target_url, output_dir)
            # 如果 pages 字典不为空，使用 pages（包含本地文件路径和页面内容），否则使用 visited_urls
            sitemap_data = pages if pages else crawler.visited_urls
            # 传递页面深度信息
            page_depths = crawler.page_depths if hasattr(crawler, 'page_depths') else None
            sitemap_generator.generate_html_sitemap(sitemap_data, page_depths)
    else:
        if sitemap_enable or sitemap_html_enable:
            logger.info(_("跳过生成站点地图") + f": {_('页面未保存')}")
    
    # 清理插件
    if has_enabled_plugins:
        plugin_manager.cleanup()
    
    logger.info(_("抓取完成！"))
    
    # 关闭日志，释放文件锁
    from logger import close_all_loggers
    close_all_loggers()


if __name__ == "__main__":
    main()
