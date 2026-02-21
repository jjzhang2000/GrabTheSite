"""PDF 生成器

使用 Playwright 将 HTML 渲染为 PDF 文件。
"""

import os
from playwright.sync_api import sync_playwright


class PdfGenerator:
    """PDF 生成器，使用 Playwright 将 HTML 渲染为 PDF"""

    def __init__(self, config=None):
        """初始化 PDF 生成器

        Args:
            config: PDF 配置字典
        """
        self.config = config or {}
        self.page_config = self.config.get('page', {})
        self.header_config = self.config.get('header', {})
        self.footer_config = self.config.get('footer', {})

    def _find_system_browser(self):
        """查找系统安装的浏览器

        Returns:
            str: 浏览器可执行文件路径，如果未找到返回 None
        """
        # 可能的浏览器路径
        possible_paths = [
            # Microsoft Edge
            os.path.expandvars(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            # Google Chrome
            os.path.expandvars(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            # Chromium
            os.path.expandvars(r"C:\Program Files\Chromium\Application\chrome.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def generate_pdf(self, html_content, output_path, source_url=None):
        """将 HTML 内容渲染为 PDF

        Args:
            html_content: HTML 内容字符串
            output_path: 输出 PDF 文件路径
            source_url: 源 URL（用于日志记录）

        Raises:
            Exception: 当 PDF 生成失败时抛出
        """
        with sync_playwright() as p:
            # 尝试查找系统浏览器
            browser_path = self._find_system_browser()

            if browser_path:
                # 使用系统浏览器
                browser = p.chromium.launch(executable_path=browser_path)
            else:
                # 尝试使用 Playwright 内置浏览器
                try:
                    browser = p.chromium.launch()
                except Exception as e:
                    raise Exception(
                        "无法启动浏览器。请安装 Playwright 浏览器: playwright install chromium，"
                        "或确保系统已安装 Edge/Chrome 浏览器。"
                    ) from e

            page = browser.new_page()

            try:
                # 加载 HTML 内容
                page.set_content(html_content)

                # 等待资源加载完成
                page.wait_for_load_state('networkidle')

                # 获取页面配置
                format_option = self.page_config.get('format', 'A4')
                margin_config = self.page_config.get('margin', {})

                # 生成 PDF
                page.pdf(
                    path=output_path,
                    format=format_option,
                    margin={
                        'top': f"{margin_config.get('top', 20)}mm",
                        'bottom': f"{margin_config.get('bottom', 20)}mm",
                        'left': f"{margin_config.get('left', 20)}mm",
                        'right': f"{margin_config.get('right', 20)}mm"
                    },
                    display_header_footer=self.header_config.get('enabled', True),
                    header_template=self._build_header_template(),
                    footer_template=self._build_footer_template(),
                    print_background=True
                )

            finally:
                browser.close()

    def _build_header_template(self):
        """构建页眉模板

        Returns:
            str: HTML 格式的页眉模板
        """
        if not self.header_config.get('enabled', True):
            return ''

        template = self.header_config.get('template', '{title}')
        # 替换模板变量
        # 注意：Playwright 的页眉/页脚模板支持的变量有限
        # 这里使用简单的 HTML 样式
        return f'<div style="font-size: 9px; width: 100%; text-align: center; color: #666;">{template}</div>'

    def _build_footer_template(self):
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
