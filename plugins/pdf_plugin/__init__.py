"""PDF 插件

核心插件，负责将抓取的页面保存为 PDF 文件：
- 处理页面链接转换
- 生成单页 PDF 文件
- 构建书签/目录结构
- 合并 PDF 并添加书签
- 保留页面内链接跳转
"""

import os
import shutil
import tempfile
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from utils.plugin_manager import Plugin
from logger import _ as _t


class PdfPlugin(Plugin):
    """PDF 保存插件

    负责将抓取的网站保存为 PDF 文件，保留目录结构和页面链接。
    参考 save_plugin.SavePlugin 的实现方式。
    """

    # 插件名称
    name = "PDF Plugin"

    # 插件描述
    description = "将抓取的网站保存为 PDF 文件，保留目录结构和页面链接"

    def __init__(self, config=None):
        """初始化插件

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.target_url = None
        self.output_dir = None
        self.output_pdf_path = None
        self.pdf_config = config.get('pdf', {}) if config else {}

        # 页面数据
        self.pages = {}
        self.page_depths = {}
        self.saved_files = []

        # 工具类实例（延迟初始化）
        self.bookmark_builder = None
        self.link_processor = None
        self.pdf_generator = None
        self.pdf_merger = None

        # URL 到页码的映射（用于内部链接跳转）
        self.url_to_page_map = {}

        # 临时文件目录
        self.temp_dir = None

    def on_init(self):
        """插件初始化时调用"""
        super().on_init()
        self.logger.info(_t("PDF插件初始化完成"))

    def on_crawl_end(self, pages):
        """抓取结束时调用，准备保存参数

        Args:
            pages: 抓取的页面字典
        """
        self.logger.info(_t("准备生成PDF，共") + f" {len(pages)} " + _t("个页面"))
        self.pages = pages

    def on_save_start(self, saver_data):
        """保存开始时调用

        参考 save_plugin.on_save_start 的实现

        Args:
            saver_data: 保存器数据，包含target_url、output_dir等
        """
        self.target_url = saver_data.get('target_url')
        self.output_dir = saver_data.get('output_dir')

        # 获取页面深度信息
        self.page_depths = saver_data.get('page_depths', {})

        if self.target_url and self.output_dir:
            # 提取起始目录路径
            parsed_target = urlparse(self.target_url)
            self.target_directory = parsed_target.path
            if not self.target_directory.endswith('/'):
                self.target_directory += '/'

            # 设置输出路径
            output_filename = self.pdf_config.get('output_filename', 'site.pdf')
            self.output_pdf_path = os.path.join(self.output_dir, output_filename)

            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix='pdf_plugin_')

            self.logger.info(_t("PDF插件准备就绪，输出路径") + f": {self.output_pdf_path}")
        else:
            self.logger.error(_t("PDF插件初始化失败：缺少必要参数"))

    def save_site(self, pages):
        """保存抓取的页面为 PDF

        参考 save_plugin.save_site 的实现方式

        Args:
            pages: 暂存的页面内容，键为URL，值为页面内容

        Returns:
            list: 保存的文件列表
        """
        if not pages:
            self.logger.warning(_t("没有页面需要保存"))
            return []

        self.logger.info(_t("开始生成PDF，共") + f" {len(pages)} " + _t("个页面"))

        try:
            # 延迟初始化工具类
            self._init_tools()

            # 1. 分析页面结构，构建书签树
            bookmark_tree = self.bookmark_builder.build_bookmarks(pages, self.page_depths)
            self.logger.info(_t("书签树构建完成"))

            # 2. 为每个页面生成单个 PDF（临时文件）
            temp_pdf_files = []
            page_count = 0

            for url, html_content in pages.items():
                try:
                    # 处理页面内链接
                    processed_html = self.link_processor.process_links(
                        html_content, url, pages.keys()
                    )

                    # 生成临时 PDF 文件
                    temp_pdf_path = os.path.join(
                        self.temp_dir,
                        f"page_{page_count:04d}.pdf"
                    )

                    self.pdf_generator.generate_pdf(processed_html, temp_pdf_path, url)
                    temp_pdf_files.append((url, temp_pdf_path))

                    # 记录 URL 到页码的映射
                    self.url_to_page_map[url] = page_count + 1  # PDF 页码从 1 开始

                    page_count += 1
                    self.logger.info(_t("生成页面PDF") + f": {url} ({page_count}/{len(pages)})")

                except Exception as e:
                    self.logger.error(_t("生成页面PDF失败") + f": {url}, " + _t("错误") + f": {str(e)}")

            # 3. 合并所有 PDF 并添加书签
            if temp_pdf_files:
                try:
                    self.pdf_merger.merge_pdfs(
                        temp_pdf_files,
                        self.output_pdf_path,
                        bookmark_tree,
                        self.url_to_page_map
                    )
                    self.saved_files.append((self.target_url, self.output_pdf_path))
                    self.logger.info(_t("PDF生成完成") + f": {self.output_pdf_path}")

                except Exception as e:
                    self.logger.error(_t("合并PDF失败") + f": {str(e)}")

            return self.saved_files

        except Exception as e:
            self.logger.error(_t("生成PDF过程中发生错误") + f": {str(e)}")
            return []

        finally:
            # 清理临时文件
            self._cleanup_temp_files()

    def _init_tools(self):
        """延迟初始化工具类"""
        from .pdf_generator import PdfGenerator
        from .bookmark_builder import BookmarkBuilder
        from .link_processor import LinkProcessor
        from .pdf_merger import PdfMerger

        self.bookmark_builder = BookmarkBuilder(self.target_url, self.output_dir)
        self.link_processor = LinkProcessor()
        self.pdf_generator = PdfGenerator(self.pdf_config)
        self.pdf_merger = PdfMerger()

    def _cleanup_temp_files(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.debug(_t("清理临时文件完成"))
            except Exception as e:
                self.logger.warning(_t("清理临时文件失败") + f": {str(e)}")

    def on_save_end(self, saved_files):
        """保存结束时调用

        Args:
            saved_files: 保存的文件列表
        """
        self.logger.info(_t("PDF插件工作完成") + f", {_('共生成')} {len(saved_files)} {_('个文件')}")


# 创建插件实例
plugin = PdfPlugin()
