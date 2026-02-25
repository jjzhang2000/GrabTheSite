#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""GrabTheSite 主脚本

网站抓取工具的命令行入口。
"""

import sys
from cli.base_cli import BaseCLI, main
from utils.sitemap_generator import SitemapGenerator


def _(message: str) -> str:
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)


class CrawlCLI(BaseCLI):
    """抓取 CLI 类"""

    def __init__(self):
        """初始化抓取 CLI"""
        super().__init__(
            description="GrabTheSite - 网站抓取工具，支持离线浏览",
            prog="grab_the_site"
        )

    def _add_specific_args(self, parser):
        """添加特定参数"""
        # 抓取模式没有特定参数
        pass

    def _update_specific_config(self, config, args):
        """更新特定配置"""
        # 抓取模式没有特定配置
        pass

    def _configure_plugins(self, plugin_manager, config):
        """配置插件"""
        # 启用所有插件
        plugin_manager.enable_all_plugins()

    def _post_process(self, config, pages):
        """后续处理"""
        # 生成站点地图
        if pages:
            sitemap_generator = SitemapGenerator(
                config["target_url"],
                config["output"]["base_dir"]
            )
            sitemap_generator.generate(pages)

        return 0


def main_entry(args_list=None, stop_event=None):
    """主入口"""
    return main(CrawlCLI, args_list, stop_event)


if __name__ == "__main__":
    sys.exit(main_entry())
