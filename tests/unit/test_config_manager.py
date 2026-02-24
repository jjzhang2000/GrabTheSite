"""配置管理器模块单元测试"""

import pytest
import os
import tempfile
from utils.config_manager import ConfigManager, ConfigValidator, ValidationError


class TestConfigValidator:
    """测试配置验证器"""

    def test_validate_url_valid(self):
        """测试验证有效 URL"""
        ConfigValidator.validate_url("https://example.com", "test_url")

    def test_validate_url_empty(self):
        """测试验证空 URL"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_url("", "test_url")

    def test_validate_url_no_scheme(self):
        """测试验证缺少协议的 URL"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_url("example.com/path", "test_url")

    def test_validate_url_invalid_scheme(self):
        """测试验证无效协议的 URL"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_url("ftp://example.com", "test_url")

    def test_validate_positive_int_valid(self):
        """测试验证有效正整数"""
        result = ConfigValidator.validate_positive_int(10, "test_field")
        assert result == 10

    def test_validate_positive_int_zero_allowed(self):
        """测试验证允许零"""
        result = ConfigValidator.validate_positive_int(0, "test_field", allow_zero=True)
        assert result == 0

    def test_validate_positive_int_zero_not_allowed(self):
        """测试验证不允许零"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_positive_int(0, "test_field", allow_zero=False)

    def test_validate_positive_int_negative(self):
        """测试验证负数"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_positive_int(-1, "test_field")

    def test_validate_positive_int_invalid_type(self):
        """测试验证无效类型"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_positive_int("abc", "test_field")

    def test_validate_range_valid(self):
        """测试验证有效范围"""
        result = ConfigValidator.validate_range(5, "test_field", min_val=0, max_val=10)
        assert result == 5.0

    def test_validate_range_below_min(self):
        """测试验证低于最小值"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_range(-1, "test_field", min_val=0)

    def test_validate_range_above_max(self):
        """测试验证高于最大值"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_range(11, "test_field", max_val=10)

    def test_validate_path_valid(self):
        """测试验证有效路径"""
        result = ConfigValidator.validate_path("/tmp/test", "test_path")
        assert result == "/tmp/test"

    def test_validate_path_empty(self):
        """测试验证空路径"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_path("", "test_path")

    def test_validate_path_expand_user(self):
        """测试验证展开用户目录"""
        result = ConfigValidator.validate_path("~/test", "test_path")
        assert result.startswith("/") or result[1] == ":"  # Unix 或 Windows
        assert "~" not in result

    def test_validate_choice_valid(self):
        """测试验证有效选项"""
        result = ConfigValidator.validate_choice("option1", "test_field", ["option1", "option2"])
        assert result == "option1"

    def test_validate_choice_invalid(self):
        """测试验证无效选项"""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_choice("option3", "test_field", ["option1", "option2"])

    def test_validate_choice_case_insensitive(self):
        """测试验证选项大小写不敏感"""
        result = ConfigValidator.validate_choice("OPTION1", "test_field", ["option1", "option2"])
        assert result == "option1"


class TestConfigManager:
    """测试配置管理器"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = ConfigManager()
        assert manager.config_dir == "config"

    def test_init_custom_dir(self):
        """测试自定义配置目录"""
        manager = ConfigManager("custom_config")
        assert manager.config_dir == "custom_config"

    def test_get_existing_key(self):
        """测试获取存在的键"""
        manager = ConfigManager()
        manager._config = {"crawl": {"max_depth": 5}}
        result = manager.get("crawl.max_depth")
        assert result == 5

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        manager = ConfigManager()
        manager._config = {"crawl": {}}
        result = manager.get("crawl.nonexistent", "default")
        assert result == "default"

    def test_get_nested_key(self):
        """测试获取嵌套键"""
        manager = ConfigManager()
        manager._config = {"level1": {"level2": {"level3": "value"}}}
        result = manager.get("level1.level2.level3")
        assert result == "value"

    def test_set_key(self):
        """测试设置键"""
        manager = ConfigManager()
        manager._config = {}
        manager.set("key", "value")
        assert manager._config["key"] == "value"

    def test_set_nested_key(self):
        """测试设置嵌套键"""
        manager = ConfigManager()
        manager._config = {}
        manager.set("level1.level2", "value")
        assert manager._config["level1"]["level2"] == "value"

    def test_config_property(self):
        """测试配置属性"""
        manager = ConfigManager()
        manager._config = {"key": "value"}
        config = manager.config
        assert config == {"key": "value"}
        # 确保返回的是副本
        config["new_key"] = "new_value"
        assert "new_key" not in manager._config


class TestConfigManagerValidation:
    """测试配置管理器验证功能"""

    def test_validate_target_url_valid(self):
        """测试验证有效的 target_url"""
        manager = ConfigManager()
        config = {"target_url": "https://example.com"}
        manager.validate(config)

    def test_validate_target_url_invalid(self):
        """测试验证无效的 target_url"""
        manager = ConfigManager()
        config = {"target_url": "invalid-url"}
        with pytest.raises(ValidationError):
            manager.validate(config)

    def test_validate_crawl_max_depth_negative(self):
        """测试验证负数的 max_depth"""
        manager = ConfigManager()
        config = {"crawl": {"max_depth": -1}}
        manager.validate(config)
        # 应该被修复为默认值
        assert config["crawl"]["max_depth"] == 1

    def test_validate_crawl_threads_out_of_range(self):
        """测试验证超出范围的 threads"""
        manager = ConfigManager()
        config = {"crawl": {"threads": 100}}
        manager.validate(config)
        # 应该被修复为默认值
        assert config["crawl"]["threads"] == 4

    def test_validate_logging_level_invalid(self):
        """测试验证无效的日志级别"""
        manager = ConfigManager()
        config = {"logging": {"level": "INVALID"}}
        manager.validate(config)
        # 应该被修复为默认值
        assert config["logging"]["level"] == "INFO"

    def test_validate_i18n_lang_invalid(self):
        """测试验证无效的语言"""
        manager = ConfigManager()
        config = {"i18n": {"lang": "invalid"}}
        manager.validate(config)
        # 应该被修复为默认值
        assert config["i18n"]["lang"] == "en"


class TestConfigManagerMerge:
    """测试配置合并功能"""

    def test_merge_simple(self):
        """测试简单合并"""
        manager = ConfigManager()
        base = {"key1": "value1", "key2": "value2"}
        override = {"key2": "new_value2"}
        result = manager._merge(base, override)
        assert result["key1"] == "value1"
        assert result["key2"] == "new_value2"

    def test_merge_nested(self):
        """测试嵌套合并"""
        manager = ConfigManager()
        base = {"level1": {"key1": "value1", "key2": "value2"}}
        override = {"level1": {"key2": "new_value2"}}
        result = manager._merge(base, override)
        assert result["level1"]["key1"] == "value1"
        assert result["level1"]["key2"] == "new_value2"

    def test_merge_add_new_key(self):
        """测试合并添加新键"""
        manager = ConfigManager()
        base = {"key1": "value1"}
        override = {"key2": "value2"}
        result = manager._merge(base, override)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
