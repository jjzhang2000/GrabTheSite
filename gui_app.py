#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI应用程序入口
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """主函数"""
    # 创建主窗口
    root = MainWindow()
    
    # 启动主事件循环
    root.mainloop()


if __name__ == "__main__":
    main()