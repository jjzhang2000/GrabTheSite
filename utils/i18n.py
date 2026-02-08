# 国际化模块

import os
import gettext
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)

# 翻译域
DOMAIN = 'grabthesite'

# 翻译文件目录
LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale')

# 确保 locale 目录存在
if not os.path.exists(LOCALE_DIR):
    os.makedirs(LOCALE_DIR)

# 已加载的翻译器缓存
_translators = {}

# 当前语言
_current_lang = 'en'  # 默认语言


def init_i18n(lang='en'):
    """初始化国际化模块
    
    Args:
        lang: 语言代码，如 'en', 'zh_CN' 等
    """
    global _current_lang
    _current_lang = lang
    
    # 尝试加载指定语言的翻译
    if lang not in _translators:
        try:
            # 尝试使用gettext.translation加载
            try:
                # 加载翻译器
                translator = gettext.translation(
                    DOMAIN,
                    localedir=LOCALE_DIR,
                    languages=[lang],
                    fallback=True
                )
                _translators[lang] = translator
                logger.info(f"加载语言: {lang}")
            except Exception as e:
                # 如果加载失败，创建一个简单的翻译器
                logger.warning(f"使用gettext.translation加载语言 {lang} 失败: {e}")
                # 创建一个基于字典的翻译器
                translations = {}
                # 尝试读取.po文件
                po_file = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', f'{DOMAIN}.po')
                if os.path.exists(po_file):
                    try:
                        with open(po_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 简单解析.po文件
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
                        logger.info(f"从.po文件加载翻译: {po_file}")
                    except Exception as e:
                        logger.warning(f"读取.po文件失败: {e}")
                
                # 创建一个基于字典的翻译器
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
                logger.info(f"使用基于字典的翻译器: {lang}")
        except Exception as e:
            logger.warning(f"加载语言 {lang} 失败: {e}")
            # 使用默认翻译器
            if 'en' not in _translators:
                try:
                    translator = gettext.translation(
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
                mo_file = os.path.join(lang_dir, f'{DOMAIN}.mo')
                if os.path.exists(mo_file):
                    available_langs.append(lang)
    
    # 确保英语始终可用
    if 'en' not in available_langs:
        available_langs.append('en')
    
    return available_langs


# 导出常用函数
_ = gettext
N_ = lambda message: message  # 用于标记需要翻译但不立即翻译的消息