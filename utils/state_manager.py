"""状态管理模块

管理抓取状态，支持断点续传：
- 保存已访问的URL
- 保存已下载的文件
- 自动状态保存
"""

import os
import json
import time
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


class StateManager:
    """状态管理器，用于保存和加载抓取状态"""
    
    def __init__(self, state_file):
        """初始化状态管理器
        
        Args:
            state_file: 状态文件路径
        """
        self.state_file = state_file
        self.state = {
            "visited_urls": set(),
            "downloaded_files": set(),
            "start_time": time.time(),
            "last_save_time": time.time(),
            "stats": {
                "total_urls": 0,
                "downloaded_files": 0,
                "failed_urls": 0
            }
        }
        
        self.load_state()
    
    def load_state(self):
        """加载状态文件
        
        Returns:
            bool: 是否成功加载状态文件
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                
                # JSON不支持集合类型，需要转换
                if "visited_urls" in loaded_state:
                    self.state["visited_urls"] = set(loaded_state["visited_urls"])
                if "downloaded_files" in loaded_state:
                    self.state["downloaded_files"] = set(loaded_state["downloaded_files"])
                
                # 恢复其他状态
                if "start_time" in loaded_state:
                    self.state["start_time"] = loaded_state["start_time"]
                if "stats" in loaded_state:
                    self.state["stats"] = loaded_state["stats"]
                
                logger.info(f"成功加载状态文件: {self.state_file}")
                logger.info(f"已访问 URL 数量: {len(self.state['visited_urls'])}")
                logger.info(f"已下载文件数量: {len(self.state['downloaded_files'])}")
                return True
            except (IOError, OSError, json.JSONDecodeError) as e:
                logger.error(f"加载状态文件失败: {e}")
                return False
        return False
    
    def save_state(self):
        """保存状态文件
        
        Returns:
            bool: 是否成功保存状态文件
        """
        try:
            # 创建状态文件目录
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # 转换集合为列表，以便 JSON 序列化
            state_to_save = {
                "visited_urls": list(self.state["visited_urls"]),
                "downloaded_files": list(self.state["downloaded_files"]),
                "start_time": self.state["start_time"],
                "last_save_time": time.time(),
                "stats": self.state["stats"]
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, indent=2, ensure_ascii=False)
            
            self.state["last_save_time"] = state_to_save["last_save_time"]
            logger.info(f"成功保存状态文件: {self.state_file}")
            return True
        except (IOError, OSError, TypeError) as e:
            logger.error(f"保存状态文件失败: {e}")
            return False
    
    def add_visited_url(self, url):
        """添加已访问的 URL
        
        Args:
            url: 已访问的 URL
        """
        self.state["visited_urls"].add(url)
        self.state["stats"]["total_urls"] = len(self.state["visited_urls"])
    
    def add_downloaded_file(self, file_path):
        """添加已下载的文件
        
        Args:
            file_path: 已下载的文件路径
        """
        self.state["downloaded_files"].add(file_path)
        self.state["stats"]["downloaded_files"] = len(self.state["downloaded_files"])
    
    def add_failed_url(self, url):
        """添加失败的 URL
        
        Args:
            url: 失败的 URL
        """
        self.state["stats"]["failed_urls"] += 1
    
    def is_url_visited(self, url):
        """检查 URL 是否已访问
        
        Args:
            url: 要检查的 URL
            
        Returns:
            bool: 是否已访问
        """
        return url in self.state["visited_urls"]
    
    def is_file_downloaded(self, file_path):
        """检查文件是否已下载
        
        Args:
            file_path: 要检查的文件路径
            
        Returns:
            bool: 是否已下载
        """
        return file_path in self.state["downloaded_files"]
    
    def get_stats(self):
        """获取抓取统计信息
        
        Returns:
            dict: 统计信息
        """
        return self.state["stats"]
    
    def clear_state(self):
        """清除状态
        
        Returns:
            bool: 是否成功清除状态
        """
        try:
            self.state = {
                "visited_urls": set(),
                "downloaded_files": set(),
                "start_time": time.time(),
                "last_save_time": time.time(),
                "stats": {
                    "total_urls": 0,
                    "downloaded_files": 0,
                    "failed_urls": 0
                }
            }
            
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            
            logger.info("成功清除状态")
            return True
        except (IOError, OSError) as e:
            logger.error(f"清除状态失败: {e}")
            return False
    
    def should_save(self, interval=300):
        """检查是否应该保存状态
        
        Args:
            interval: 保存间隔（秒）
            
        Returns:
            bool: 是否应该保存状态
        """
        return time.time() - self.state["last_save_time"] > interval
