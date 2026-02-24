"""PDF 生成器

使用 Playwright 将 HTML 渲染为 PDF 文件。
现在使用 BrowserManager 实现浏览器复用。
"""

import os
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, Any, Set

from utils.browser_manager import get_browser_manager
from logger import setup_logger, _ as _t

logger = setup_logger(__name__)


class PdfGenerator:
    """PDF 生成器，使用 Playwright 将 HTML 渲染为 PDF"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 PDF 生成器

        Args:
            config: PDF 配置字典
        """
        self.config = config or {}
        self.page_config = self.config.get('page', {})
        self.header_config = self.config.get('header', {})
        self.footer_config = self.config.get('footer', {})

    def _process_html_images(self, html_content: str, base_url: str) -> str:
        """处理 HTML 中的图片链接，将相对路径转换为绝对路径

        Args:
            html_content: HTML 内容
            base_url: 基础 URL

        Returns:
            str: 处理后的 HTML
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')

        # 处理图片标签
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # 将相对路径转换为绝对路径
                absolute_url = urljoin(base_url, src)
                img['src'] = absolute_url

        # 处理 CSS 中的背景图片（内联样式）
        for tag in soup.find_all(style=True):
            style = tag['style']
            # 简单的背景图片 URL 替换
            if 'url(' in style:
                import re
                def replace_url(match):
                    url = match.group(1).strip('"\'')
                    if not url.startswith(('http://', 'https://', 'data:')):
                        return f'url("{urljoin(base_url, url)}")'
                    return match.group(0)
                style = re.sub(r'url\(([^)]+)\)', replace_url, style)
                tag['style'] = style

        # 处理链接标签（CSS 文件）
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                link['href'] = urljoin(base_url, href)

        return str(soup)

    def _process_html_links(self, html_content: str, base_url: str, downloaded_urls: Optional[Set[str]] = None) -> str:
        """处理 HTML 中的链接

        将已下载的内部链接的 href 设为空串（通过书签导航）。
        未下载的本站链接和外部链接保留，可在 PDF 中点击。

        Args:
            html_content: HTML 内容
            base_url: 基础 URL
            downloaded_urls: 已下载页面的 URL 集合

        Returns:
            str: 处理后的 HTML
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')
        parsed_base = urlparse(base_url)
        downloaded_urls = downloaded_urls or set()

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # 跳过锚点链接和空链接
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue

            # 转换为绝对 URL
            full_url = urljoin(base_url, href)
            parsed_link = urlparse(full_url)

            # 检查是否为已下载的内部链接
            # 只有已下载的页面才视为内部链接（通过书签导航）
            # 未下载的本站链接视为外部链接（可点击跳转）
            is_downloaded_internal = full_url in downloaded_urls

            if is_downloaded_internal:
                # 已下载的内部链接：将 href 设为空串，使其不可点击
                # 通过书签导航到对应页面
                link['href'] = ''
            else:
                # 其他链接（未下载的本站链接、外部链接）：转换为绝对 URL，确保可点击
                link['href'] = full_url

        return str(soup)

    def _extract_title_from_html(self, html_content: str) -> str:
        """从 HTML 中提取标题

        Args:
            html_content: HTML 内容

        Returns:
            str: 页面标题
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag and title_tag.text.strip():
            return title_tag.text.strip()
        return ""

    def generate_pdf(self, html_content: str, output_path: str, source_url: Optional[str] = None, downloaded_urls: Optional[Set[str]] = None) -> None:
        """将 HTML 内容渲染为 PDF

        Args:
            html_content: HTML 内容字符串
            output_path: 输出 PDF 文件路径
            source_url: 源 URL（用于日志记录）
            downloaded_urls: 已下载页面的 URL 集合（用于区分内部和外部链接）

        Raises:
            Exception: 当 PDF 生成失败时抛出
        """
        # 获取浏览器管理器
        browser_manager = get_browser_manager()

        if not browser_manager.initialize():
            raise Exception(
                "无法启动浏览器。请安装 Playwright 浏览器: playwright install chromium，"
                "或确保系统已安装 Edge/Chrome 浏览器。"
            )

        # 获取页面（复用浏览器实例）
        page_id = f"pdf_{id(self)}"
        page = browser_manager.get_page(page_id)

        if page is None:
            raise Exception("无法创建页面")

        try:
            # 处理 HTML 中的图片链接和内部链接
            if source_url:
                html_content = self._process_html_images(html_content, source_url)
                html_content = self._process_html_links(html_content, source_url, downloaded_urls)

            # 加载 HTML 内容
            page.set_content(html_content)

            # 等待页面加载完成
            page.wait_for_load_state('networkidle')

            # 额外等待图片加载
            page.wait_for_function("""
                () => {
                    const images = document.querySelectorAll('img');
                    if (images.length === 0) return true;
                    return Array.from(images).every(img => img.complete);
                }
            """, timeout=10000)

            # 再等待一小段时间确保渲染完成
            page.wait_for_timeout(500)

            # 获取页面配置
            format_option = self.page_config.get('format', 'A4')
            margin_config = self.page_config.get('margin', {})

            # 提取页面标题和 URL 用于页眉
            page_title = self._extract_title_from_html(html_content)
            if not page_title and source_url:
                page_title = source_url
            page_url = source_url if source_url else ""

            # 获取边距配置
            margin_left = margin_config.get('left', 20)
            margin_right = margin_config.get('right', 20)

            # 生成 PDF
            # Playwright 会自动保留外部链接，内部链接已被移除
            page.pdf(
                path=output_path,
                format=format_option,
                margin={
                    'top': f"{margin_config.get('top', 20)}mm",
                    'bottom': f"{margin_config.get('bottom', 20)}mm",
                    'left': f"{margin_left}mm",
                    'right': f"{margin_right}mm"
                },
                display_header_footer=self.header_config.get('enabled', True),
                header_template=self._build_header_template(page_title, page_url, margin_left, margin_right),
                footer_template=self._build_footer_template(),
                print_background=True
            )

            logger.info(_t("PDF 生成成功") + f": {output_path}")

        finally:
            # 释放页面（但不关闭浏览器）
            browser_manager.release_page(page_id)

    def _build_header_template(self, page_title: str = "", page_url: str = "", margin_left: int = 20, margin_right: int = 20) -> str:
        """构建页眉模板

        页眉布局：左侧显示页面标题，右侧显示页面网址
        使用页面配置的左右边距

        Args:
            page_title: 页面标题
            page_url: 页面 URL
            margin_left: 左边距（mm）
            margin_right: 右边距（mm）

        Returns:
            str: HTML 格式的页眉模板
        """
        if not self.header_config.get('enabled', True):
            return ''

        # 对标题和 URL 进行 HTML 转义，防止 XSS
        import html
        page_title = html.escape(page_title) if page_title else ""
        page_url = html.escape(page_url) if page_url else ""

        # 构建左右对齐的页眉布局
        # 左侧：页面标题，右侧：页面网址
        # 使用页面配置的左右边距
        return f'''<div style="font-size: 9px; width: 100%; color: #666; margin: 0; padding-left: {margin_left}mm; padding-right: {margin_right}mm; box-sizing: border-box;">
            <div style="float: left; text-align: left;">{page_title}</div>
            <div style="float: right; text-align: right;">{page_url}</div>
            <div style="clear: both;"></div>
        </div>'''

    def _build_footer_template(self) -> str:
        """构建页脚模板

        Returns:
            str: HTML 格式的页脚模板
        """
        if not self.footer_config.get('enabled', True):
            return ''

        template = self.footer_config.get('template', 'Page {page} of {total}')
        # Playwright 使用特殊类名来插入页码
        # <span class="pageNumber"></span> - 当前页码
        # <span class="totalPages"></span> - 总页数
        template = template.replace('{page}', '<span class="pageNumber"></span>')
        template = template.replace('{total}', '<span class="totalPages"></span>')

        return f'<div style="font-size: 9px; width: 100%; text-align: center; color: #666;">{template}</div>'
