"""CLI 基类模块

提供 grab_the_site.py 和 pdf_the_site.py 的公共基类，消除重复代码。
"""

import os
import sys
import argparse
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from config import load_config, CONFIG, TARGET_URL, MAX_DEPTH, MAX_FILES, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, OUTPUT_DIR, I18N_CONFIG
from crawler.crawl_site import CrawlSite
from logger import setup_logger
from utils.i18n import init_i18n, get_current_lang
from utils.plugin_manager import PluginManager


logger = setup_logger(__name__)


def _(message: str) -> str:
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)


class BaseCLI(ABC):
    """CLI 基类

    提供 grab_the_site 和 pdf_the_site 的公共功能：
    - 参数解析
    - 配置加载和合并
    - 插件系统初始化
    - 抓取流程启动
    """

    def __init__(self, description: str, prog: str):
        """初始化 CLI

        Args:
            description: 程序描述
            prog: 程序名称
        """
        self.description = description
        self.prog = prog
        self.parser = self._create_parser()

        # 设置 CLI 模式的控制台日志级别
        self._setup_cli_logging()

    def _setup_cli_logging(self) -> None:
        """设置 CLI 模式的日志级别"""
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.ERROR)

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器

        Returns:
            argparse.ArgumentParser: 参数解析器
        """
        parser = argparse.ArgumentParser(
            description=self.description,
            prog=self.prog
        )

        # 添加通用参数
        self._add_common_args(parser)

        # 添加特定参数（子类实现）
        self._add_specific_args(parser)

        return parser

    def _add_common_args(self, parser: argparse.ArgumentParser) -> None:
        """添加通用参数

        Args:
            parser: 参数解析器
        """
        parser.add_argument(
            "--url", "-u",
            type=str,
            default=None,
            help=_("目标网站 URL")
        )

        parser.add_argument(
            "--depth", "-d",
            type=int,
            default=None,
            help=_("最大抓取深度")
        )

        parser.add_argument(
            "--max-files", "-m",
            type=int,
            default=None,
            help=_("最大文件数量")
        )

        parser.add_argument(
            "--output", "-o",
            type=str,
            default=None,
            help=_("输出目录")
        )

        parser.add_argument(
            "--delay", "-t",
            type=float,
            default=None,
            help=_("请求间隔（秒）")
        )

        parser.add_argument(
            "--no-random-delay",
            action="store_true",
            help=_("禁用随机延迟")
        )

        parser.add_argument(
            "--threads", "-p",
            type=int,
            default=None,
            help=_("线程数")
        )

        parser.add_argument(
            "--no-js",
            action="store_true",
            help=_("禁用 JavaScript 渲染")
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help=_("强制重新下载已存在的文件")
        )

        parser.add_argument(
            "--proxy",
            type=str,
            default=None,
            help=_("代理服务器地址，例如: http://127.0.0.1:7890")
        )

        parser.add_argument(
            "--exclude",
            action="append",
            default=None,
            help=_("排除的 URL 模式，可多次使用")
        )

        parser.add_argument(
            "--lang",
            type=str,
            default=None,
            choices=["zh_CN", "en"],
            help=_("界面语言 (zh_CN/en)")
        )

    @abstractmethod
    def _add_specific_args(self, parser: argparse.ArgumentParser) -> None:
        """添加特定参数（子类实现）

        Args:
            parser: 参数解析器
        """
        pass

    def parse_args(self, args_list: Optional[List[str]] = None) -> argparse.Namespace:
        """解析命令行参数

        Args:
            args_list: 命令行参数列表

        Returns:
            argparse.Namespace: 解析后的参数
        """
        return self.parser.parse_args(args_list)

    def update_config(self, args: argparse.Namespace) -> Dict[str, Any]:
        """更新配置

        Args:
            args: 解析后的参数

        Returns:
            Dict[str, Any]: 更新后的配置
        """
        config = load_config()

        # 语言设置
        if args.lang:
            if "i18n" not in config:
                config["i18n"] = {}
            config["i18n"]["lang"] = args.lang
            init_i18n(args.lang)

        # 基本配置
        if args.url:
            config["target_url"] = args.url
        if args.depth is not None:
            config["crawl"]["max_depth"] = args.depth
        if args.max_files is not None:
            config["crawl"]["max_files"] = args.max_files
        if args.output:
            config["output"]["base_dir"] = args.output
        if args.delay is not None:
            config["crawl"]["delay"] = args.delay
        if args.no_random_delay:
            config["crawl"]["random_delay"] = False
        if args.threads is not None:
            config["crawl"]["threads"] = args.threads
        if args.no_js:
            if "js_rendering" not in config:
                config["js_rendering"] = {}
            config["js_rendering"]["enabled"] = False
        if args.force:
            config["crawl"]["force_download"] = True
        if args.proxy:
            config["crawl"]["proxy"] = args.proxy
        if args.exclude:
            config["crawl"]["exclude_patterns"] = args.exclude

        # 子类特定的配置更新
        self._update_specific_config(config, args)

        return config

    @abstractmethod
    def _update_specific_config(self, config: Dict[str, Any], args: argparse.Namespace) -> None:
        """更新特定配置（子类实现）

        Args:
            config: 配置字典
            args: 解析后的参数
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置

        Args:
            config: 配置字典

        Returns:
            bool: 配置是否有效
        """
        if not config.get("target_url"):
            logger.error(_("错误: 必须提供目标 URL"))
            return False

        # 验证 URL 格式
        try:
            result = urlparse(config["target_url"])
            if not all([result.scheme, result.netloc]):
                logger.error(_("错误: 无效的 URL 格式"))
                return False
        except Exception:
            logger.error(_("错误: 无效的 URL"))
            return False

        return True

    def setup_plugin_manager(self, config: Dict[str, Any]) -> PluginManager:
        """设置插件管理器

        Args:
            config: 配置字典

        Returns:
            PluginManager: 插件管理器实例
        """
        plugin_manager = PluginManager(config)
        plugin_manager.discover_plugins()
        plugin_manager.load_plugins()

        # 子类特定的插件配置
        self._configure_plugins(plugin_manager, config)

        return plugin_manager

    @abstractmethod
    def _configure_plugins(self, plugin_manager: PluginManager, config: Dict[str, Any]) -> None:
        """配置插件（子类实现）

        Args:
            plugin_manager: 插件管理器
            config: 配置字典
        """
        pass

    def run(self, args_list: Optional[List[str]] = None, stop_event=None) -> int:
        """运行主逻辑

        Args:
            args_list: 命令行参数列表
            stop_event: 停止事件

        Returns:
            int: 退出码
        """
        # 解析参数
        args = self.parse_args(args_list)

        # 更新配置
        config = self.update_config(args)

        # 验证配置
        if not self.validate_config(config):
            return 1

        # 初始化语言
        lang = config.get("i18n", {}).get("lang", "zh_CN")
        init_i18n(lang)

        # 设置插件管理器
        plugin_manager = self.setup_plugin_manager(config)

        try:
            # 启动抓取
            crawler = CrawlSite(
                target_url=config["target_url"],
                max_depth=config["crawl"]["max_depth"],
                max_files=config["crawl"]["max_files"],
                output_dir=config["output"]["base_dir"],
                threads=config["crawl"]["threads"],
                plugin_manager=plugin_manager,
                force_download=config["crawl"].get("force_download", False),
                stop_event=stop_event
            )

            pages = crawler.crawl_site()

            # 子类特定的后续处理
            return self._post_process(config, pages)

        except Exception as e:
            logger.error(_("抓取失败: {}").format(e))
            return 1

        finally:
            plugin_manager.cleanup()

    @abstractmethod
    def _post_process(self, config: Dict[str, Any], pages: Dict[str, str]) -> int:
        """后续处理（子类实现）

        Args:
            config: 配置字典
            pages: 抓取的页面

        Returns:
            int: 退出码
        """
        pass


def main(cli_class: type, args_list: Optional[List[str]] = None, stop_event=None) -> int:
    """主入口函数

    Args:
        cli_class: CLI 类
        args_list: 命令行参数列表
        stop_event: 停止事件

    Returns:
        int: 退出码
    """
    cli = cli_class()
    return cli.run(args_list, stop_event)
