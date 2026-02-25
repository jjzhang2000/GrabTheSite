"""JavaScript渲染模块 - Playwright版本

使用 Playwright 进行无头浏览器渲染：
- 比 Pyppeteer 更稳定的线程管理
- 自动资源清理
- 更好的跨平台支持
"""

import os
import threading
import queue
import time
from logger import setup_logger, _ as _t
from config import USER_AGENT

# 尝试导入 Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    logger = setup_logger(__name__)
    logger.info(_t("Playwright 已加载"))
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger = setup_logger(__name__)
    logger.warning(_t("Playwright 未安装，JavaScript 渲染功能将不可用"))
    logger.info(_t("安装命令: pip install playwright && playwright install chromium"))


class JSRendererThread:
    """JS渲染专用线程 - 使用 Playwright"""
    
    def __init__(self, enable=False, timeout=30):
        """初始化渲染线程
        
        Args:
            enable: 是否启用JavaScript渲染
            timeout: 渲染超时时间（秒）
        """
        self.enable = enable and PLAYWRIGHT_AVAILABLE
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.page = None
        self._initialized = False
        self._stop_event = threading.Event()
        self._task_queue = queue.Queue()
        self._result_dict = {}
        self._lock = threading.Lock()
        self._thread = None
        self._task_counter = 0
        self._channel = None  # 保存当前使用的浏览器 channel
        
    def start(self):
        """启动渲染线程"""
        if not self.enable or (self._thread and self._thread.is_alive()):
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="JSRendererThread")
        self._thread.daemon = True
        self._thread.start()
        
        # 等待初始化完成或失败
        import time
        init_timeout = 60  # 最多等待60秒
        start_time = time.time()
        while time.time() - start_time < init_timeout:
            if self._initialized:
                logger.info(_t("JS渲染线程已启动(Playwright)"))
                return
            if not self._thread.is_alive():
                # 线程已退出，说明初始化失败
                logger.error(_t("JS渲染线程启动失败，将禁用JavaScript渲染"))
                self.enable = False
                return
            time.sleep(0.1)
        
        # 超时
        logger.error(_t("JS渲染线程启动超时，将禁用JavaScript渲染"))
        self.stop(timeout=5)
        self.enable = False
    
    def stop(self, timeout=30):
        """停止渲染线程"""
        if not self._thread or not self._thread.is_alive():
            return
        
        logger.info(_t("正在停止JS渲染线程..."))
        self._stop_event.set()
        
        # 清空队列
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break
        
        # 添加停止信号
        self._task_queue.put((None, None, None))
        
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning(_t("JS渲染线程停止超时"))
    
    def _find_system_browser(self, p):
        """查找系统中已安装的浏览器

        支持 Windows、macOS 和 Linux 系统。

        Returns:
            tuple: (browser_type, channel, executable_path) 或 None
        """
        import platform
        system = platform.system()

        # 定义不同系统的浏览器路径
        browsers = []

        if system == "Windows":
            browsers = [
                ("chromium", "msedge", [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
                ]),
                ("chromium", "chrome", [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                ]),
            ]
        elif system == "Darwin":  # macOS
            browsers = [
                ("chromium", "msedge", [
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                    os.path.expanduser("~/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                ]),
                ("chromium", "chrome", [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                ]),
            ]
        elif system == "Linux":
            browsers = [
                ("chromium", "chrome", [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                    "/snap/bin/chromium",
                ]),
                ("chromium", "msedge", [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable",
                ]),
            ]

        # 查找可用的浏览器
        for browser_type, channel, paths in browsers:
            for path in paths:
                if os.path.exists(path):
                    logger.info(_t(f"检测到 {channel}: ") + path)
                    return (browser_type, channel, path)

        logger.warning(_t(f"未在 {system} 系统检测到支持的浏览器"))
        return None
    
    def _find_next_browser(self, p, last_channel):
        """查找下一个可用的浏览器（排除已尝试过的）
        
        Args:
            p: Playwright 实例
            last_channel: 上次尝试的浏览器 channel
            
        Returns:
            tuple: (browser_type, channel, executable_path) 或 None
        """
        import platform
        system = platform.system()
        
        # 定义不同系统的浏览器路径（排除已尝试过的）
        browsers = []
        
        if system == "Windows":
            if last_channel != "chrome":
                browsers.append(("chromium", "chrome", [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                ]))
            if last_channel != "msedge":
                browsers.append(("chromium", "msedge", [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
                ]))
        elif system == "Darwin":  # macOS
            if last_channel != "chrome":
                browsers.append(("chromium", "chrome", [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                ]))
            if last_channel != "msedge":
                browsers.append(("chromium", "msedge", [
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                    os.path.expanduser("~/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                ]))
        elif system == "Linux":
            if last_channel != "chrome":
                browsers.append(("chromium", "chrome", [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                    "/snap/bin/chromium",
                ]))
            if last_channel != "msedge":
                browsers.append(("chromium", "msedge", [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable",
                ]))
        
        # 查找可用的浏览器
        for browser_type, channel, paths in browsers:
            for path in paths:
                if os.path.exists(path):
                    logger.info(_t(f"检测到备用浏览器: ") + f"{channel} ({path})")
                    return (browser_type, channel, path)
        
        logger.warning(_t("没有其他可用的系统浏览器"))
        return None
    
    def _run(self):
        """渲染线程主循环"""
        try:
            # Playwright 使用同步 API
            with sync_playwright() as p:
                self.playwright = p
                
                # 首先尝试使用系统中已安装的浏览器
                browser_info = self._find_system_browser(p)
                browser_launched = False
                
                # 尝试启动找到的系统浏览器
                while browser_info and not browser_launched:
                    browser_type, channel, executable_path = browser_info
                    self._channel = channel  # 保存 channel 以便重新启动时使用
                    logger.info(_t("正在启动系统浏览器(Playwright)...") + f" [{channel}]")
                    try:
                        self.browser = p.chromium.launch(
                            headless=True,
                            channel=channel,  # 使用系统浏览器
                            args=[
                                '--disable-gpu',
                                '--disable-dev-shm-usage',
                                '--disable-setuid-sandbox',
                                '--no-sandbox',
                                '--single-process',
                                '--disable-extensions',
                                '--disable-plugins',
                            ]
                        )
                        logger.info(_t("使用系统浏览器: ") + channel)
                        browser_launched = True
                    except Exception as e:
                        logger.warning(_t("启动系统浏览器失败") + f" [{channel}]: {str(e)}")
                        # 尝试查找其他浏览器
                        browser_info = self._find_next_browser(p, channel)
                
                # 如果没有系统浏览器或所有系统浏览器都启动失败，尝试使用 Playwright 内置浏览器
                if not browser_launched:
                    # 检查 Playwright 内置浏览器是否已安装
                    try:
                        browser_path = p.chromium.executable_path
                        if not browser_path or not os.path.exists(browser_path):
                            logger.error(_t("=" * 60))
                            logger.error(_t("未检测到系统浏览器，且 Playwright 内置浏览器未安装！"))
                            logger.error(_t("请安装以下任一浏览器:"))
                            logger.error(_t("  1. Microsoft Edge (推荐)") )
                            logger.error(_t("  2. Google Chrome"))
                            logger.error(_t("或安装 Playwright 内置浏览器:"))
                            logger.error(_t("    playwright install chromium"))
                            logger.error(_t("=" * 60))
                            return
                    except Exception as check_error:
                        logger.warning(_t("检查浏览器安装状态时出错: ") + str(check_error))
                    
                    logger.info(_t("正在启动Chromium(Playwright)..."))
                    self.browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-gpu',
                            '--disable-dev-shm-usage',
                            '--disable-setuid-sandbox',
                            '--no-sandbox',
                            '--single-process',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                        ]
                    )
                
                # 创建单一页面实例并复用
                logger.info(_t("创建页面实例..."))
                # 等待浏览器完全启动
                time.sleep(1)
                try:
                    self.page = self.browser.new_page(
                        user_agent=USER_AGENT,
                        viewport={'width': 1280, 'height': 720}
                    )
                except Exception as e:
                    logger.error(_t("创建页面实例失败") + f": {e}")
                    # 如果浏览器已关闭，尝试重新启动
                    if "browser has been closed" in str(e).lower() or "target page" in str(e).lower():
                        logger.info(_t("浏览器已关闭，尝试重新启动..."))
                        # 使用保存的 channel 重新启动浏览器
                        launch_options = {
                            'headless': True,
                            'args': [
                                '--disable-gpu',
                                '--disable-dev-shm-usage',
                                '--disable-setuid-sandbox',
                                '--no-sandbox',
                                '--single-process',
                                '--disable-extensions',
                                '--disable-plugins',
                                '--disable-background-timer-throttling',
                                '--disable-backgrounding-occluded-windows',
                                '--disable-renderer-backgrounding',
                            ]
                        }
                        if self._channel:
                            launch_options['channel'] = self._channel
                            logger.info(_t("使用系统浏览器重新启动") + f": {self._channel}")
                        else:
                            logger.info(_t("使用 Playwright 内置浏览器重新启动"))
                        
                        try:
                            self.browser = p.chromium.launch(**launch_options)
                            # 等待浏览器完全启动
                            time.sleep(1)
                            self.page = self.browser.new_page(
                                user_agent=USER_AGENT,
                                viewport={'width': 1280, 'height': 720}
                            )
                        except Exception as relaunch_error:
                            logger.error(_t("重新启动浏览器失败") + f": {relaunch_error}")
                            # 如果重新启动失败，禁用 JS 渲染
                            self.enable = False
                            return
                    else:
                        raise
                
                # 拦截图片等不必要资源
                self.page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}", 
                               lambda route: route.abort())
                
                self._initialized = True
                logger.info(_t("浏览器初始化成功，页面实例: ") + f"{id(self.page)}")
                
                # 处理渲染任务
                while not self._stop_event.is_set():
                    try:
                        task_id, url, event = self._task_queue.get(timeout=1)
                        
                        # 停止信号
                        if task_id is None:
                            break
                        
                        # 执行渲染
                        try:
                            html = self._render_page(url)
                            with self._lock:
                                self._result_dict[task_id] = html
                        except Exception as e:
                            logger.error(_t("渲染失败") + f": {url}, {e}")
                            with self._lock:
                                self._result_dict[task_id] = None
                        finally:
                            if event:
                                event.set()
                            
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(_t("渲染线程错误") + f": {e}")
                
                # 关闭资源
                logger.info(_t("正在关闭浏览器..."))
                if self.page:
                    self.page.close()
                if self.browser:
                    self.browser.close()
                    
        except Exception as e:
            logger.error(_t("渲染线程异常") + f": {e}")
        finally:
            self._initialized = False
            logger.info(_t("JS渲染线程已退出"))
    
    def _render_page(self, url):
        """渲染单个页面"""
        if not self.page:
            return None
        
        # 导航到目标URL
        logger.debug(_t("正在渲染") + f": {url}")
        self.page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
        
        # 等待动态内容加载
        time.sleep(2)
        
        # 获取内容
        html = self.page.content()
        
        logger.info(_t("页面渲染成功") + f": {url}")
        return html
    
    def render_page(self, url, timeout=60):
        """提交渲染任务并等待结果（线程安全）"""
        if not self.enable or not self._thread or not self._thread.is_alive():
            return None
        
        # 生成任务ID
        with self._lock:
            self._task_counter += 1
            task_id = self._task_counter
        
        # 创建完成事件
        event = threading.Event()
        
        # 提交任务
        self._task_queue.put((task_id, url, event))
        
        # 等待完成
        if event.wait(timeout=timeout):
            with self._lock:
                return self._result_dict.pop(task_id, None)
        else:
            logger.warning(_t("渲染超时") + f": {url}")
            with self._lock:
                self._result_dict.pop(task_id, None)
            return None


# 全局单例（延迟初始化）
_js_renderer = None
_js_renderer_lock = threading.Lock()


def get_js_renderer(enable=False, timeout=30, init_timeout=10):
    """获取全局JS渲染器实例

    Args:
        enable: 是否启用JS渲染
        timeout: 渲染超时时间（秒）
        init_timeout: 初始化超时时间（秒）

    Returns:
        JSRendererThread: 渲染器实例，如果初始化失败返回 None
    """
    global _js_renderer

    with _js_renderer_lock:
        if _js_renderer is None and enable:
            renderer = JSRendererThread(enable=True, timeout=timeout)
            renderer.start()

            # 等待初始化完成
            start_time = time.time()
            while time.time() - start_time < init_timeout:
                if renderer._initialized:
                    _js_renderer = renderer
                    logger.info(_t("JS渲染器初始化成功"))
                    break
                if not renderer._thread or not renderer._thread.is_alive():
                    # 线程已终止，初始化失败
                    logger.error(_t("JS渲染器线程异常终止"))
                    break
                time.sleep(0.1)
            else:
                # 初始化超时
                logger.error(_t("JS渲染器初始化超时"))
                renderer.stop(timeout=5)
                return None

        return _js_renderer


def close_js_renderer(timeout=30):
    """关闭全局JS渲染器"""
    global _js_renderer
    
    with _js_renderer_lock:
        if _js_renderer:
            _js_renderer.stop(timeout=timeout)
            _js_renderer = None
