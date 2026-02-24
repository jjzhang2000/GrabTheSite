"""配置管理模块

提供配置加载、验证和管理功能：
- 支持默认配置和用户配置合并
- 提供配置验证功能
- 支持通过点号路径访问嵌套配置
"""

import os
from typing import Dict, Any, Optional, List, Union, Callable
from urllib.parse import urlparse
import yaml
from logger import setup_logger, _ as _t

logger = setup_logger(__name__)


class ValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_url(url: str, field_name: str = "URL") -> None:
        """验证 URL 格式

        Args:
            url: 要验证的 URL
            field_name: 字段名称（用于错误信息）

        Raises:
            ValidationError: URL 格式无效
        """
        if not url:
            raise ValidationError(f"{field_name} 不能为空")

        parsed = urlparse(url)
        if not parsed.scheme:
            raise ValidationError(f"{field_name} 缺少协议（如 https://）: {url}")
        if not parsed.netloc:
            raise ValidationError(f"{field_name} 缺少域名: {url}")
        if parsed.scheme not in ('http', 'https'):
            raise ValidationError(f"{field_name} 协议必须是 http 或 https: {url}")

    @staticmethod
    def validate_positive_int(value: Any, field_name: str, allow_zero: bool = True) -> int:
        """验证正整数

        Args:
            value: 要验证的值
            field_name: 字段名称
            allow_zero: 是否允许零

        Returns:
            int: 验证后的整数值

        Raises:
            ValidationError: 验证失败
        """
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} 必须是整数: {value}")

        if allow_zero:
            if int_value < 0:
                raise ValidationError(f"{field_name} 不能为负数: {int_value}")
        else:
            if int_value <= 0:
                raise ValidationError(f"{field_name} 必须是正整数: {int_value}")

        return int_value

    @staticmethod
    def validate_range(value: Union[int, float], field_name: str,
                       min_val: Optional[Union[int, float]] = None,
                       max_val: Optional[Union[int, float]] = None) -> Union[int, float]:
        """验证数值范围

        Args:
            value: 要验证的值
            field_name: 字段名称
            min_val: 最小值
            max_val: 最大值

        Returns:
            验证后的值

        Raises:
            ValidationError: 验证失败
        """
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} 必须是数字: {value}")

        if min_val is not None and num_value < min_val:
            raise ValidationError(f"{field_name} 不能小于 {min_val}: {num_value}")
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"{field_name} 不能大于 {max_val}: {num_value}")

        return num_value

    @staticmethod
    def validate_path(path: str, field_name: str, must_exist: bool = False) -> str:
        """验证路径

        Args:
            path: 要验证的路径
            field_name: 字段名称
            must_exist: 路径是否必须存在

        Returns:
            str: 验证后的路径

        Raises:
            ValidationError: 验证失败
        """
        if not path:
            raise ValidationError(f"{field_name} 不能为空")

        # 展开用户目录
        expanded_path = os.path.expanduser(path)

        if must_exist and not os.path.exists(expanded_path):
            raise ValidationError(f"{field_name} 路径不存在: {expanded_path}")

        return expanded_path

    @staticmethod
    def validate_choice(value: Any, field_name: str, choices: List[str]) -> str:
        """验证枚举值

        Args:
            value: 要验证的值
            field_name: 字段名称
            choices: 允许的选项

        Returns:
            str: 验证后的值

        Raises:
            ValidationError: 验证失败
        """
        str_value = str(value).lower()
        valid_choices = [c.lower() for c in choices]

        if str_value not in valid_choices:
            raise ValidationError(
                f"{field_name} 必须是以下值之一: {', '.join(choices)}, 实际值: {value}"
            )

        return str_value


class ConfigManager:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG: Dict[str, Any] = {
        "target_url": "",
        "crawl": {
            "max_depth": 1,
            "max_files": 10,
            "delay": 1.0,
            "random_delay": True,
            "threads": 4,
            "incremental": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "error_handling": {
            "retry_count": 3,
            "retry_delay": 2.0,
            "exponential_backoff": True,
            "retryable_errors": [429, 500, 502, 503, 504],
            "fail_strategy": "log"
        },
        "js_rendering": {
            "enabled": True,
            "timeout": 30
        },
        "output": {
            "base_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
            "site_name": "",
            "full_path": ""
        },
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
        "exclude_urls": []
    }

    def __init__(self, config_dir: str = "config"):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir: str = config_dir
        self.default_config_file: str = os.path.join(config_dir, "default.yaml")
        self.user_config_file: str = os.path.join(config_dir, "config.yaml")
        self._config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._validator: ConfigValidator = ConfigValidator()

    def load(self) -> Dict[str, Any]:
        """加载配置

        加载顺序：默认配置 -> 默认配置文件 -> 用户配置文件

        Returns:
            dict: 合并后的配置
        """
        # 从默认配置开始
        config = self.DEFAULT_CONFIG.copy()
        config_loaded = False

        # 加载默认配置文件
        if os.path.exists(self.default_config_file):
            try:
                with open(self.default_config_file, "r", encoding="utf-8") as f:
                    default_config = yaml.safe_load(f)
                    if default_config:
                        config = self._merge(config, default_config)
                        logger.debug(_t("已加载默认配置文件") + f": {self.default_config_file}")
                        config_loaded = True
            except Exception as e:
                logger.error(_t("加载默认配置文件失败") + f": {e}")
        else:
            logger.warning(_t("默认配置文件不存在") + f": {self.default_config_file}")

        # 加载用户配置文件
        if os.path.exists(self.user_config_file):
            try:
                with open(self.user_config_file, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        config = self._merge(config, user_config)
                        logger.debug(_t("已加载用户配置文件") + f": {self.user_config_file}")
                        config_loaded = True
            except Exception as e:
                logger.error(_t("加载用户配置文件失败") + f": {e}")
        else:
            logger.debug(_t("用户配置文件不存在") + f": {self.user_config_file}")

        if not config_loaded:
            logger.warning(_t("未加载任何配置文件，使用默认配置"))

        # 计算派生配置
        self._compute_derived_config(config)

        # 验证配置
        self.validate(config)

        self._config = config
        return config

    def validate(self, config: Dict[str, Any]) -> None:
        """验证配置

        Args:
            config: 要验证的配置

        Raises:
            ValidationError: 验证失败时抛出
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 验证 target_url
        try:
            if config.get("target_url"):
                self._validator.validate_url(config["target_url"], "target_url")
        except ValidationError as e:
            errors.append(str(e))

        # 验证 crawl 配置
        if "crawl" in config:
            crawl = config["crawl"]

            # max_depth
            try:
                if "max_depth" in crawl:
                    crawl["max_depth"] = self._validator.validate_positive_int(
                        crawl["max_depth"], "crawl.max_depth"
                    )
            except ValidationError as e:
                warnings.append(str(e))
                crawl["max_depth"] = 1

            # max_files
            try:
                if "max_files" in crawl:
                    crawl["max_files"] = self._validator.validate_positive_int(
                        crawl["max_files"], "crawl.max_files"
                    )
            except ValidationError as e:
                warnings.append(str(e))
                crawl["max_files"] = 10

            # threads
            try:
                if "threads" in crawl:
                    threads = self._validator.validate_positive_int(
                        crawl["threads"], "crawl.threads", allow_zero=False
                    )
                    crawl["threads"] = self._validator.validate_range(
                        threads, "crawl.threads", min_val=1, max_val=20
                    )
            except ValidationError as e:
                warnings.append(str(e))
                crawl["threads"] = 4

            # delay
            try:
                if "delay" in crawl:
                    crawl["delay"] = self._validator.validate_range(
                        crawl["delay"], "crawl.delay", min_val=0, max_val=60
                    )
            except ValidationError as e:
                warnings.append(str(e))
                crawl["delay"] = 1.0

        # 验证 output 配置
        if "output" in config:
            output = config["output"]
            try:
                if "base_dir" in output:
                    output["base_dir"] = self._validator.validate_path(
                        output["base_dir"], "output.base_dir"
                    )
            except ValidationError as e:
                warnings.append(str(e))
                output["base_dir"] = os.path.join(os.path.expanduser("~"), "Downloads")

        # 验证 logging 配置
        if "logging" in config:
            logging_config = config["logging"]
            try:
                if "level" in logging_config:
                    logging_config["level"] = self._validator.validate_choice(
                        logging_config["level"],
                        "logging.level",
                        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                    ).upper()
            except ValidationError as e:
                warnings.append(str(e))
                logging_config["level"] = "INFO"

        # 验证 i18n 配置
        if "i18n" in config:
            i18n = config["i18n"]
            try:
                if "lang" in i18n:
                    i18n["lang"] = self._validator.validate_choice(
                        i18n["lang"],
                        "i18n.lang",
                        ["en", "zh_CN"]
                    )
            except ValidationError as e:
                warnings.append(str(e))
                i18n["lang"] = "en"

        # 验证 error_handling 配置
        if "error_handling" in config:
            error_handling = config["error_handling"]
            try:
                if "fail_strategy" in error_handling:
                    error_handling["fail_strategy"] = self._validator.validate_choice(
                        error_handling["fail_strategy"],
                        "error_handling.fail_strategy",
                        ["log", "skip", "raise"]
                    )
            except ValidationError as e:
                warnings.append(str(e))
                error_handling["fail_strategy"] = "log"

        # 输出警告
        for warning in warnings:
            logger.warning(_t("配置警告") + f": {warning}")

        # 如果有错误，抛出异常
        if errors:
            raise ValidationError("; ".join(errors))

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号路径

        Args:
            key: 配置键，支持点号路径（如 "crawl.max_depth"）
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号路径

        Args:
            key: 配置键，支持点号路径
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()

    def _merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value

        return result

    def _compute_derived_config(self, config: Dict[str, Any]) -> None:
        """计算派生配置

        Args:
            config: 配置字典
        """
        # 从 target_url 中提取域名作为 site_name
        if config.get("target_url"):
            parsed_url = urlparse(config["target_url"])
            config["output"]["site_name"] = parsed_url.netloc

            # 计算 full_path
            config["output"]["full_path"] = os.path.join(
                config["output"]["base_dir"],
                config["output"]["site_name"]
            )


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例

    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config() -> Dict[str, Any]:
    """加载配置的便捷函数

    Returns:
        dict: 配置字典
    """
    return get_config_manager().load()


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数

    Args:
        key: 配置键
        default: 默认值

    Returns:
        配置值
    """
    return get_config_manager().get(key, default)
