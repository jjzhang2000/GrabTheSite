#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDFtheSite CLI 入口

网站抓取工具的 PDF 输出命令行入口：
1. 解析命令行参数
2. 加载和合并配置
3. 初始化插件系统（启用 pdf_plugin，禁用 save_plugin）
4. 启动抓取流程
5. 生成 PDF 文件
"""

import os
import sys
import argparse
from urllib.parse import urlparse
from config import load_config, CONFIG, TARGET_URL, MAX_DEPTH, MAX_FILES, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, OUTPUT_DIR, I18N_CONFIG, JS_RENDERING_CONFIG
from crawler.crawl_site import CrawlSite
from logger import setup_logger
from utils.i18n import init_i18n, get_current_lang


def _(message):
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)


from utils.plugin_manager import PluginManager

logger = setup_logger(__name__)


def parse_args():
    """解析命令行参数

    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="PDFtheSite - 网站抓取工具，输出PDF格式"
    )

    # 基础参数（与 grab_the_site.py 相同）
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

    # 抓取相关参数
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="强制重新下载页面"
    )

    # 排除URL参数
    parser.add_argument(
        "--exclude-urls",
        type=str,
        nargs="*",
        default=None,
        help="不要下载的URL列表，支持通配符"
    )

    # PDF 特有参数
    parser.add_argument(
        "--pdf-filename",
        type=str,
        default=None,
        help="PDF输出文件名（默认：site.pdf）"
    )

    parser.add_argument(
        "--pdf-format",
        type=str,
        choices=["A4", "Letter", "Legal", "Tabloid"],
        default=None,
        help="PDF页面格式"
    )

    parser.add_argument(
        "--pdf-margin",
        type=int,
        default=None,
        help="PDF页边距（mm）"
    )

    parser.add_argument(
        "--no-bookmarks",
        action="store_true",
        help="不生成PDF书签"
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

    # JavaScript渲染配置
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

    # 排除URL配置
    if args.exclude_urls is not None:
        config["exclude_urls"] = args.exclude_urls

    # PDF 特有配置
    if "pdf" not in config:
        config["pdf"] = {}

    if args.pdf_filename:
        config["pdf"]["output_filename"] = args.pdf_filename

    if args.pdf_format:
        if "page" not in config["pdf"]:
            config["pdf"]["page"] = {}
        config["pdf"]["page"]["format"] = args.pdf_format

    if args.pdf_margin:
        if "page" not in config["pdf"]:
            config["pdf"]["page"] = {}
        config["pdf"]["page"]["margin"] = {
            "top": args.pdf_margin,
            "bottom": args.pdf_margin,
            "left": args.pdf_margin,
            "right": args.pdf_margin
        }

    if args.no_bookmarks:
        if "bookmarks" not in config["pdf"]:
            config["pdf"]["bookmarks"] = {}
        config["pdf"]["bookmarks"]["enabled"] = False

    # 计算完整输出路径
    if "output" in config and "base_dir" in config["output"] and "site_name" in config["output"]:
        config["output"]["full_path"] = os.path.join(
            config["output"]["base_dir"],
            config["output"]["site_name"]
        )

    return config


def init_pdf_plugin_only(plugin_manager, config):
    """只初始化 pdf_plugin，跳过 save_plugin

    Args:
        plugin_manager: 插件管理器实例
        config: 配置对象
    """
    # 发现插件
    plugin_manager.discover_plugins()

    # 只加载 pdf_plugin，跳过 save_plugin
    pdf_plugin_loaded = False

    for plugin_path in plugin_manager.plugin_paths:
        try:
            # 获取插件模块名
            plugin_name = os.path.basename(plugin_path)
            module_path = f'plugins.{plugin_name}'

            # 导入插件模块
            module = __import__(module_path, fromlist=['plugin'])

            # 查找Plugin子类
            import inspect
            from utils.plugin_manager import Plugin
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, Plugin) and cls != Plugin:
                    if cls.__name__ == "PdfPlugin":
                        try:
                            plugin = cls(config)
                            plugin_manager.plugins.append(plugin)
                            plugin_manager.enabled_plugins.append(plugin)
                            logger.info(_("已启用PDF插件") + f": {plugin.name}")
                            pdf_plugin_loaded = True
                        except Exception as e:
                            logger.error(_("加载PDF插件失败") + f": {e}")
                    elif cls.__name__ == "SavePlugin":
                        logger.debug(_("跳过HTML保存插件"))
                        continue
                    else:
                        # 其他插件正常加载
                        try:
                            plugin = cls(config)
                            plugin_manager.plugins.append(plugin)
                            plugin_manager.enabled_plugins.append(plugin)
                            logger.debug(_("已加载插件") + f": {plugin.name}")
                        except Exception as e:
                            logger.warning(_("加载插件失败") + f": {plugin_name}, {e}")
        except Exception as e:
            logger.warning(_("加载插件失败") + f": {plugin_path}, {e}")

    if not pdf_plugin_loaded:
        logger.error(_("未能加载PDF插件，请确保 pdf_plugin 已正确安装"))

    return pdf_plugin_loaded


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
        sys.argv = ['pdf_the_site.py'] + args_list
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

    # 初始化插件系统 - 关键区别：只启用 pdf_plugin，禁用 save_plugin
    plugin_manager = PluginManager(config)
    pdf_plugin_loaded = init_pdf_plugin_only(plugin_manager, config)

    if not pdf_plugin_loaded:
        logger.error(_("PDF插件未加载，程序退出"))
        return

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

    # 获取PDF配置
    pdf_config = config.get("pdf", {})
    pdf_filename = pdf_config.get("output_filename", "site.pdf")

    logger.info(_("开始抓取网站并生成PDF..."))
    logger.info(f"{_('目标网站')}: {target_url}")
    logger.info(f"{_('最大深度')}: {max_depth}")
    logger.info(f"{_('最大文件数')}: {max_files}")
    logger.info(f"{_('请求间隔')}: {delay} {_('秒')}")
    logger.info(f"{_('随机延迟')}: {_('Enabled') if random_delay else _('Disabled')}")
    logger.info(f"{_('线程数')}: {threads}")
    logger.info(f"{_('用户代理:')}{user_agent[:50]}..." if len(user_agent) > 50 else f"{_('用户代理:')}{user_agent}")
    logger.info(f"{_('输出路径')}: {output_dir}")
    logger.info(f"{_('PDF文件名')}: {pdf_filename}")

    # 显示JavaScript渲染配置
    js_rendering_config = config.get("js_rendering", JS_RENDERING_CONFIG)
    js_rendering_timeout = js_rendering_config.get("timeout", 30)

    # 禁用JavaScript渲染以避免Playwright多线程问题
    # 在PDF生成模式下，我们使用直接HTTP请求获取页面内容
    import config as config_module
    config_module.JS_RENDERING_CONFIG['enabled'] = False
    logger.info(f"{_('JavaScript渲染')}: {_('Disabled')} (PDF生成使用直接HTTP请求)")

    # 显示语言配置
    logger.info(f"{_('当前语言')}: {current_lang}")

    # 创建抓取器实例
    has_enabled_plugins = len(plugin_manager.enabled_plugins) > 0
    crawler = CrawlSite(
        target_url,
        max_depth,
        max_files,
        output_dir,
        threads=threads,
        plugin_manager=plugin_manager if has_enabled_plugins else None,
        force_download=args.force_download,
        stop_event=stop_event
    )

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
            'static_resources': crawler.static_resources,
            'page_depths': crawler.page_depths if hasattr(crawler, 'page_depths') else {}
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

    # PDF 输出不需要生成 HTML 站点地图
    # 但可以在 PDF 中保留目录结构

    # 清理插件
    if has_enabled_plugins:
        plugin_manager.cleanup()

    logger.info(_("PDF生成完成！"))

    # 关闭日志，释放文件锁
    from logger import close_all_loggers
    close_all_loggers()


if __name__ == "__main__":
    main()
