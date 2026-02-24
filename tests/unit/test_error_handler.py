"""错误处理器模块单元测试"""

import pytest
from unittest.mock import Mock, patch
import time

from utils.error_handler import ErrorHandler, retry


class TestErrorHandler:
    """测试 ErrorHandler 类"""

    def test_init_default(self):
        """测试默认初始化"""
        handler = ErrorHandler()
        assert handler.retry_count == 3
        assert handler.retry_delay == 2
        assert handler.exponential_backoff is True
        assert handler.fail_strategy == 'log'

    def test_init_custom(self):
        """测试自定义初始化"""
        handler = ErrorHandler(
            retry_count=5,
            retry_delay=1,
            exponential_backoff=False,
            fail_strategy='raise'
        )
        assert handler.retry_count == 5
        assert handler.retry_delay == 1
        assert handler.exponential_backoff is False
        assert handler.fail_strategy == 'raise'

    def test_retry_success_first_attempt(self):
        """测试首次尝试成功"""
        handler = ErrorHandler()
        mock_func = Mock(return_value="success")

        decorated = handler.retry(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_with_network_error(self):
        """测试网络错误会重试"""
        handler = ErrorHandler(retry_count=2, retry_delay=0.01)
        mock_func = Mock(side_effect=[Exception("Connection timeout"), "success"])

        decorated = handler.retry(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_exhausted_with_network_error(self):
        """测试网络错误重试次数耗尽"""
        handler = ErrorHandler(retry_count=2, retry_delay=0.01, fail_strategy='raise')
        mock_func = Mock(side_effect=Exception("Connection timeout"))

        decorated = handler.retry(mock_func)

        with pytest.raises(Exception, match="Connection timeout"):
            decorated()

        assert mock_func.call_count == 3  # 初始 + 2次重试

    def test_retry_non_retryable_error(self):
        """测试非可重试错误不会重试"""
        handler = ErrorHandler(
            retryable_errors=[],
            fail_strategy='raise'
        )
        mock_func = Mock(side_effect=ValueError("non-retryable"))

        decorated = handler.retry(mock_func)

        with pytest.raises(ValueError, match="non-retryable"):
            decorated()

        assert mock_func.call_count == 1  # 不重试

    def test_retry_with_exponential_backoff(self):
        """测试指数退避"""
        handler = ErrorHandler(
            retry_count=2,
            retry_delay=0.05,
            exponential_backoff=True
        )
        mock_func = Mock(side_effect=[Exception("Connection timeout"), "success"])

        start_time = time.time()
        decorated = handler.retry(mock_func)
        decorated()
        elapsed = time.time() - start_time

        assert mock_func.call_count == 2
        # 指数退避应该有延迟
        assert elapsed >= 0.05

    def test_retry_without_exponential_backoff(self):
        """测试固定延迟"""
        handler = ErrorHandler(
            retry_count=2,
            retry_delay=0.05,
            exponential_backoff=False
        )
        mock_func = Mock(side_effect=[Exception("Connection timeout"), "success"])

        start_time = time.time()
        decorated = handler.retry(mock_func)
        decorated()
        elapsed = time.time() - start_time

        assert mock_func.call_count == 2
        # 固定延迟
        assert elapsed >= 0.05

    def test_retry_with_args(self):
        """测试带参数的重试"""
        handler = ErrorHandler(retry_count=2, retry_delay=0.01)

        @handler.retry
        def test_func(arg1, arg2):
            return f"{arg1}-{arg2}"

        result = test_func("hello", "world")

        assert result == "hello-world"

    def test_retry_with_kwargs(self):
        """测试带关键字参数的重试"""
        handler = ErrorHandler(retry_count=2, retry_delay=0.01)

        @handler.retry
        def test_func(a=1, b=2):
            return a + b

        result = test_func(a=5, b=10)

        assert result == 15


class TestRetryDecorator:
    """测试 retry 装饰器"""

    def test_retry_decorator(self):
        """测试装饰器功能"""
        call_count = 0

        @retry(retry_count=3, retry_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection timeout")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count == 3

    def test_retry_decorator_with_args(self):
        """测试带参数的装饰器"""
        @retry(retry_count=2, retry_delay=0.01)
        def test_func(arg1, arg2):
            return f"{arg1}-{arg2}"

        result = test_func("hello", "world")

        assert result == "hello-world"

    def test_retry_decorator_with_kwargs(self):
        """测试带关键字参数的装饰器"""
        @retry(retry_count=2, retry_delay=0.01)
        def test_func(a=1, b=2):
            return a + b

        result = test_func(a=5, b=10)

        assert result == 15
