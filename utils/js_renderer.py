"""JavaScript渲染模块

使用Pyppeteer进行无头浏览器渲染：
- 支持动态加载的内容
- 可配置渲染超时
- 自动降级到常规HTTP请求
"""

import os
import asyncio
from logger import setup_logger
from config import CONFIG, USER_AGENT

# JavaScript渲染配置常量
DEFAULT_JS_TIMEOUT = 30  # 默认超时时间（秒）
DEFAULT_SLEEP_TIME = 2   # 渲染后等待时间（秒）
BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu'
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
    logger.warning("Pyppeteer 未安装，JavaScript 渲染功能将不可用")


class JSRenderer:
    """JavaScript渲染器，用于渲染使用JavaScript动态加载内容的页面"""
    
    def __init__(self, enable=False, timeout=30):
        """初始化JavaScript渲染器
        
        Args:
            enable: 是否启用JavaScript渲染
            timeout: 渲染超时时间（秒）
        """
        self.enable = enable and PYPPETEER_AVAILABLE
        self.timeout = timeout
        self.browser = None
    
    async def initialize(self):
        """初始化浏览器
        
        Returns:
            bool: 是否成功初始化
        """
        if not self.enable:
            return False
        
        try:
            # 启动浏览器
            self.browser = await launch(
                headless=True,
                args=BROWSER_ARGS,
                timeout=self.timeout * 1000
            )
            logger.info("浏览器初始化成功")
            return True
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False
    
    async def render_page(self, url):
        """渲染页面
        
        Args:
            url: 要渲染的页面URL
            
        Returns:
            str: 渲染后的页面HTML内容，如果渲染失败返回None
        """
        if not self.enable or not self.browser:
            return None
        
        try:
            # 创建新页面
            page = await self.browser.newPage()
            
            # 设置用户代理
            await page.setUserAgent(USER_AGENT)
            
            # 设置超时
            await page.setDefaultNavigationTimeout(self.timeout * 1000)
            
            # 导航到URL
            await page.goto(url, waitUntil='networkidle2')
            
            # 等待一段时间，确保所有内容都已加载
            await asyncio.sleep(DEFAULT_SLEEP_TIME)
            
            # 获取页面HTML
            html = await page.content()
            
            # 关闭页面
            await page.close()
            
            logger.info(f"页面渲染成功: {url}")
            return html
        except Exception as e:
            logger.error(f"页面渲染失败: {url}, 错误: {e}")
            try:
                await page.close()
            except:
                pass
            return None
    
    async def close(self):
        """关闭浏览器
        
        Returns:
            bool: 是否成功关闭
        """
        if not self.browser:
            return True
        
        try:
            await self.browser.close()
            logger.info("浏览器关闭成功")
            return True
        except Exception as e:
            logger.error(f"浏览器关闭失败: {e}")
            return False
    
    def render_page_sync(self, url):
        """同步渲染页面
        
        Args:
            url: 要渲染的页面URL
            
        Returns:
            str: 渲染后的页面HTML内容，如果渲染失败返回None
        """
        if not self.enable:
            return None
        
        try:
            # 检查浏览器是否已初始化
            if not self.browser:
                asyncio.get_event_loop().run_until_complete(self.initialize())
            
            # 渲染页面
            html = asyncio.get_event_loop().run_until_complete(self.render_page(url))
            return html
        except Exception as e:
            logger.error(f"同步渲染页面失败: {url}, 错误: {e}")
            return None
    
    def close_sync(self):
        """同步关闭浏览器
        
        Returns:
            bool: 是否成功关闭
        """
        if not self.browser:
            return True
        
        try:
            result = asyncio.get_event_loop().run_until_complete(self.close())
            return result
        except Exception as e:
            logger.error(f"同步关闭浏览器失败: {e}")
            return False


# 创建默认渲染器实例
default_renderer = JSRenderer()
