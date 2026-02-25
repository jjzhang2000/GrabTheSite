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

_t = _


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
        # 只启用 Save 插件，禁用 PDF 插件
        plugin_config = {
            "save_plugin": True,
            "pdf_plugin": False
        }
        plugin_manager.enable_plugins(plugin_config)

    def _post_process(self, config, pages, plugin_manager, logger):
        """后续处理"""
        saved_files = []
        
        # 调用保存插件保存页面
        if pages:
            # 准备保存器数据
            saver_data = {
                'target_url': config['target_url'],
                'output_dir': config['output']['base_dir'],
                'static_resources': set(),
            }
            
            # 调用 on_save_start 钩子
            plugin_manager.call_hook("on_save_start", saver_data)
            
            # 查找所有实现了 save_site 方法的插件
            for plugin in plugin_manager.enabled_plugins:
                if hasattr(plugin, 'save_site') and callable(getattr(plugin, 'save_site')):
                    try:
                        plugin_saved_files = plugin.save_site(pages)
                        if plugin_saved_files:
                            saved_files.extend(plugin_saved_files)
                            logger.info(_t("插件") + f" {plugin.name} " + _t("保存了") + f" {len(plugin_saved_files)} " + _t("个页面"))
                    except Exception as e:
                        logger.error(_t("插件") + f" {plugin.name} " + _t("保存失败") + f": {e}")
            
            # 调用 on_save_end 钩子
            plugin_manager.call_hook("on_save_end", saved_files)
            
            # 生成站点地图
            sitemap_generator = SitemapGenerator(
                config["target_url"],
                config["output"]["base_dir"]
            )
            sitemap_generator.generate_html_sitemap(pages)

        return 0


def main_entry(args_list=None, stop_event=None):
    """主入口"""
    return main(CrawlCLI, args_list, stop_event)


if __name__ == "__main__":
    sys.exit(main_entry())
