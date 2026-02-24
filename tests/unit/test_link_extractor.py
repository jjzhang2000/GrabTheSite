"""链接提取器模块单元测试"""

import pytest
from crawler.link_extractor import LinkExtractor


class TestLinkExtractorInit:
    """测试 LinkExtractor 初始化"""

    def test_init(self):
        """测试初始化"""
        extractor = LinkExtractor()
        assert extractor is not None


class TestExtractLinks:
    """测试链接提取"""

    def test_extract_page_links(self):
        """测试提取页面链接"""
        html = '''
        <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://example.com/page3">Page 3</a>
        </body>
        </html>
        '''
        extractor = LinkExtractor()
        page_links, static_resources = extractor.extract_links(html, "https://example.com/")

        assert len(page_links) == 3
        assert "https://example.com/page1" in page_links
        assert "https://example.com/page2" in page_links
        assert "https://example.com/page3" in page_links

    def test_extract_static_resources(self):
        """测试提取静态资源"""
        html = '''
        <html>
        <head>
            <link rel="stylesheet" href="/style.css">
        </head>
        <body>
            <img src="/image.png">
            <script src="/script.js"></script>
        </body>
        </html>
        '''
        extractor = LinkExtractor()
        page_links, static_resources = extractor.extract_links(html, "https://example.com/")

        assert len(static_resources) == 3
        assert "https://example.com/style.css" in static_resources
        assert "https://example.com/image.png" in static_resources
        assert "https://example.com/script.js" in static_resources

    def test_extract_relative_links(self):
        """测试提取相对链接"""
        html = '''
        <html>
        <body>
            <a href="page1">Page 1</a>
            <a href="../page2">Page 2</a>
        </body>
        </html>
        '''
        extractor = LinkExtractor()
        page_links, _ = extractor.extract_links(html, "https://example.com/docs/")

        assert "https://example.com/docs/page1" in page_links
        assert "https://example.com/page2" in page_links

    def test_extract_no_links(self):
        """测试没有链接的情况"""
        html = '<html><body><p>No links here</p></body></html>'
        extractor = LinkExtractor()
        page_links, static_resources = extractor.extract_links(html, "https://example.com/")

        assert len(page_links) == 0
        assert len(static_resources) == 0


class TestExtractPageLinks:
    """测试仅提取页面链接"""

    def test_extract_only_page_links(self):
        """测试仅提取页面链接"""
        html = '''
        <html>
        <body>
            <a href="/page1">Page 1</a>
            <img src="/image.png">
            <a href="/page2">Page 2</a>
        </body>
        </html>
        '''
        extractor = LinkExtractor()
        links = extractor.extract_page_links(html, "https://example.com/")

        assert len(links) == 2
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links


class TestExtractStaticResources:
    """测试仅提取静态资源"""

    def test_extract_only_static_resources(self):
        """测试仅提取静态资源"""
        html = '''
        <html>
        <head>
            <link rel="stylesheet" href="/style.css">
        </head>
        <body>
            <a href="/page1">Page 1</a>
            <img src="/image.png">
            <script src="/script.js"></script>
        </body>
        </html>
        '''
        extractor = LinkExtractor()
        resources = extractor.extract_static_resources(html, "https://example.com/")

        assert len(resources) == 3
        assert "https://example.com/style.css" in resources
        assert "https://example.com/image.png" in resources
        assert "https://example.com/script.js" in resources

    def test_extract_css_only(self):
        """测试仅提取 CSS"""
        html = '''
        <html>
        <head>
            <link rel="stylesheet" href="/style.css">
            <link rel="icon" href="/favicon.ico">
        </head>
        </html>
        '''
        extractor = LinkExtractor()
        resources = extractor.extract_static_resources(html, "https://example.com/")

        # 应该只提取 stylesheet
        assert "https://example.com/style.css" in resources
        # favicon 不应该被提取（rel 不是 stylesheet）
        assert "https://example.com/favicon.ico" not in resources
