"""自定义异常模块

定义项目中使用的自定义异常层次结构：
- GrabTheSiteError: 基础异常
- ConfigError: 配置错误
- CrawlError: 抓取错误
- NetworkError: 网络错误
- PluginError: 插件错误
"""


class GrabTheSiteError(Exception):
    """GrabTheSite 基础异常

    所有自定义异常的基类。
    """
    pass


class ConfigError(GrabTheSiteError):
    """配置错误

    配置加载、验证失败时抛出。
    """
    pass


class ValidationError(ConfigError):
    """配置验证错误

    配置验证失败时抛出。
    """
    pass


class CrawlError(GrabTheSiteError):
    """抓取错误

    抓取过程中发生的错误。
    """
    pass


class NetworkError(CrawlError):
    """网络错误

    网络请求相关的错误。
    """
    pass


class TimeoutError(NetworkError):
    """超时错误

    请求超时。
    """
    pass


class RateLimitError(NetworkError):
    """速率限制错误

    请求被速率限制。
    """
    pass


class ConnectionError(NetworkError):
    """连接错误

    无法建立连接。
    """
    pass


class HTTPError(NetworkError):
    """HTTP 错误

    HTTP 请求返回错误状态码。

    Attributes:
        status_code: HTTP 状态码
        url: 请求 URL
    """

    def __init__(self, message: str, status_code: int = None, url: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class RetryExhaustedError(NetworkError):
    """重试耗尽错误

    所有重试尝试都失败。
    """
    pass


class PluginError(GrabTheSiteError):
    """插件错误

    插件相关的错误。
    """
    pass


class PluginLoadError(PluginError):
    """插件加载错误

    插件加载失败。
    """
    pass


class PluginHookError(PluginError):
    """插件钩子错误

    插件钩子执行失败。
    """
    pass


class RenderError(GrabTheSiteError):
    """渲染错误

    JavaScript 渲染相关的错误。
    """
    pass


class JSError(RenderError):
    """JavaScript 错误

    页面 JavaScript 执行错误。
    """
    pass


class FileError(GrabTheSiteError):
    """文件错误

    文件操作相关的错误。
    """
    pass


class FileNotFoundError(FileError):
    """文件未找到错误

    文件不存在。
    """
    pass


class FileAccessError(FileError):
    """文件访问错误

    无法访问文件（权限问题等）。
    """
    pass


class StateError(GrabTheSiteError):
    """状态错误

    状态管理相关的错误。
    """
    pass


class StateLoadError(StateError):
    """状态加载错误

    无法加载状态文件。
    """
    pass


class StateSaveError(StateError):
    """状态保存错误

    无法保存状态文件。
    """
    pass


class URLFilterError(GrabTheSiteError):
    """URL 过滤错误

    URL 过滤相关的错误。
    """
    pass


class InvalidURLError(URLFilterError):
    """无效 URL 错误

    URL 格式无效。
    """
    pass


class URLNotAllowedError(URLFilterError):
    """URL 不允许错误

    URL 不在允许的范围内（不同域名、被排除等）。
    """
    pass


class TaskError(GrabTheSiteError):
    """任务错误

    抓取任务相关的错误。
    """
    pass


class TaskNotFoundError(TaskError):
    """任务未找到错误

    任务不存在。
    """
    pass


class TaskAlreadyExistsError(TaskError):
    """任务已存在错误

    任务已存在。
    """
    pass


class TaskStateError(TaskError):
    """任务状态错误

    任务状态转换无效。
    """
    pass
