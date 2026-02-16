"""配置管理模块

负责加载和管理YAML配置文件，支持：
1. 默认配置（default.yaml）
2. 用户配置（config.yaml）覆盖默认配置
3. 命令行参数覆盖配置文件

配置优先级：命令行 > 用户配置 > 默认配置
"""

import os
from typing import Dict, Any
import yaml
from logger import setup_logger, _ as _t
from urllib.parse import urlparse

logger = setup_logger(__name__)

# 常用配置常量
DEFAULT_REQUEST_TIMEOUT = 10  # 默认请求超时（秒）
DEFAULT_CHUNK_SIZE = 8192     # 默认文件下载块大小（字节）
DEFAULT_RETRY_COUNT = 3       # 默认重试次数
DEFAULT_RETRY_DELAY = 2       # 默认重试延迟（秒）

# 默认配置（最低优先级）
DEFAULT_CONFIG = {
    "target_url": "https://www.mir.com.my/rb/photography/",
    "crawl": {
        "max_depth": 1,
        "max_files": 10,
        "delay": 1,
        "random_delay": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "error_handling": {
        "retry_count": 3,
        "retry_delay": 2,
        "exponential_backoff": True,
        "retryable_errors": [429, 500, 502, 503, 504],
        "fail_strategy": "log"
    },
    "js_rendering": {
        "enable": False,
        "timeout": 30,
        "engine": "playwright"  # 可选: "playwright" (推荐) 或 "pyppeteer"
    },
    "output": {
        "base_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
        "sitemap": {
            "enable": False,
            "enable_html": False
        }
    },
    "exclude": [
        "https://www.mir.com.my/rb/photography/ftz/"
    ],
    "logging": {
        "level": "INFO",
        "file": "logs/grabthesite.log",
        "max_bytes": 10485760,
        "backup_count": 5
    },
    "i18n": {
        "lang": "en",
        "available_langs": ["en", "zh_CN"]
    },
    "plugins": {
        "save_plugin": True
    }
}

# 配置文件路径
CONFIG_DIR = "config"
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "default.yaml")
USER_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")


def load_config() -> Dict[str, Any]:
    """加载配置文件
    
    Returns:
        dict: 合并后的配置
    """
    # 从默认配置开始
    config = DEFAULT_CONFIG.copy()
    
    # 加载默认配置文件
    config_loaded = False
    if os.path.exists(DEFAULT_CONFIG_FILE):
        try:
            with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                default_config = yaml.safe_load(f)
                if default_config:
                    config = merge_configs(config, default_config)
                    logger.debug(_t("已加载默认配置文件") + f": {DEFAULT_CONFIG_FILE}")
                    config_loaded = True
        except Exception as e:
            logger.error(_t("加载默认配置文件失败") + f": {e}")
    else:
        logger.warning(_t("默认配置文件不存在") + f": {DEFAULT_CONFIG_FILE}")
    
    # 加载用户配置文件
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config = merge_configs(config, user_config)
                    logger.debug(_t("已加载用户配置文件") + f": {USER_CONFIG_FILE}")
                    config_loaded = True
        except Exception as e:
            logger.error(_t("加载用户配置文件失败") + f": {e}")
    else:
        logger.debug(_t("用户配置文件不存在") + f": {USER_CONFIG_FILE}")
    
    # 检查配置是否加载成功
    if not config_loaded:
        logger.error(_t("配置文件加载失败，使用默认配置"))
    
    # 从 target_url 中提取域名作为 site_name
    parsed_url = urlparse(config["target_url"])
    site_name = parsed_url.netloc
    config["output"]["site_name"] = site_name
    
    # 计算 full_path
    config["output"]["full_path"] = os.path.join(config["output"]["base_dir"], config["output"]["site_name"])
    
    # 验证配置
    validate_config(config)
    
    return config


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置
    
    Args:
        base: 基础配置
        override: 覆盖配置
    
    Returns:
        dict: 合并后的配置
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = merge_configs(base[key], value)
        else:
            base[key] = value
    return base


def validate_config(config: Dict[str, Any]) -> None:
    """验证配置
    
    Args:
        config: 配置字典
    """
    # 验证必填项
    required_fields = ["target_url", "crawl", "output"]
    for field in required_fields:
        if field not in config:
            logger.warning(_t("配置缺少必填项") + f": {field}")
    
    # 验证抓取参数
    if "crawl" in config:
        crawl_config = config["crawl"]
        if "max_depth" in crawl_config and crawl_config["max_depth"] < 0:
            logger.warning(_t("max_depth 不能为负数，设置为 0"))
            crawl_config["max_depth"] = 0
        if "max_files" in crawl_config and crawl_config["max_files"] < 0:
            logger.warning(_t("max_files 不能为负数，设置为 0"))
            crawl_config["max_files"] = 0


# 加载配置
config = load_config()

# 导出完整配置对象
CONFIG = config

# 爬取核心参数
TARGET_URL = config["target_url"]
MAX_DEPTH = config["crawl"]["max_depth"]
MAX_FILES = config["crawl"]["max_files"]
USER_AGENT = config["crawl"]["user_agent"]

# 爬取行为参数
DELAY = config["crawl"].get("delay", 1)
RANDOM_DELAY = config["crawl"].get("random_delay", True)
THREADS = config["crawl"].get("threads", 4)

# 输出相关
BASE_OUTPUT_DIR = config["output"]["base_dir"]
SITE_NAME = config["output"]["site_name"]
OUTPUT_DIR = config["output"]["full_path"]
EXCLUDE_LIST = config.get("exclude", [])

# 子配置字典
LOGGING_CONFIG = config.get("logging", {})
ERROR_HANDLING_CONFIG = config.get("error_handling", {})
JS_RENDERING_CONFIG = config.get("js_rendering", {})
I18N_CONFIG = config.get("i18n", {})
# 插件配置格式: {plugin_name: True/False}
PLUGIN_CONFIG = config.get("plugins", {})
