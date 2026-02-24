"""HTTP 客户端模块单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from utils.http_client import (
    HTTPClient,
    HTTPClientManager,
    create_default_client,
    create_retry_client,
)


class TestHTTPClient:
    """测试 HTTPClient 类"""

    @patch('utils.http_client.requests.Session')
    def test_init_default(self, mock_session_class):
        """测试默认初始化"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client = HTTPClient()

        assert client.user_agent is not None
        assert client.timeout == 10.0
        mock_session.mount.assert_called()

    @patch('utils.http_client.requests.Session')
    def test_init_custom(self, mock_session_class):
        """测试自定义初始化"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client = HTTPClient(
            user_agent="Custom Agent",
            timeout=30.0,
            max_retries=3
        )

        assert client.user_agent == "Custom Agent"
        assert client.timeout == 30.0

    @patch('utils.http_client.requests.Session')
    def test_get(self, mock_session_class):
        """测试 GET 请求"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = HTTPClient()
        response = client.get("https://example.com")

        mock_session.get.assert_called_once_with(
            "https://example.com",
            timeout=10.0
        )
        assert response == mock_response

    @patch('utils.http_client.requests.Session')
    def test_post(self, mock_session_class):
        """测试 POST 请求"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = HTTPClient()
        response = client.post(
            "https://example.com",
            data={"key": "value"},
            json={"json_key": "json_value"}
        )

        mock_session.post.assert_called_once_with(
            "https://example.com",
            data={"key": "value"},
            json={"json_key": "json_value"},
            timeout=10.0
        )
        assert response == mock_response

    @patch('utils.http_client.requests.Session')
    def test_head(self, mock_session_class):
        """测试 HEAD 请求"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = HTTPClient()
        response = client.head("https://example.com")

        mock_session.head.assert_called_once_with(
            "https://example.com",
            timeout=10.0
        )
        assert response == mock_response

    @patch('utils.http_client.requests.Session')
    @patch('builtins.open', create=True)
    @patch('os.makedirs')
    def test_download_success(self, mock_makedirs, mock_open, mock_session_class):
        """测试下载文件成功"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        mock_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        client = HTTPClient()
        result = client.download(
            "https://example.com/file.txt",
            "/tmp/test/file.txt"
        )

        assert result is True
        mock_makedirs.assert_called_once()
        mock_session.get.assert_called_once()

    @patch('utils.http_client.requests.Session')
    def test_download_failure(self, mock_session_class):
        """测试下载文件失败"""
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Network error")
        mock_session_class.return_value = mock_session

        client = HTTPClient()
        result = client.download(
            "https://example.com/file.txt",
            "/tmp/test/file.txt"
        )

        assert result is False

    @patch('utils.http_client.requests.Session')
    def test_context_manager(self, mock_session_class):
        """测试上下文管理器"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        with HTTPClient() as client:
            assert isinstance(client, HTTPClient)

        mock_session.close.assert_called_once()


class TestHTTPClientManager:
    """测试 HTTPClientManager 类"""

    def setup_method(self):
        """每个测试前清理实例"""
        HTTPClientManager._instances.clear()

    @patch('utils.http_client.requests.Session')
    def test_get_client_singleton(self, mock_session_class):
        """测试获取客户端单例"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client1 = HTTPClientManager.get_client("test")
        client2 = HTTPClientManager.get_client("test")

        assert client1 is client2

    @patch('utils.http_client.requests.Session')
    def test_get_client_different_names(self, mock_session_class):
        """测试获取不同名称的客户端"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client1 = HTTPClientManager.get_client("client1")
        client2 = HTTPClientManager.get_client("client2")

        assert client1 is not client2

    @patch('utils.http_client.requests.Session')
    def test_close_client(self, mock_session_class):
        """测试关闭客户端"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client = HTTPClientManager.get_client("test")
        HTTPClientManager.close_client("test")

        mock_session.close.assert_called_once()
        assert "test" not in HTTPClientManager._instances

    @patch('utils.http_client.requests.Session')
    def test_close_all(self, mock_session_class):
        """测试关闭所有客户端"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        HTTPClientManager.get_client("client1")
        HTTPClientManager.get_client("client2")

        HTTPClientManager.close_all()

        assert len(HTTPClientManager._instances) == 0
        assert mock_session.close.call_count == 2


class TestCreateClient:
    """测试便捷函数"""

    @patch('utils.http_client.requests.Session')
    def test_create_default_client(self, mock_session_class):
        """测试创建默认客户端"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client = create_default_client()

        assert isinstance(client, HTTPClient)

    @patch('utils.http_client.requests.Session')
    def test_create_retry_client(self, mock_session_class):
        """测试创建带重试的客户端"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        client = create_retry_client(max_retries=5)

        assert isinstance(client, HTTPClient)
