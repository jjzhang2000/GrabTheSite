"""HTTP 客户端模块

提供统一的 HTTP 请求功能：
- Session 管理
- 连接池配置
- 请求重试
- 超时处理
"""

import os
from typing import Any, Dict, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logger import _ as _t
from logger import setup_logger

logger = setup_logger(__name__)


def _get_default_user_agent() -> str:
    """获取默认 User-Agent，使用延迟导入避免循环导入"""
    try:
        from app_config import USER_AGENT
        return USER_AGENT
    except ImportError:
        # 如果 config 模块不可用，使用硬编码默认值
        return "GrabTheSite/1.0"


class HTTPClient:
    """HTTP 客户端

    封装 requests.Session，提供统一的 HTTP 请求功能。
    支持连接池配置、自动重试、超时处理等。
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        pool_connections: int = 1,
        pool_maxsize: int = 1,
        max_retries: int = 0,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
        keep_alive: bool = False
    ):
        """初始化 HTTP 客户端

        Args:
            user_agent: User-Agent 字符串
            pool_connections: 连接池连接数
            pool_maxsize: 连接池最大大小
            max_retries: 最大重试次数
            timeout: 默认超时时间（秒）
            headers: 额外的请求头
            keep_alive: 是否保持连接
        """
        self.user_agent: str = user_agent or _get_default_user_agent()
        self.timeout: float = timeout
        self._session: requests.Session = self._create_session(
            pool_connections, pool_maxsize, max_retries, keep_alive
        )

        # 设置默认请求头
        self._session.headers.update({
            'User-Agent': self.user_agent,
        })

        if not keep_alive:
            self._session.headers.update({'Connection': 'close'})

        # 添加额外的请求头
        if headers:
            self._session.headers.update(headers)

    def _create_session(
        self,
        pool_connections: int,
        pool_maxsize: int,
        max_retries: int,
        keep_alive: bool
    ) -> requests.Session:
        """创建并配置 Session

        Args:
            pool_connections: 连接池连接数
            pool_maxsize: 连接池最大大小
            max_retries: 最大重试次数
            keep_alive: 是否保持连接

        Returns:
            requests.Session: 配置好的 Session
        """
        session = requests.Session()

        # 配置重试策略
        if max_retries > 0:
            retry_strategy = Retry(
                total=max_retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
        else:
            retry_strategy = Retry(total=0)

        # 配置适配器
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
        )

        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def get(
        self,
        url: str,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """发送 GET 请求

        Args:
            url: 请求 URL
            timeout: 超时时间（秒），None 使用默认值
            **kwargs: 其他 requests 参数

        Returns:
            requests.Response: 响应对象

        Raises:
            requests.RequestException: 请求失败
        """
        actual_timeout = timeout if timeout is not None else self.timeout
        return self._session.get(url, timeout=actual_timeout, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """发送 POST 请求

        Args:
            url: 请求 URL
            data: 表单数据
            json: JSON 数据
            timeout: 超时时间（秒）
            **kwargs: 其他 requests 参数

        Returns:
            requests.Response: 响应对象
        """
        actual_timeout = timeout if timeout is not None else self.timeout
        return self._session.post(url, data=data, json=json, timeout=actual_timeout, **kwargs)

    def head(
        self,
        url: str,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """发送 HEAD 请求

        Args:
            url: 请求 URL
            timeout: 超时时间（秒）
            **kwargs: 其他 requests 参数

        Returns:
            requests.Response: 响应对象
        """
        actual_timeout = timeout if timeout is not None else self.timeout
        return self._session.head(url, timeout=actual_timeout, **kwargs)

    def download(
        self,
        url: str,
        file_path: str,
        chunk_size: int = 8192,
        timeout: Optional[float] = None,
        **kwargs
    ) -> bool:
        """下载文件到本地

        Args:
            url: 文件 URL
            file_path: 本地文件路径
            chunk_size: 下载块大小
            timeout: 超时时间（秒）
            **kwargs: 其他 requests 参数

        Returns:
            bool: 下载是否成功
        """
        try:
            response = self.get(url, stream=True, timeout=timeout, **kwargs)
            response.raise_for_status()

            # 创建目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 写入文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

            return True
        except Exception as e:
            logger.error(_t("下载文件失败") + f": {url} -> {file_path}, {e}")
            return False

    def close(self) -> None:
        """关闭 Session，释放资源"""
        self._session.close()

    def __enter__(self) -> 'HTTPClient':
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()


class HTTPClientManager:
    """HTTP 客户端管理器

    管理多个 HTTP 客户端实例，支持单例模式。
    """

    _instances: Dict[str, HTTPClient] = {}

    @classmethod
    def get_client(
        cls,
        name: str = "default",
        **kwargs
    ) -> HTTPClient:
        """获取或创建 HTTP 客户端

        Args:
            name: 客户端名称
            **kwargs: HTTPClient 构造参数

        Returns:
            HTTPClient: HTTP 客户端实例
        """
        if name not in cls._instances:
            cls._instances[name] = HTTPClient(**kwargs)
        return cls._instances[name]

    @classmethod
    def close_client(cls, name: str) -> None:
        """关闭指定客户端

        Args:
            name: 客户端名称
        """
        if name in cls._instances:
            cls._instances[name].close()
            del cls._instances[name]

    @classmethod
    def close_all(cls) -> None:
        """关闭所有客户端"""
        for client in cls._instances.values():
            client.close()
        cls._instances.clear()


# 便捷函数
def create_default_client() -> HTTPClient:
    """创建默认 HTTP 客户端

    适用于大多数场景，禁用连接池，避免后台线程。

    Returns:
        HTTPClient: 默认 HTTP 客户端
    """
    return HTTPClient(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=0,
        keep_alive=False
    )


def create_retry_client(
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> HTTPClient:
    """创建带重试的 HTTP 客户端

    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子

    Returns:
        HTTPClient: 带重试的 HTTP 客户端
    """
    return HTTPClient(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=max_retries,
        keep_alive=False
    )
