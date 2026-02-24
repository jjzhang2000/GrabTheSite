"""状态管理器模块单元测试"""

import pytest
import json
import os
import time
from unittest.mock import Mock, patch, mock_open

from utils.state_manager import StateManager


class TestStateManager:
    """测试 StateManager 类"""

    def test_init(self):
        """测试初始化"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            assert manager.state_file == "test_state.json"
            assert "visited_urls" in manager.state
            assert "downloaded_files" in manager.state
            assert "stats" in manager.state

    def test_init_creates_default_state(self):
        """测试初始化创建默认状态"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            assert isinstance(manager.state["visited_urls"], set)
            assert isinstance(manager.state["downloaded_files"], set)
            assert manager.state["stats"]["total_urls"] == 0

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"visited_urls": ["url1"], "downloaded_files": ["file1"], "start_time": 123, "last_save_time": 456, "stats": {"total_urls": 1}}')
    def test_load_state_exists(self, mock_file, mock_exists):
        """测试加载存在的状态文件"""
        mock_exists.return_value = True

        manager = StateManager("test_state.json")

        assert "url1" in manager.state["visited_urls"]
        assert "file1" in manager.state["downloaded_files"]
        assert manager.state["stats"]["total_urls"] == 1

    @patch('os.path.exists')
    def test_load_state_not_exists(self, mock_exists):
        """测试加载不存在的状态文件"""
        mock_exists.return_value = False

        manager = StateManager("test_state.json")

        # 应该使用默认状态
        assert manager.state["visited_urls"] == set()
        assert manager.state["downloaded_files"] == set()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_state(self, mock_file, mock_makedirs, mock_exists):
        """测试保存状态"""
        mock_exists.return_value = True

        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["visited_urls"] = {"https://example.com"}
            result = manager.save_state()

            assert result is True
            # 验证文件写入被调用（json.dump 会多次调用 write）
            assert mock_file().write.called

    def test_add_visited_url(self):
        """测试添加已访问 URL"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.add_visited_url("https://example.com")

            assert "https://example.com" in manager.state["visited_urls"]
            assert manager.state["stats"]["total_urls"] == 1

    def test_add_downloaded_file(self):
        """测试添加已下载文件"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.add_downloaded_file("example.html")

            assert "example.html" in manager.state["downloaded_files"]
            assert manager.state["stats"]["downloaded_files"] == 1

    def test_is_url_visited(self):
        """测试检查 URL 是否已访问"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["visited_urls"] = {"https://example.com"}

            assert manager.is_url_visited("https://example.com") is True
            assert manager.is_url_visited("https://notvisited.com") is False

    @patch('os.path.isfile')
    def test_is_file_downloaded(self, mock_isfile):
        """测试检查文件是否已下载"""
        mock_isfile.return_value = True

        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["downloaded_files"] = {"example.html"}

            assert manager.is_file_downloaded("example.html") is True
            assert manager.is_file_downloaded("notdownloaded.html") is False

    @patch('os.path.isfile')
    def test_is_file_downloaded_file_not_exist(self, mock_isfile):
        """测试文件不存在时返回 False"""
        mock_isfile.return_value = False

        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["downloaded_files"] = {"example.html"}

            # 文件不存在，应该返回 False 并从状态中移除
            assert manager.is_file_downloaded("example.html") is False
            assert "example.html" not in manager.state["downloaded_files"]

    def test_add_failed_url(self):
        """测试添加失败的 URL"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.add_failed_url("https://example.com")
            manager.add_failed_url("https://example2.com")

            assert manager.state["stats"]["failed_urls"] == 2

    def test_get_stats(self):
        """测试获取统计信息"""
        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["stats"]["total_urls"] = 10
            manager.state["stats"]["downloaded_files"] = 5
            manager.state["stats"]["failed_urls"] = 2

            stats = manager.get_stats()

            assert stats["total_urls"] == 10
            assert stats["downloaded_files"] == 5
            assert stats["failed_urls"] == 2

    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_state(self, mock_remove, mock_exists):
        """测试清除状态"""
        mock_exists.return_value = True

        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            manager.state["visited_urls"] = {"https://example.com"}
            manager.state["downloaded_files"] = {"example.html"}
            manager.state["stats"]["total_urls"] = 10

            result = manager.clear_state()

            assert result is True
            assert manager.state["visited_urls"] == set()
            assert manager.state["downloaded_files"] == set()
            assert manager.state["stats"]["total_urls"] == 0
            mock_remove.assert_called_once_with("test_state.json")

    @patch('os.path.exists')
    def test_should_save(self, mock_exists):
        """测试检查是否应该保存状态"""
        mock_exists.return_value = False

        with patch.object(StateManager, 'load_state'):
            manager = StateManager("test_state.json")
            # 刚初始化，不应该保存
            assert manager.should_save(interval=300) is False

            # 修改 last_save_time 为很久以前
            manager.state["last_save_time"] = time.time() - 301
            assert manager.should_save(interval=300) is True

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_state_invalid_json(self, mock_file, mock_exists):
        """测试加载无效的 JSON"""
        mock_exists.return_value = True

        manager = StateManager("test_state.json")

        # 应该使用默认状态
        assert manager.state["visited_urls"] == set()
