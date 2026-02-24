"""配置管理模块

此模块现在作为 utils.config_manager 的兼容层，保留向后兼容性。
建议使用新的配置管理器：
    from utils import ConfigManager, load_config, get_config
"""

from utils.config_manager import (
    ConfigManager,
    ConfigValidator,
    ValidationError,
    load_config,
    get_config,
    get_config_manager
)
from logger import setup_logger

logger = setup_logger(__name__)

# 加载配置
config = load_config()

# 导出完整配置对象
CONFIG = config

# 爬取核心参数
TARGET_URL = config.get("target_url", "")
MAX_DEPTH = config.get("crawl", {}).get("max_depth", 1)
MAX_FILES = config.get("crawl", {}).get("max_files", 10)
USER_AGENT = config.get("crawl", {}).get("user_agent", "")

# 爬取行为参数
DELAY = config.get("crawl", {}).get("delay", 1)
RANDOM_DELAY = config.get("crawl", {}).get("random_delay", True)
THREADS = config.get("crawl", {}).get("threads", 4)

# 输出相关
BASE_OUTPUT_DIR = config.get("output", {}).get("base_dir", "")
SITE_NAME = config.get("output", {}).get("site_name", "")
OUTPUT_DIR = config.get("output", {}).get("full_path", "")
EXCLUDE_LIST = config.get("exclude_urls", [])

# 子配置字典
LOGGING_CONFIG = config.get("logging", {})
ERROR_HANDLING_CONFIG = config.get("error_handling", {})
JS_RENDERING_CONFIG = config.get("js_rendering", {})
I18N_CONFIG = config.get("i18n", {})

# 便捷常量
DEFAULT_REQUEST_TIMEOUT = 10  # 默认请求超时（秒）
DEFAULT_CHUNK_SIZE = 8192     # 默认文件下载块大小（字节）
DEFAULT_RETRY_COUNT = 3       # 默认重试次数
DEFAULT_RETRY_DELAY = 2       # 默认重试延迟（秒）

__all__ = [
    # 新的配置管理类
    "ConfigManager",
    "ConfigValidator",
    "ValidationError",
    "load_config",
    "get_config",
    "get_config_manager",
    # 旧的兼容导出
    "config",
    "CONFIG",
    "TARGET_URL",
    "MAX_DEPTH",
    "MAX_FILES",
    "USER_AGENT",
    "DELAY",
    "RANDOM_DELAY",
    "THREADS",
    "BASE_OUTPUT_DIR",
    "SITE_NAME",
    "OUTPUT_DIR",
    "EXCLUDE_LIST",
    "LOGGING_CONFIG",
    "ERROR_HANDLING_CONFIG",
    "JS_RENDERING_CONFIG",
    "I18N_CONFIG",
    "DEFAULT_REQUEST_TIMEOUT",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_RETRY_COUNT",
    "DEFAULT_RETRY_DELAY",
]
