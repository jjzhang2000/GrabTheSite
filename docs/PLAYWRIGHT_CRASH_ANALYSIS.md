# Playwright 浏览器崩溃问题分析

> 分析日期：2026-02-25
> 问题现象：浏览器反复崩溃并尝试重新启动

---

## 一、问题现象

### 1.1 错误日志

```
2026-02-25 16:43:44 - utils.js_renderer_playwright - INFO - Playwright 已加载
2026-02-25 16:44:00 - utils.js_renderer_playwright - ERROR - 浏览器已关闭，尝试重新启动... [https://www.mir.com.my/rb/photography/hardwares/classics/michaeliu/cameras/nikonf/index.htm]
2026-02-25 16:44:14 - utils.js_renderer_playwright - ERROR - 浏览器已关闭，尝试重新启动... [https://www.mir.com.my/rb/photography/hardwares/classics/nikonf3ver2/index.htm]
2026-02-25 16:44:31 - utils.js_renderer_playwright - ERROR - 浏览器已关闭，尝试重新启动... [http://www.mir.com.my/rb/photography/hardwares/classics/NikonF5/index.htm]
2026-02-25 16:44:44 - utils.js_renderer_playwright - ERROR - 浏览器已关闭，尝试重新启动... [https://www.mir.com.my/rb/photography/hardwares/classics/nikonfeseries/index.htm]
[Logger] 日志资源已清理
```

### 1.2 时间模式分析

| 时间 | 事件 | 间隔 |
|------|------|------|
| 16:43:44 | Playwright 已加载 | - |
| 16:44:00 | 第一个错误 | 16秒 |
| 16:44:14 | 第二个错误 | 14秒 |
| 16:44:31 | 第三个错误 | 17秒 |
| 16:44:44 | 第四个错误 | 13秒 |

**观察**：每个页面处理约 13-17 秒后浏览器崩溃，符合页面加载超时后部分完成的模式。

---

## 二、相关代码位置

### 2.1 错误触发点

文件：`utils/js_renderer_playwright.py`

```python
# 第 432-433 行
if "target page, context or browser has been closed" in error_msg:
    logger.error(_t("浏览器已关闭，尝试重新启动...") + f" [{url}]")
```

### 2.2 浏览器启动参数

```python
# 第 253-261 行，第 291-302 行
args=[
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--disable-setuid-sandbox',
    '--no-sandbox',
    '--single-process',      # ⚠️ 可能的问题参数
    '--disable-extensions',
    '--disable-plugins',
]
```

### 2.3 页面渲染逻辑

```python
# 第 412 行
response = self.page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)

# 第 416-419 行：状态码检查
if response:
    status = response.status
    if status >= 400:
        logger.warning(_t("页面返回错误状态码") + f": {url}, 状态码: {status}")
        return None
```

### 2.4 资源拦截

```python
# 第 358-359 行
self.page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}",
               lambda route: route.abort())
```

---

## 三、问题 URL 分析

### 3.1 URL 列表

| URL | HTTP 状态 |
|-----|----------|
| `https://www.mir.com.my/rb/photography/hardwares/classics/michaeliu/cameras/nikonf/index.htm]` | 404 Not Found |
| `https://www.mir.com.my/rb/photography/hardwares/classics/nikonf3ver2/index.htm]` | 404 Not Found |
| `http://www.mir.com.my/rb/photography/hardwares/classics/NikonF5/index.htm]` | 404 Not Found |
| `https://www.mir.com.my/rb/photography/hardwares/classics/nikonfeseries/index.htm]` | 404 Not Found |

### 3.2 URL 格式异常

**注意**：所有 URL 末尾都有异常字符 `]`

```
正确格式: https://...index.htm
实际格式: https://...index.htm]
```

**可能原因**：
1. 上游 HTML 中的链接格式错误（如 `<a href="url]">`）
2. 链接提取时的解析错误
3. 某些特殊字符未正确处理

---

## 四、根本原因分析

### 4.1 主要原因

#### 原因 1：目标网站返回 404 页面

所有出错的 URL 都返回 **404 Not Found**。虽然代码检查了状态码，但：

- 404 页面可能包含大量 JavaScript
- 可能有无限循环或内存泄漏
- 页面内容可能触发浏览器崩溃

#### 原因 2：`--single-process` 模式

```python
'--single-process'  # 单进程模式
```

**风险**：
- 单进程模式下，页面崩溃会导致整个浏览器崩溃
- 没有进程隔离保护
- 内存问题会直接影响浏览器主进程

#### 原因 3：`wait_until='networkidle'` 与 404 页面

```python
self.page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
```

**风险**：
- 404 页面可能有持续的网络活动（如重试请求、广告脚本）
- `networkidle` 可能永远无法达到，导致超时
- 超时后的浏览器状态可能不稳定

#### 原因 4：资源拦截可能导致页面异常

```python
self.page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}",
               lambda route: route.abort())
```

**风险**：
- 拦截 CSS 可能导致页面布局异常
- 某些 JavaScript 可能依赖这些资源
- 404 页面的错误处理脚本可能因此崩溃

### 4.2 崩溃流程推测

```
1. 浏览器访问 404 URL
2. 服务器返回 404 页面（包含错误处理脚本）
3. 资源拦截导致脚本执行异常
4. 页面 JavaScript 触发内存问题或无限循环
5. 单进程模式下，页面崩溃导致浏览器崩溃
6. 代码检测到 "browser has been closed" 错误
7. 尝试重新启动浏览器
8. 下一个 404 URL 触发相同问题
9. 循环往复
```

---

## 五、解决方案建议

### 5.1 短期修复（推荐优先尝试）

#### 方案 A：移除 `--single-process` 参数

```python
# 修改前
args=[
    '--disable-gpu',
    '--single-process',  # 移除此行
    ...
]

# 修改后
args=[
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    ...
]
```

**效果**：多进程模式可隔离页面崩溃，提高稳定性。

#### 方案 B：在渲染前检查 URL 有效性

```python
def _render_page(self, url, p):
    """渲染单个页面"""
    if not self.page:
        return None

    try:
        # 先用 HEAD 请求检查状态码
        import requests
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code >= 400:
            logger.warning(f"URL 返回错误状态码，跳过渲染: {url}, 状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.debug(f"HEAD 请求失败，继续尝试渲染: {url}, {e}")

    # 继续原有渲染逻辑...
```

#### 方案 C：使用 `domcontentloaded` 替代 `networkidle`

```python
# 修改前
response = self.page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)

# 修改后
response = self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
```

**效果**：不等待网络完全空闲，减少超时风险。

### 5.2 中期优化

#### 方案 D：添加 URL 清理逻辑

```python
def normalize_url(url: str) -> str:
    """清理 URL 中的异常字符"""
    # 移除末尾的特殊字符
    url = url.rstrip('])}>')
    return url
```

#### 方案 E：添加浏览器健康检查

```python
def _check_browser_health(self) -> bool:
    """检查浏览器是否健康"""
    try:
        if not self.browser or not self.browser.is_connected():
            return False
        if not self.page or self.page.is_closed():
            return False
        return True
    except Exception:
        return False
```

#### 方案 F：限制重试次数

```python
def __init__(self, ...):
    ...
    self._crash_count = 0
    self._max_crash_count = 3

def _render_page(self, url, p):
    if self._crash_count >= self._max_crash_count:
        logger.error("浏览器崩溃次数过多，禁用 JS 渲染")
        self.enable = False
        return None
    ...
```

### 5.3 长期改进

1. **使用独立的浏览器进程池**：避免单点故障
2. **实现优雅降级**：JS 渲染失败时自动切换到 HTTP 请求
3. **添加详细的崩溃日志**：记录崩溃时的内存、CPU 状态
4. **考虑使用 Docker 容器**：隔离浏览器进程

---

## 六、测试验证步骤

### 6.1 单独测试问题 URL

```bash
# 使用 curl 测试
curl -I "https://www.mir.com.my/rb/photography/hardwares/classics/michaeliu/cameras/nikonf/index.htm"

# 预期结果：HTTP/1.1 404 Not Found
```

### 6.2 测试浏览器稳定性

```python
# 测试脚本
from playwright.sync_api import sync_playwright

def test_404_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 测试 404 页面
        try:
            response = page.goto(
                "https://www.mir.com.my/rb/photography/hardwares/classics/michaeliu/cameras/nikonf/index.htm",
                wait_until='domcontentloaded',
                timeout=30000
            )
            print(f"状态码: {response.status}")
            print(f"页面内容长度: {len(page.content())}")
        except Exception as e:
            print(f"错误: {e}")

        browser.close()

test_404_page()
```

### 6.3 验证修复效果

1. 应用方案 A（移除 `--single-process`）
2. 运行测试脚本
3. 观察是否仍有崩溃

---

## 七、总结

| 问题 | 严重程度 | 解决难度 |
|------|----------|----------|
| `--single-process` 模式 | 高 | 低（移除参数即可） |
| 404 页面处理 | 中 | 中（需要添加预检查） |
| `networkidle` 等待策略 | 中 | 低（改用 `domcontentloaded`） |
| URL 格式异常 | 低 | 低（添加清理逻辑） |
| 资源拦截 | 低 | 中（需要评估影响） |

**建议优先级**：
1. 移除 `--single-process` 参数（最简单、最有效）
2. 改用 `domcontentloaded` 等待策略
3. 添加 URL 状态码预检查
4. 添加崩溃次数限制

---

## 八、相关文件

- `utils/js_renderer_playwright.py` - JS 渲染器主模块
- `utils/browser_manager.py` - 浏览器管理器
- `crawler/fetcher.py` - 页面获取器
- `docs/CODE_QUALITY_REPORT.md` - 代码质量报告（问题 22、23 相关）
