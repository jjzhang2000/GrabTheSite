#!/usr/bin/env python3
# 编译翻译文件

import gettext
import os

# 编译英文翻译文件
en_po = os.path.join('locale', 'en', 'LC_MESSAGES', 'grabthesite.po')
en_mo = os.path.join('locale', 'en', 'LC_MESSAGES', 'grabthesite.mo')
gettext.msgfmt(en_po, en_mo)
print(f'编译英文翻译文件: {en_po} -> {en_mo}')

# 编译中文翻译文件
zh_po = os.path.join('locale', 'zh_CN', 'LC_MESSAGES', 'grabthesite.po')
zh_mo = os.path.join('locale', 'zh_CN', 'LC_MESSAGES', 'grabthesite.mo')
gettext.msgfmt(zh_po, zh_mo)
print(f'编译中文翻译文件: {zh_po} -> {zh_mo}')

print('翻译文件编译完成！')
