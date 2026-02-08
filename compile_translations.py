#!/usr/bin/env python3
"""编译翻译文件

将 .po 文件编译为 .mo 文件：
- 支持英文和中文
- 自动创建目录结构
- 错误处理和报告
"""

import gettext
import os

def compile_po_file(po_path, mo_path):
    """编译单个 .po 文件为 .mo 文件"""
    if os.path.exists(po_path):
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(mo_path), exist_ok=True)
            gettext.msgfmt(po_path, mo_path)
            print(f'✓ 编译成功: {po_path} -> {mo_path}')
            return True
        except Exception as e:
            print(f'✗ 编译失败: {po_path}, 错误: {e}')
            return False
    else:
        print(f'⚠ 翻译文件不存在，跳过: {po_path}')
        return False

# 定义要编译的翻译文件
translations = [
    ('locale/en/LC_MESSAGES/grabthesite.po', 'locale/en/LC_MESSAGES/grabthesite.mo'),
    ('locale/zh_CN/LC_MESSAGES/grabthesite.po', 'locale/zh_CN/LC_MESSAGES/grabthesite.mo'),
]

# 编译所有翻译文件
success_count = 0
for po_file, mo_file in translations:
    if compile_po_file(po_file, mo_file):
        success_count += 1

print(f'\n翻译文件编译完成！成功: {success_count}/{len(translations)}')
