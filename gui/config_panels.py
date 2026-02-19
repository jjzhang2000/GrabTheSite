"""配置面板模块

提供GUI配置界面：
- URL输入面板
- 高级配置面板（深度、文件数等）
- 插件配置面板
"""

import os
import tkinter as tk
from tkinter import ttk
import yaml
from utils.i18n import gettext as _, init_i18n, register_language_change_callback, get_current_lang
from config import MAX_DEPTH, MAX_FILES, DELAY, BASE_OUTPUT_DIR, USER_CONFIG_FILE, load_config


def save_config_to_yaml(config):
    """保存配置到config.yaml
    
    Args:
        config: 配置字典，包含 url, depth, max_files 等
    """
    try:
        # 加载现有配置
        existing_config = {}
        if os.path.exists(USER_CONFIG_FILE):
            try:
                with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}
            except Exception:
                existing_config = {}
        
        # 构建新的配置结构
        new_config = existing_config.copy()
        
        # 更新 target_url
        if 'url' in config and config['url']:
            new_config['target_url'] = config['url']
        
        # 更新 crawl 配置
        if 'crawl' not in new_config:
            new_config['crawl'] = {}
        if 'depth' in config:
            new_config['crawl']['max_depth'] = config['depth']
        if 'max_files' in config:
            new_config['crawl']['max_files'] = config['max_files']
        if 'delay' in config:
            new_config['crawl']['delay'] = config['delay']
        if 'no_random_delay' in config:
            new_config['crawl']['random_delay'] = not config['no_random_delay']
        if 'threads' in config:
            new_config['crawl']['threads'] = config['threads']
        if 'user_agent' in config:
            new_config['crawl']['user_agent'] = config['user_agent']
        
        # 更新 output 配置
        if 'output' not in new_config:
            new_config['output'] = {}
        if 'output' in config:
            new_config['output']['base_dir'] = config['output']
        
        # 更新 js_rendering 配置
        if 'js_rendering' not in new_config:
            new_config['js_rendering'] = {}
        if 'js_rendering' in config:
            new_config['js_rendering']['enable'] = config['js_rendering']
        if 'js_timeout' in config:
            new_config['js_rendering']['timeout'] = config['js_timeout']
        
        # 更新 i18n 配置
        if 'i18n' not in new_config:
            new_config['i18n'] = {}
        if 'lang' in config:
            new_config['i18n']['lang'] = config['lang']
        
        # 更新排除URL配置
        if 'exclude_urls' in config:
            new_config['exclude_urls'] = config['exclude_urls']
        
        # 保存到文件
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


class BasicConfigPanel(ttk.Frame):
    """基本配置面板，包含URL、抓取深度、最大文件数和输出目录"""
    
    def __init__(self, parent, config=None):
        """初始化基本配置面板
        
        Args:
            parent: 父窗口
            config: 配置字典，如果为None则从配置文件加载
        """
        super().__init__(parent)
        
        # 获取配置
        if config is None:
            config = load_config()
        
        crawl_config = config.get('crawl', {})
        output_config = config.get('output', {})
        
        # 创建网格布局
        self.grid_columnconfigure(0, weight=0, minsize=80)  # 标签列固定宽度
        self.grid_columnconfigure(1, weight=1)  # 输入框列
        self.grid_columnconfigure(2, weight=0)  # 浏览按钮列
        
        # URL配置
        self.url_label = ttk.Label(self, text=_("目标URL:"))
        self.url_label.grid(row=0, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        initial_url = config.get('target_url', '')
        self.url_var = tk.StringVar(value=initial_url)
        self.url_entry = ttk.Entry(self, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 抓取深度配置
        self.depth_label = ttk.Label(self, text=_("抓取深度:"))
        self.depth_label.grid(row=1, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.depth_var = tk.IntVar(value=crawl_config.get('max_depth', MAX_DEPTH))
        self.depth_spinbox = ttk.Spinbox(self, from_=0, to=10, textvariable=self.depth_var, width=8)
        self.depth_spinbox.grid(row=1, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 最大文件数配置
        self.max_files_label = ttk.Label(self, text=_("最大文件数:"))
        self.max_files_label.grid(row=2, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.max_files_var = tk.IntVar(value=crawl_config.get('max_files', MAX_FILES))
        self.max_files_spinbox = ttk.Spinbox(self, from_=1, to=10000, textvariable=self.max_files_var, width=8)
        self.max_files_spinbox.grid(row=2, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 输出目录配置
        self.output_label = ttk.Label(self, text=_("输出目录:"))
        self.output_label.grid(row=3, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.output_var = tk.StringVar(value=output_config.get('base_dir', BASE_OUTPUT_DIR))
        self.output_entry = ttk.Entry(self, textvariable=self.output_var, width=40)
        self.output_entry.grid(row=3, column=1, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 浏览按钮
        self.browse_button = ttk.Button(self, text=_("浏览..."), command=self._browse_output_dir, width=8)
        self.browse_button.grid(row=3, column=2, sticky=tk.W, padx=3, pady=5)
    
    def _browse_output_dir(self):
        """浏览选择输出目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.output_var.get() or '.')
        if directory:
            self.output_var.set(directory)
    
    def get_config(self):
        """获取基本配置"""
        return {
            "url": self.url_var.get(),
            "depth": self.depth_var.get(),
            "max_files": self.max_files_var.get(),
            "output": self.output_var.get()
        }
    
    def get_url(self):
        """获取URL"""
        return self.url_var.get()


class AdvancedConfigPanel(ttk.Frame):
    """高级配置面板"""
    
    def __init__(self, parent, config=None):
        """初始化高级配置面板
        
        Args:
            parent: 父窗口
            config: 配置字典，如果为None则从配置文件加载
        """
        super().__init__(parent)
        
        # 获取配置
        if config is None:
            config = load_config()
        
        crawl_config = config.get('crawl', {})
        i18n_config = config.get('i18n', {})
        exclude_urls = config.get('exclude_urls', [])
        
        # 创建网格布局 - 第0列是标签，第1列是输入框，第2列是额外选项
        self.grid_columnconfigure(0, weight=0, minsize=100)  # 标签列固定宽度
        self.grid_columnconfigure(1, weight=0)  # 输入框列
        self.grid_columnconfigure(2, weight=1)  # 剩余空间
        
        # 延迟配置 + 无随机延迟（同一行显示）
        self.delay_label = ttk.Label(self, text=_('请求延迟(秒):'))
        self.delay_label.grid(row=0, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        # 延迟输入框（宽度缩小，放在左侧）
        self.delay_var = tk.DoubleVar(value=crawl_config.get('delay', DELAY))
        self.delay_spinbox = ttk.Spinbox(self, from_=0.0, to=10.0, increment=0.1, textvariable=self.delay_var, width=6)
        self.delay_spinbox.grid(row=0, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 无随机延迟复选框（放在同一行右侧）
        random_delay = crawl_config.get('random_delay', True)
        self.no_random_delay_var = tk.BooleanVar(value=not random_delay)
        self.no_random_delay_checkbutton = ttk.Checkbutton(self, text=_('无随机延迟'), variable=self.no_random_delay_var)
        self.no_random_delay_checkbutton.grid(row=0, column=2, sticky=tk.W, padx=3, pady=5)
        
        # 线程数配置
        self.threads_label = ttk.Label(self, text=_('线程数:'))
        self.threads_label.grid(row=1, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.threads_var = tk.IntVar(value=crawl_config.get('threads', 4))
        self.threads_spinbox = ttk.Spinbox(self, from_=1, to=32, textvariable=self.threads_var, width=6)
        self.threads_spinbox.grid(row=1, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 用户代理配置
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.user_agent_label = ttk.Label(self, text=_('用户代理:'))
        self.user_agent_label.grid(row=2, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.user_agent_var = tk.StringVar(value=crawl_config.get('user_agent', default_ua))
        self.user_agent_entry = ttk.Entry(self, textvariable=self.user_agent_var, width=35)
        self.user_agent_entry.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 语言配置
        self.lang_label = ttk.Label(self, text=_('语言:'))
        self.lang_label.grid(row=3, column=0, sticky=tk.W, padx=(5, 3), pady=5)
        
        self.lang_var = tk.StringVar(value=i18n_config.get('lang', 'zh_CN'))
        self.lang_combobox = ttk.Combobox(self, textvariable=self.lang_var, values=['zh_CN', 'en'], width=8)
        self.lang_combobox.grid(row=3, column=1, sticky=tk.W, padx=3, pady=5)
        
        # 强制下载配置（不从配置文件读取，默认为False）
        self.force_download_var = tk.BooleanVar(value=False)
        self.force_download_checkbutton = ttk.Checkbutton(self, text=_('强制下载所有文件'), variable=self.force_download_var)
        self.force_download_checkbutton.grid(row=4, column=0, columnspan=4, sticky=tk.W, padx=(5, 3), pady=5)
        
        # 不要下载URL配置（多行文本框）
        self.exclude_urls_label = ttk.Label(self, text=_('不要下载URL:'))
        self.exclude_urls_label.grid(row=5, column=0, sticky=tk.NW, padx=(5, 3), pady=5)
        
        # 创建多行文本框，每行一个URL或URL片段，支持通配符
        self.exclude_urls_text = tk.Text(self, width=40, height=5, wrap=tk.WORD)
        self.exclude_urls_text.grid(row=5, column=1, columnspan=3, sticky=tk.W+tk.E, padx=3, pady=5)
        
        # 加载已保存的排除URL列表到文本框
        if exclude_urls:
            self.exclude_urls_text.insert("1.0", '\n'.join(exclude_urls))
        
        # 添加提示标签
        self.exclude_urls_hint = ttk.Label(self, text=_('每行一个URL或URL片段，支持通配符(*)'), foreground='gray')
        self.exclude_urls_hint.grid(row=6, column=1, columnspan=3, sticky=tk.W, padx=3, pady=(0, 5))
        
        # 绑定语言选择变化事件
        self.lang_combobox.bind('<<ComboboxSelected>>', self._on_language_changed)
        
        # 注册语言切换回调，用于更新界面文本（必须在所有UI元素初始化完成后）
        register_language_change_callback(self._update_ui_texts)
    
    def _on_language_changed(self, event=None):
        """语言选择改变时触发"""
        new_lang = self.lang_var.get()
        
        # 保存语言配置到 config.yaml
        config = {
            'lang': new_lang
        }
        save_config_to_yaml(config)
        
        # 切换语言
        init_i18n(new_lang)
    
    def _update_ui_texts(self):
        """更新界面文本（语言切换后调用）"""
        # 重新导入gettext以确保使用最新的翻译
        from utils.i18n import gettext as _
        
        # 更新标签文本
        self.delay_label.config(text=_('请求延迟(秒):'))
        self.no_random_delay_checkbutton.config(text=_('无随机延迟'))
        self.threads_label.config(text=_('线程数:'))
        self.lang_label.config(text=_('语言:'))
        self.user_agent_label.config(text=_('用户代理:'))
        self.force_download_checkbutton.config(text=_('强制下载所有文件'))
        self.exclude_urls_label.config(text=_('不要下载URL:'))
        self.exclude_urls_hint.config(text=_('每行一个URL或URL片段，支持通配符(*)'))
    

    
    def _browse_output_dir(self):
        """浏览选择输出目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.output_var.get() or '.')
        if directory:
            self.output_var.set(directory)
    
    def get_config(self):
        """获取所有配置参数（JS渲染相关配置从config.yaml读取，不在GUI中设置）"""
        # 获取排除URL列表（多行文本框内容）
        exclude_urls_text = self.exclude_urls_text.get("1.0", tk.END).strip()
        exclude_urls = [url.strip() for url in exclude_urls_text.split('\n') if url.strip()]
        
        return {
            "delay": self.delay_var.get(),
            "no_random_delay": self.no_random_delay_var.get(),
            "threads": self.threads_var.get(),
            "lang": self.lang_var.get(),
            "user_agent": self.user_agent_var.get(),
            "force_download": self.force_download_var.get(),
            "exclude_urls": exclude_urls,
        }


