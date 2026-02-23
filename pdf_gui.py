#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDFtheSite GUI 应用程序入口

启动 PDFtheSite 的图形界面：
- 加载 PDF 主窗口
- 启用 pdf_plugin
- 禁用 save_plugin
- 启动事件循环
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.pdf_main_window import PdfMainWindow


def main():
    """主函数"""
    # 创建PDF主窗口
    root = PdfMainWindow()
    
    # 启动主事件循环
    root.mainloop()


if __name__ == "__main__":
    main()
