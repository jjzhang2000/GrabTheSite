"""统一入口点模块

提供项目的统一入口点：
- CLI 命令行入口
- GUI 图形界面入口
- PDF 生成器入口
"""

import sys
import argparse
from typing import Optional, List

from logger import setup_logger, _ as _t
from utils.i18n import init_i18n
from utils.config_manager import load_config

logger = setup_logger(__name__)


def init_application():
    """初始化应用程序

    加载配置、初始化国际化等。
    """
    # 加载配置
    config = load_config()

    # 初始化国际化
    lang = config.get('i18n', {}).get('lang', 'en')
    init_i18n(lang)

    return config


def cli_main(args: Optional[List[str]] = None) -> int:
    """CLI 命令行入口

    Args:
        args: 命令行参数

    Returns:
        int: 退出码
    """
    config = init_application()

    parser = argparse.ArgumentParser(
        prog='grabthesite',
        description=_t('GrabTheSite - 网站抓取工具')
    )

    parser.add_argument(
        'url',
        help=_t('目标 URL')
    )

    parser.add_argument(
        '-o', '--output',
        default=config.get('output', {}).get('base_dir'),
        help=_t('输出目录')
    )

    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=config.get('crawl', {}).get('max_depth', 1),
        help=_t('最大抓取深度')
    )

    parser.add_argument(
        '-m', '--max-files',
        type=int,
        default=config.get('crawl', {}).get('max_files', 10),
        help=_t('最大文件数')
    )

    parser.add_argument(
        '-t', '--threads',
        type=int,
        default=config.get('crawl', {}).get('threads', 4),
        help=_t('线程数')
    )

    parser.add_argument(
        '--no-js',
        action='store_true',
        help=_t('禁用 JavaScript 渲染')
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help=_t('强制重新下载')
    )

    parsed_args = parser.parse_args(args)

    logger.info(_t("启动 CLI 模式"))

    # 导入并运行抓取
    from crawler.crawl_site import CrawlSite
    from utils.plugin_manager import PluginManager

    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()
    plugin_manager.load_plugins()
    plugin_manager.enable_all_plugins()

    try:
        crawler = CrawlSite(
            target_url=parsed_args.url,
            max_depth=parsed_args.depth,
            max_files=parsed_args.max_files,
            output_dir=parsed_args.output,
            threads=parsed_args.threads,
            plugin_manager=plugin_manager,
            force_download=parsed_args.force
        )

        pages = crawler.crawl_site()

        logger.info(_t("抓取完成，共") + f" {len(pages)} " + _t("个页面"))

        return 0

    except Exception as e:
        logger.error(_t("抓取失败") + f": {e}")
        return 1

    finally:
        plugin_manager.cleanup()


def gui_main() -> int:
    """GUI 图形界面入口

    Returns:
        int: 退出码
    """
    config = init_application()

    logger.info(_t("启动 GUI 模式"))

    try:
        # 导入 GUI 模块
        from grab_gui import main as grab_gui_main
        return grab_gui_main()
    except ImportError:
        logger.error(_t("GUI 模块未安装"))
        return 1


def pdf_main() -> int:
    """PDF 生成器入口

    Returns:
        int: 退出码
    """
    config = init_application()

    logger.info(_t("启动 PDF 生成器"))

    try:
        # 导入 PDF GUI 模块
        from pdf_gui import main as pdf_gui_main
        return pdf_gui_main()
    except ImportError:
        logger.error(_t("PDF 模块未安装"))
        return 1


def main() -> int:
    """主入口点

    根据命令行参数决定启动模式。

    Returns:
        int: 退出码
    """
    # 检查是否有子命令
    if len(sys.argv) > 1 and sys.argv[1] in ['gui', 'pdf']:
        mode = sys.argv.pop(1)
        if mode == 'gui':
            return gui_main()
        elif mode == 'pdf':
            return pdf_main()

    # 默认 CLI 模式
    return cli_main()


if __name__ == '__main__':
    sys.exit(main())
