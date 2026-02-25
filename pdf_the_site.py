#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDFtheSite 主脚本

网站抓取工具的 PDF 输出命令行入口。
"""

import sys
import argparse
from cli.base_cli import BaseCLI, main


def _(message: str) -> str:
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)


class PDFCLI(BaseCLI):
    """PDF CLI 类"""

    def __init__(self):
        """初始化 PDF CLI"""
        super().__init__(
            description="PDFtheSite - 网站抓取工具，输出PDF格式",
            prog="pdf_the_site"
        )

    def _add_specific_args(self, parser):
        """添加 PDF 特定参数"""
        parser.add_argument(
            "--pdf-filename",
            type=str,
            default="site.pdf",
            help=_("PDF 文件名")
        )

        parser.add_argument(
            "--pdf-format",
            type=str,
            default="A4",
            choices=["A4", "Letter", "Legal"],
            help=_("PDF 页面格式")
        )

        parser.add_argument(
            "--pdf-margin",
            type=int,
            default=20,
            help=_("PDF 页面边距（毫米）")
        )

    def _update_specific_config(self, config, args):
        """更新 PDF 特定配置"""
        if "pdf" not in config:
            config["pdf"] = {}

        if args.pdf_filename:
            config["pdf"]["output_filename"] = args.pdf_filename
        if args.pdf_format:
            config["pdf"]["format"] = args.pdf_format
        if args.pdf_margin:
            config["pdf"]["margin"] = args.pdf_margin

        # PDF 模式下禁用 JS 渲染
        if "js_rendering" not in config:
            config["js_rendering"] = {}
        config["js_rendering"]["enabled"] = False

    def _configure_plugins(self, plugin_manager, config):
        """配置插件"""
        # 启用 pdf_plugin，禁用 save_plugin
        plugin_config = {
            "pdf_plugin": True,
            "save_plugin": False
        }
        plugin_manager.enable_plugins(plugin_config)

    def _post_process(self, config, pages, plugin_manager, logger):
        """后续处理"""
        # PDF 生成由 pdf_plugin 处理
        return 0


def main_entry(args_list=None, stop_event=None):
    """主入口"""
    return main(PDFCLI, args_list, stop_event)


if __name__ == "__main__":
    sys.exit(main_entry())
