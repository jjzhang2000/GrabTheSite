"""日志面板模块

GUI中的日志显示组件：
- 实时显示日志
- 支持滚动查看
- 自动滚动到底部
- 通过GUIHandler与logging系统集成
"""

import logging
import tkinter as tk
from tkinter import ttk



class GUIHandler(logging.Handler):
    """自定义日志处理器，将日志消息发送到GUI"""
    
    def __init__(self, log_panel):
        """初始化处理器
        
        Args:
            log_panel: LogPanel实例，用于显示日志
        """
        super().__init__()
        self.log_panel = log_panel
    
    def emit(self, record):
        """处理日志记录"""
        try:
            msg = self.format(record)
            self.log_panel.add_log(msg)
        except Exception:
            self.handleError(record)


class LogPanel(ttk.Frame):
    """日志面板类，用于显示抓取过程中的日志信息"""
    
    def __init__(self, parent):
        """初始化日志面板
        
        Args:
            parent: 父窗口组件
        """
        super().__init__(parent)
        
        # 创建日志文本框，默认设置为禁用状态，防止用户编辑
        # wrap=tk.WORD 表示自动换行，以单词为单位
        # height=8 设置固定高度为8行
        self.log_text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 添加垂直滚动条，以便在日志过多时可以滚动查看
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.log_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 绑定滚动条和文本框
        self.log_text.config(yscrollcommand=self.scrollbar.set)
        
        # 设置日志文本框的样式
        self._setup_styles()
    
    def _setup_styles(self):
        """设置日志文本框的样式"""
        # 这里可以设置不同级别的日志的颜色
        # 为了简化，这里只设置默认样式
        pass
    
    def add_log(self, message):
        """添加日志消息"""
        # 启用文本框编辑
        self.log_text.config(state=tk.NORMAL)
        
        # 添加日志消息
        self.log_text.insert(tk.END, message + '\n')
        
        # 滚动到底部
        self.log_text.see(tk.END)
        
        # 禁用文本框编辑
        self.log_text.config(state=tk.DISABLED)
    
    def clear_logs(self):
        """清空日志"""
        # 启用文本框编辑
        self.log_text.config(state=tk.NORMAL)
        
        # 清空文本
        self.log_text.delete(1.0, tk.END)
        
        # 禁用文本框编辑
        self.log_text.config(state=tk.DISABLED)
    
    def setup_logger_handler(self, logger_name=None):
        """设置日志处理器，将日志输出到GUI
        
        Args:
            logger_name: logger名称，如果为None则使用根logger
        """
        # 获取logger
        logger = logging.getLogger(logger_name)
        
        # 检查是否已添加GUIHandler
        for handler in logger.handlers:
            if isinstance(handler, GUIHandler):
                return  # 已存在，不再添加
        
        # 创建GUI处理器
        gui_handler = GUIHandler(self)
        gui_handler.setLevel(logging.INFO)
        
        # 设置格式（与文件日志一致）
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        
        # 添加到logger
        logger.addHandler(gui_handler)