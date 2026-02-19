"""国际化模块

使用Python标准库gettext实现多语言支持：
- 支持英文和中文
- 自动降级到默认语言
- 提供翻译函数 gettext
"""

import os
import gettext as gettext_module
from logger import setup_logger, _ as _t

# 获取 logger 实例
logger = setup_logger(__name__)

# 翻译域
DOMAIN = 'grabthesite'

# 翻译文件目录
LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale')

# 确保 locale 目录存在
if not os.path.exists(LOCALE_DIR):
    os.makedirs(LOCALE_DIR)

# 翻译器缓存和当前语言设置
_translators = {}
_current_lang = 'en'

# 语言切换回调列表
_on_language_changed_callbacks = []


def register_language_change_callback(callback):
    """注册语言切换回调函数
    
    Args:
        callback: 回调函数，无参数
    """
    if callback not in _on_language_changed_callbacks:
        _on_language_changed_callbacks.append(callback)


def unregister_language_change_callback(callback):
    """取消注册语言切换回调函数
    
    Args:
        callback: 回调函数
    """
    if callback in _on_language_changed_callbacks:
        _on_language_changed_callbacks.remove(callback)


def _notify_language_changed():
    """通知所有注册的回调函数语言已切换"""
    for callback in _on_language_changed_callbacks:
        try:
            callback()
        except Exception as e:
            logger.warning(_t("语言切换回调执行失败") + f": {e}")


def init_i18n(lang='en'):
    """初始化国际化模块
    
    Args:
        lang: 语言代码，如 'en', 'zh_CN' 等
    """
    global _current_lang
    _current_lang = lang
    
    if lang not in _translators:
        # 首先检查是否存在.mo文件
        mo_file = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', f'{DOMAIN}.mo')
        po_file = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', f'{DOMAIN}.po')
        
        if os.path.exists(mo_file):
            # 使用gettext加载.mo文件
            try:
                translator = gettext_module.translation(
                    DOMAIN,
                    localedir=LOCALE_DIR,
                    languages=[lang],
                    fallback=False
                )
                _translators[lang] = translator
                logger.info(_t("加载语言") + f": {lang} (from .mo)")
            except Exception as e:
                logger.warning(_t("使用gettext.translation加载语言失败") + f" {lang}: {e}")
        elif os.path.exists(po_file):
            # 从.po文件加载翻译
            translations = {}
            try:
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 解析.po文件格式
                lines = content.split('\n')
                msgid = None
                msgstr = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('msgid "'):
                        msgid = line[7:-1]
                        msgstr = None
                    elif line.startswith('msgstr "'):
                        msgstr = line[8:-1]
                        if msgid and msgstr:
                            translations[msgid] = msgstr
                            msgid = None
                            msgstr = None
                logger.info(_t("从.po文件加载翻译") + f": {po_file}")
            except Exception as e:
                logger.warning(_t("读取.po文件失败") + f": {e}")
            
            # 基于字典的翻译器实现
            class DictTranslator:
                def __init__(self, translations):
                    self.translations = translations
                
                def gettext(self, message):
                    return self.translations.get(message, message)
                
                def ngettext(self, singular, plural, n):
                    return self.translations.get(plural if n != 1 else singular, plural if n != 1 else singular)
                
                def install(self):
                    global _
                    _ = self.gettext
            
            translator = DictTranslator(translations)
            _translators[lang] = translator
            logger.info(_t("使用基于字典的翻译器") + f": {lang}")
            # 使用默认翻译器
            if 'en' not in _translators:
                try:
                    translator = gettext_module.translation(
                        DOMAIN,
                        localedir=LOCALE_DIR,
                        languages=['en'],
                        fallback=True
                    )
                    _translators['en'] = translator
                except Exception:
                    # 创建一个空的翻译器
                    class EmptyTranslator:
                        def gettext(self, message):
                            return message
                        
                        def ngettext(self, singular, plural, n):
                            return plural if n != 1 else singular
                        
                        def install(self):
                            global _
                            _ = self.gettext
                    
                    translator = EmptyTranslator()
                    _translators['en'] = translator
            _current_lang = 'en'
    
    # 安装翻译器
    translator = _translators.get(_current_lang, _translators.get('en'))
    if translator:
        translator.install()
    
    # 同时手动安装到 builtins，确保所有模块都能使用
    import builtins
    builtins._ = gettext
    
    # 通知语言已切换
    _notify_language_changed()


def gettext(message):
    """翻译函数
    
    Args:
        message: 要翻译的消息
        
    Returns:
        str: 翻译后的消息
    """
    translator = _translators.get(_current_lang, _translators.get('en'))
    if translator:
        return translator.gettext(message)
    return message


def ngettext(singular, plural, n):
    """复数翻译函数
    
    Args:
        singular: 单数形式的消息
        plural: 复数形式的消息
        n: 数量
        
    Returns:
        str: 翻译后的消息
    """
    translator = _translators.get(_current_lang, _translators.get('en'))
    if translator:
        return translator.ngettext(singular, plural, n)
    return plural if n != 1 else singular


def get_current_lang():
    """获取当前语言
    
    Returns:
        str: 当前语言代码
    """
    return _current_lang


def get_available_languages():
    """获取可用的语言列表
    
    Returns:
        list: 可用的语言代码列表
    """
    available_langs = []
    
    if os.path.exists(LOCALE_DIR):
        for lang in os.listdir(LOCALE_DIR):
            lang_dir = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES')
            if os.path.isdir(lang_dir):
                # 检查.mo文件或.po文件是否存在
                mo_file = os.path.join(lang_dir, f'{DOMAIN}.mo')
                po_file = os.path.join(lang_dir, f'{DOMAIN}.po')
                if os.path.exists(mo_file) or os.path.exists(po_file):
                    available_langs.append(lang)
    
    # 确保英语始终可用
    if 'en' not in available_langs:
        available_langs.append('en')
    
    return available_langs


# 导出常用函数
_ = gettext
N_ = lambda message: message  # 用于标记需要翻译但不立即翻译的消息

# 模块加载时自动初始化默认语言
try:
    init_i18n('en')
except Exception:
    pass  # 如果初始化失败，使用默认的空翻译