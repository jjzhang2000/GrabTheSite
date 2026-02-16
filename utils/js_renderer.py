"""JavaScript渲染模块

使用Pyppeteer进行无头浏览器渲染：
- 支持动态加载的内容
- 专用渲染线程，避免多线程竞争
- 页面重复使用
"""

import os
import asyncio
import threading
import queue
import time
from logger import setup_logger, _ as _t
from config import CONFIG, USER_AGENT

# JavaScript渲染配置常量
DEFAULT_JS_TIMEOUT = 30  # 默认超时时间（秒）
DEFAULT_SLEEP_TIME = 2   # 渲染后等待时间（秒）
BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-extensions',
    '--disable-plugins',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection',
    '--single-process',
]

# 尝试导入Pyppeteer
try:
    import pyppeteer
    from pyppeteer import launch
    PYPPETEER_AVAILABLE = True
    logger = setup_logger(__name__)
except ImportError:
    PYPPETEER_AVAILABLE = False
    logger = setup_logger(__name__)
    logger.warning(_t("Pyppeteer 未安装，JavaScript 渲染功能将不可用"))


class JSRendererThread:
    """JS渲染专用线程 - 单线程串行处理所有渲染请求"""
    
    def __init__(self, enable=False, timeout=30):
        """初始化渲染线程
        
        Args:
            enable: 是否启用JavaScript渲染
            timeout: 渲染超时时间（秒）
        """
        self.enable = enable and PYPPETEER_AVAILABLE
        self.timeout = timeout
        self.browser = None
        self.page = None
        self._initialized = False
        self._stop_event = threading.Event()
        self._task_queue = queue.Queue()
        self._result_dict = {}  # 存储结果 {task_id: result}
        self._lock = threading.Lock()
        self._thread = None
        self._task_counter = 0
        
    def start(self):
        """启动渲染线程"""
        if not self.enable or self._thread and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="JSRendererThread")
        self._thread.daemon = True
        self._thread.start()
        logger.info(_t("JS渲染线程已启动"))
    
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
        
        # 添加一个停止信号
        self._task_queue.put((None, None, None))
        
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning(_t("JS渲染线程停止超时"))
    
    def _run(self):
        """渲染线程主循环"""
        # 在线程中创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 初始化浏览器
            if not loop.run_until_complete(self._init_browser()):
                logger.error(_t("浏览器初始化失败，渲染线程退出"))
                return
            
            # 处理渲染任务
            while not self._stop_event.is_set():
                try:
                    task_id, url, event = self._task_queue.get(timeout=1)
                    
                    # 停止信号
                    if task_id is None:
                        break
                    
                    # 执行渲染
                    try:
                        html = loop.run_until_complete(self._render_page(url))
                        with self._lock:
                            self._result_dict[task_id] = html
                    except Exception as e:
                        logger.error(_t("渲染失败") + f": {url}, {e}")
                        with self._lock:
                            self._result_dict[task_id] = None
                    finally:
                        # 通知任务完成
                        if event:
                            event.set()
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(_t("渲染线程错误") + f": {e}")
        
        finally:
            # 关闭浏览器
            if self.browser:
                try:
                    loop.run_until_complete(self._close_browser())
                except Exception as e:
                    logger.error(_t("关闭浏览器失败") + f": {e}")
            
            loop.close()
            logger.info(_t("JS渲染线程已退出"))
    
    async def _init_browser(self):
        """在线程中初始化浏览器"""
        try:
            logger.info(_t("渲染线程正在启动浏览器..."))
            self.browser = await launch(
                headless=True,
                args=BROWSER_ARGS,
                timeout=self.timeout * 1000,
            )
            
            self.page = await self.browser.newPage()
            await self.page.setUserAgent(USER_AGENT)
            await self.page.setDefaultNavigationTimeout(self.timeout * 1000)
            
            await self.page.setRequestInterception(True)
            self.page.on('request', lambda req: asyncio.create_task(self._intercept_request(req)))
            
            self._initialized = True
            logger.info(_t("浏览器初始化成功，页面实例: ") + f"{id(self.page)}")
            return True
        except Exception as e:
            logger.error(_t("浏览器初始化失败") + f": {e}")
            return False
    
    async def _intercept_request(self, request):
        """拦截请求"""
        resource_type = request.resourceType
        if resource_type in ['image', 'font', 'media', 'stylesheet']:
            await request.abort()
        else:
            await request.continue_()
    
    async def _render_page(self, url):
        """渲染单个页面"""
        if not self.page:
            return None
        
        # 清除状态
        await self.page.goto('about:blank', waitUntil='networkidle0', timeout=5000)
        
        # 导航到目标
        await self.page.goto(url, waitUntil='networkidle2')
        
        # 等待动态内容
        await asyncio.sleep(DEFAULT_SLEEP_TIME)
        
        # 获取内容
        html = await self.page.content()
        
        logger.info(_t("页面渲染成功") + f": {url}")
        return html
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self.page:
            try:
                await self.page.close()
            except:
                pass
        
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        
        logger.info(_t("浏览器已关闭"))
    
    def render_page(self, url, timeout=60):
        """提交渲染任务并等待结果（线程安全）
        
        Args:
            url: 要渲染的URL
            timeout: 等待超时时间
            
        Returns:
            str: HTML内容，失败返回None
        """
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
