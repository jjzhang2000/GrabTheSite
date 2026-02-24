"""URL 工具模块单元测试"""

import pytest
from utils.url_utils import normalize_url, get_domain, get_path, is_same_domain, join_url


class TestNormalizeUrl:
    """测试 normalize_url 函数"""

    def test_normalize_url_basic(self):
        """测试基本 URL 规范化"""
        url = "https://example.com/path"
        result = normalize_url(url)
        assert result == "https://example.com/path"

    def test_normalize_url_with_fragment(self):
        """测试移除 URL 片段"""
        url = "https://example.com/path#section"
        result = normalize_url(url)
        assert result == "https://example.com/path"
        assert "#" not in result

    def test_normalize_url_with_query(self):
        """测试保留查询参数"""
        url = "https://example.com/path?key=value"
        result = normalize_url(url)
        assert result == "https://example.com/path?key=value"

    def test_normalize_url_lowercase_domain(self):
        """测试域名小写化"""
        url = "HTTPS://EXAMPLE.COM/PATH"
        result = normalize_url(url)
        assert result == "https://example.com/PATH"

    def test_normalize_url_complex(self):
        """测试复杂 URL"""
        url = "HTTPS://EXAMPLE.COM:443/PATH?key=value#section"
        result = normalize_url(url)
        assert result == "https://example.com:443/PATH?key=value"


class TestGetDomain:
    """测试 get_domain 函数"""

    def test_get_domain_basic(self):
        """测试基本域名提取"""
        url = "https://example.com/path"
        result = get_domain(url)
        assert result == "example.com"

    def test_get_domain_with_www(self):
        """测试带 www 的域名"""
        url = "https://www.example.com/path"
        result = get_domain(url)
        assert result == "www.example.com"

    def test_get_domain_lowercase(self):
        """测试域名小写化"""
        url = "https://EXAMPLE.COM/path"
        result = get_domain(url)
        assert result == "example.com"


class TestGetPath:
    """测试 get_path 函数"""

    def test_get_path_basic(self):
        """测试基本路径提取"""
        url = "https://example.com/path/to/page"
        result = get_path(url)
        assert result == "/path/to/page"

    def test_get_path_root(self):
        """测试根路径"""
        url = "https://example.com"
        result = get_path(url)
        assert result == ""

    def test_get_path_with_query(self):
        """测试带查询参数的路径"""
        url = "https://example.com/path?key=value"
        result = get_path(url)
        assert result == "/path"


class TestIsSameDomain:
    """测试 is_same_domain 函数"""

    def test_same_domain(self):
        """测试同域名"""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert is_same_domain(url1, url2) is True

    def test_different_domain(self):
        """测试不同域名"""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"
        assert is_same_domain(url1, url2) is False

    def test_same_domain_case_insensitive(self):
        """测试域名大小写不敏感"""
        url1 = "https://EXAMPLE.com/page"
        url2 = "https://example.COM/page"
        assert is_same_domain(url1, url2) is True


class TestJoinUrl:
    """测试 join_url 函数"""

    def test_join_url_absolute(self):
        """测试绝对 URL"""
        base = "https://example.com/path/"
        url = "/absolute/path"
        result = join_url(base, url)
        assert result == "https://example.com/absolute/path"

    def test_join_url_relative(self):
        """测试相对 URL"""
        base = "https://example.com/path/"
        url = "relative/path"
        result = join_url(base, url)
        assert result == "https://example.com/path/relative/path"

    def test_join_url_with_query(self):
        """测试带查询参数的 URL"""
        base = "https://example.com/path"
        url = "?key=value"
        result = join_url(base, url)
        assert result == "https://example.com/path?key=value"
