# 日志面板模块

import tkinter as tk
from tkinter import ttk
from utils.i18n import gettext as _


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
        self.log_text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
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