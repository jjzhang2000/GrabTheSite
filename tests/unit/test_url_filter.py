"""URL 过滤器模块单元测试"""

import pytest
from crawler.url_filter import URLFilter


class TestURLFilterInit:
    """测试 URLFilter 初始化"""

    def test_init_basic(self):
        """测试基本初始化"""
        filter = URLFilter("https://example.com/path/")
        assert filter.target_url == "https://example.com/path/"
        assert filter.target_domain == "example.com"
        assert filter.target_directory == "/path/"

    def test_init_without_trailing_slash(self):
        """测试不带斜杠的目标 URL"""
        filter = URLFilter("https://example.com/path")
        assert filter.target_directory == "/path/"

    def test_init_with_exclude_patterns(self):
        """测试带排除模式的初始化"""
        excludes = ["*/admin/*", "*.php*"]
        filter = URLFilter("https://example.com/", excludes)
        assert filter.exclude_patterns == excludes


class TestIsSameDomain:
    """测试同域名检查"""

    def test_same_domain(self):
        """测试同域名"""
        filter = URLFilter("https://example.com/")
        assert filter.is_same_domain("https://example.com/page") is True

    def test_different_domain(self):
        """测试不同域名"""
        filter = URLFilter("https://example.com/")
        assert filter.is_same_domain("https://other.com/page") is False

    def test_subdomain(self):
        """测试子域名"""
        filter = URLFilter("https://example.com/")
        assert filter.is_same_domain("https://www.example.com/page") is False


class TestIsInTargetDirectory:
    """测试目标目录检查"""

    def test_in_target_directory(self):
        """测试在目标目录中"""
        filter = URLFilter("https://example.com/docs/")
        assert filter.is_in_target_directory("https://example.com/docs/page") is True

    def test_in_subdirectory(self):
        """测试在子目录中"""
        filter = URLFilter("https://example.com/docs/")
        assert filter.is_in_target_directory("https://example.com/docs/guide/page") is True

    def test_outside_target_directory(self):
        """测试在目标目录外"""
        filter = URLFilter("https://example.com/docs/")
        assert filter.is_in_target_directory("https://example.com/blog/page") is False

    def test_root_directory(self):
        """测试根目录"""
        filter = URLFilter("https://example.com/")
        assert filter.is_in_target_directory("https://example.com/page") is True


class TestIsExcluded:
    """测试排除列表检查"""

    def test_excluded_by_wildcard(self):
        """测试通配符排除"""
        filter = URLFilter("https://example.com/", ["*.php*"])
        assert filter.is_excluded("https://example.com/page.php") is True

    def test_excluded_by_path_wildcard(self):
        """测试路径通配符排除"""
        filter = URLFilter("https://example.com/", ["*/admin/*"])
        assert filter.is_excluded("https://example.com/admin/page") is True

    def test_excluded_by_prefix(self):
        """测试前缀排除"""
        filter = URLFilter("https://example.com/", ["https://example.com/private/"])
        assert filter.is_excluded("https://example.com/private/page") is True

    def test_not_excluded(self):
        """测试未被排除"""
        filter = URLFilter("https://example.com/", ["*/admin/*"])
        assert filter.is_excluded("https://example.com/page") is False

    def test_empty_exclude_list(self):
        """测试空排除列表"""
        filter = URLFilter("https://example.com/")
        assert filter.is_excluded("https://example.com/page") is False


class TestShouldCrawl:
    """测试是否应该抓取"""

    def test_should_crawl_valid(self):
        """测试应该抓取的 URL"""
        filter = URLFilter("https://example.com/docs/")
        assert filter.should_crawl("https://example.com/docs/page") is True

    def test_should_not_crawl_different_domain(self):
        """测试不同域名不应该抓取"""
        filter = URLFilter("https://example.com/")
        assert filter.should_crawl("https://other.com/page") is False

    def test_should_not_crawl_outside_directory(self):
        """测试目录外不应该抓取"""
        filter = URLFilter("https://example.com/docs/")
        assert filter.should_crawl("https://example.com/blog/page") is False

    def test_should_not_crawl_excluded(self):
        """测试排除的不应该抓取"""
        filter = URLFilter("https://example.com/", ["*/admin/*"])
        assert filter.should_crawl("https://example.com/admin/page") is False
