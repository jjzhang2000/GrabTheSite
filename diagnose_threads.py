#!/usr/bin/env python3
"""诊断脚本：追踪 dummy 线程来源"""

import threading
import sys
import traceback
import time

# 保存原始 Thread 类
_original_thread = threading.Thread
_original_start = threading.Thread.start

def patched_start(self):
    """拦截线程启动"""
    print(f"\n[THREAD DEBUG] 线程启动: {self.name}")
    print(f"[THREAD DEBUG] 线程类型: {self.__class__.__name__}")
    
    # 打印创建堆栈
    stack = traceback.extract_stack()
    print(f"[THREAD DEBUG] 创建位置:")
    for filename, lineno, name, line in stack[-6:-1]:
        print(f"  {filename}:{lineno} in {name}")
        if line:
            print(f"    {line.strip()}")
    
    return _original_start(self)

# 替换 start 方法
threading.Thread.start = patched_start

# 记录初始线程数
initial_count = threading.active_count()
print(f"[诊断] 初始线程数: {initial_count}")
print(f"[诊断] 启动程序...\n")

# 导入并运行主程序
from grab_gui import main
main()

# 程序结束后统计
print(f"\n[诊断] 程序结束")
print(f"[诊断] 最终线程数: {threading.active_count()}")
print(f"[诊断] 线程列表:")
for t in threading.enumerate():
    print(f"  - {t.name} (daemon={t.daemon}, alive={t.is_alive()})")
