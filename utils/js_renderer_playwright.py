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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
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
        
    def start(self):
        """启动渲染线程"""
        if not self.enable or (self._thread and self._thread.is_alive()):
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="JSRendererThread")
        self._thread.daemon = True
        self._thread.start()
        logger.info(_t("JS渲染线程已启动(Playwright)"))
    
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
    
    def _run(self):
        """渲染线程主循环"""
        try:
            # Playwright 使用同步 API
            with sync_playwright() as p:
                self.playwright = p
                
                # 启动浏览器 - 使用 chromium，限制资源使用
                logger.info(_t("正在启动Chromium(Playwright)..."))
                self.browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox',
                        '--single-process',  # 单进程模式
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                    ]
                )
                
                # 创建单一页面实例并复用
                logger.info(_t("创建页面实例..."))
                self.page = self.browser.new_page(
                    user_agent=USER_AGENT,
                    viewport={'width': 1280, 'height': 720}
                )
                
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


def get_js_renderer(enable=False, timeout=30):
    """获取全局JS渲染器实例"""
    global _js_renderer
    
    with _js_renderer_lock:
        if _js_renderer is None and enable:
            _js_renderer = JSRendererThread(enable=True, timeout=timeout)
            _js_renderer.start()
        
        return _js_renderer


def close_js_renderer(timeout=30):
    """关闭全局JS渲染器"""
    global _js_renderer
    
    with _js_renderer_lock:
        if _js_renderer:
            _js_renderer.stop(timeout=timeout)
            _js_renderer = None
