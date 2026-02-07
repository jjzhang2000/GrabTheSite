# GrabTheSite

一个 Python 工具，用于将网站抓取并保存到本地，支持离线浏览。

## 项目简介

GrabTheSite 是一个轻量级的网站抓取工具，能够将指定网站的内容下载到本地，并智能处理相关链接，使您可以在离线环境中浏览网站。

## 初始版本原型0

### 功能说明

- 保留原始文件名
- 智能链接处理：
  - 只下载起始目录及其子目录下的内容
  - 对于基础目录之上的链接，保留原始链接
  - 自动转换已下载页面的链接为本地路径
- 日志系统：
  - 支持控制台日志和文件日志
  - 详细的日志输出，包括时间戳、模块名、日志级别等
  - 日志文件自动轮转，防止文件过大
- 排除列表：
  - 支持指定不需要下载的URL及其子目录
- 增量抓取功能：
  - 基于时间戳的增量抓取，不使用状态文件
  - 比较本地文件修改时间与远程服务器的 Last-Modified 头部
  - 只下载比本地文件更新的内容，节省带宽和时间
  - 即使页面本身不需要更新，也会处理页面中的链接，检查链接指向的页面是否需要更新
  - 可通过配置文件或命令行参数启用/禁用
- 站点地图生成：
  - 支持生成 XML 格式的站点地图
  - 支持生成 HTML 格式的站点地图
  - 使用页面标题作为链接文本
  - 使用本地文件路径作为 URL
  - 可通过配置文件或命令行参数启用/禁用
- 高级错误处理：
  - HTTP 请求失败时的自动重试
  - 网络超时的智能处理
  - 服务器错误（5xx）的重试策略
  - 支持自定义重试次数和间隔
  - 支持指数退避算法
  - 可配置的失败处理策略（仅记录、跳过、抛出异常）
- 断点续传功能：
  - 在抓取中断后可以继续之前的抓取
  - 记录已下载的文件，避免重复下载
  - 保存抓取状态，包括已访问的URL和已下载的文件
  - 可通过配置文件或命令行参数启用/禁用
  - 可配置状态文件路径
- JavaScript渲染支持：
  - 使用Pyppeteer支持动态加载的内容
  - 可通过配置文件或命令行参数启用/禁用
  - 可配置渲染超时时间
  - 自动降级：如果渲染失败或未启用，会回退到常规HTTP请求
- 国际化支持：
  - 使用Python标准库gettext实现翻译功能
  - 支持英文和中文语言
  - 可通过配置文件或命令行参数设置语言
  - 提供翻译文件的更新和扩展指南
- 自定义用户代理：
  - 支持通过配置文件或命令行参数设置自定义用户代理
  - 默认使用现代浏览器的用户代理字符串
  - 确保所有HTTP请求和JavaScript渲染都使用配置的用户代理
- 插件系统：
  - 支持通过插件扩展功能
  - 提供丰富的钩子方法，如on_init、on_crawl_start、on_page_crawled、on_crawl_end等
  - 支持插件的发现、加载、注册和管理
  - 可通过配置文件或命令行参数启用/禁用插件系统和指定启用的插件

**注：** 具体配置参数（如目标网站、下载深度、文件数量限制等）请参考配置文件。

### 实现步骤

1. 创建项目基础结构，包括主脚本和目录结构
2. 实现配置管理模块，使用 YAML 配置文件管理参数
3. 开发核心抓取模块，实现网页内容的获取和解析
4. 实现文件下载功能，保存到指定目录并保留原始文件名
5. 添加深度控制和文件数量限制逻辑
6. 实现智能链接处理，只处理起始目录及其子目录下的链接
7. 添加日志系统，支持控制台日志和文件日志
8. 测试完整的抓取流程，确保功能正常
9. 添加错误处理逻辑，提高程序稳定性
10. 实现排除列表功能，跳过指定URL及其子目录的下载
11. 实现增量抓取功能，基于时间戳比较判断是否需要更新
12. 实现站点地图生成功能：
    - 支持生成 XML 格式的站点地图
    - 支持生成 HTML 格式的站点地图
    - 使用页面标题作为链接文本
    - 使用本地文件路径作为 URL
    - 可通过配置文件或命令行参数启用/禁用
13. 实现高级错误处理功能：
    - 创建错误处理模块，提供重试机制和错误处理策略
    - 实现重试装饰器，支持自动重试失败的操作
    - 支持自定义重试次数、间隔和退避策略
    - 集成到抓取和下载模块中，提高稳定性
    - 添加错误处理配置选项到配置文件
14. 实现断点续传功能：
    - 创建状态管理模块，负责状态文件的读写
    - 实现状态文件的保存和加载，包括已访问的URL和已下载的文件
    - 集成到抓取和下载模块中，避免重复下载
    - 添加断点续传配置选项到配置文件
    - 添加断点续传相关的命令行参数
15. 实现JavaScript渲染支持：
    - 创建JavaScript渲染模块，使用Pyppeteer进行无头浏览器自动化
    - 实现异步和同步两种渲染方法
    - 集成到爬取逻辑中，在获取页面内容时使用JavaScript渲染
    - 添加渲染状态日志和清理逻辑
    - 添加JavaScript渲染配置选项到配置文件
    - 添加JavaScript渲染相关的命令行参数
    - 实现自动降级机制，当渲染失败时回退到常规HTTP请求
16. 实现国际化支持：
    - 创建国际化模块，使用Python标准库gettext实现翻译功能
    - 创建locale目录结构，存放翻译文件
    - 在配置文件中添加国际化配置选项
    - 在命令行参数中添加语言选择选项
    - 集成翻译功能到主脚本和日志系统
    - 创建英文和中文的翻译文件
    - 实现自动降级机制，当翻译文件不存在时使用默认语言
17. 实现自定义用户代理：
    - 在命令行参数中添加--user-agent选项，允许用户指定自定义用户代理
    - 更新配置处理逻辑，确保命令行参数优先级高于配置文件
    - 修改爬取代码，使用配置中的USER_AGENT常量，而不是硬编码的用户代理
    - 确保JavaScript渲染器也使用配置的用户代理
    - 在主脚本中添加显示用户代理配置的日志
    - 在README.md文件中添加自定义用户代理的说明
18. 实现插件系统：
    - 创建plugins目录结构，用于存放插件
    - 创建utils/plugin_manager.py文件，实现插件管理器
    - 定义Plugin基类，作为所有插件的父类
    - 提供常用的钩子方法，如on_init、on_crawl_start、on_page_crawled、on_crawl_end等
    - 在config/default.yaml中添加插件系统配置
    - 在config.py中添加PLUGIN_CONFIG导出
    - 在grab_the_site.py中添加插件相关的命令行参数
    - 在grab_the_site.py中初始化插件系统并集成到代码中
    - 修改crawler/crawl_site.py文件，添加对插件钩子的调用
    - 创建示例插件，展示插件的基本结构和使用方法
    - 在README.md文件中添加插件系统的说明和开发指南

### 注意事项

- 支持通过命令行参数或 YAML 配置文件管理配置参数
- 命令行参数优先级高于配置文件
- 仅支持抓取指定网站
- 只下载起始目录及其子目录下的内容，基础目录之上的链接将保留原始状态

### JavaScript渲染注意事项

- **首次使用需要安装Chrome**：Pyppeteer首次运行时会自动下载Chrome浏览器，可能需要一些时间
- **性能影响**：JavaScript渲染会增加爬取时间和资源消耗，建议仅在必要时启用
- **网络要求**：渲染过程需要稳定的网络连接，尤其是首次下载Chrome时
- **内存使用**：无头浏览器会占用一定内存，对于大型网站可能需要更多资源
- **自动降级**：如果JavaScript渲染失败或未启用，会自动回退到常规HTTP请求

## 配置文件支持

### 配置文件结构

项目使用 YAML 格式的配置文件，位于 `config/` 目录下：

- **config/default.yaml** - 默认配置文件，包含所有默认配置项
- **config/config.yaml** - 用户配置文件，用于覆盖默认配置

### 配置项说明

#### JavaScript渲染配置

```yaml
# JavaScript渲染配置
js_rendering:
  enable: false         # 是否启用JavaScript渲染
  timeout: 30           # 渲染超时时间（秒）
```

#### 国际化配置

```yaml
# 国际化配置
i18n:
  lang: "en"            # 默认语言代码
  available_langs:      # 可用语言列表
    - "en"
    - "zh_CN"
```

详见 `config/default.yaml` 文件

### 配置优先级

1. **命令行参数** - 最高优先级
2. **用户配置文件** (`config/config.yaml`) - 中等优先级
3. **默认配置文件** (`config/default.yaml`) - 低优先级
4. **内置默认配置** - 最低优先级，作为备用（当配置文件不存在时使用）

### 如何修改配置

1. 复制 `config/config.yaml` 文件（如果不存在）
2. 编辑 `config/config.yaml` 文件，取消注释并修改需要的配置项
3. 保存文件并重新运行程序

### 注意事项

- 已取消硬编码配置，所有配置均通过 YAML 文件管理
- 当配置文件不存在或加载失败时，使用内置默认配置作为备用
- 不需要修改的配置项可以保持注释状态，将使用默认值
- 配置文件格式必须是有效的 YAML 格式
- 配置项的值必须符合预期类型（如深度和文件数量必须为整数）

## 命令行参数支持

### 可用参数

| 参数 | 简写 | 类型 | 描述 |
|------|------|------|------|
| `--url` | `-u` | 字符串 | 目标网站 URL |
| `--depth` | `-d` | 整数 | 最大抓取深度 |
| `--max-files` | `-m` | 整数 | 最大文件数量 |
| `--output` | `-o` | 字符串 | 输出目录 |
| `--delay` | `-t` | 浮点数 | 请求间隔（秒） |
| `--no-random-delay` | | 布尔值 | 禁用随机延迟 |
| `--threads` | `-p` | 整数 | 线程数 |
| `--sitemap` | | 布尔值 | 生成站点地图 |
| `--no-sitemap` | | 布尔值 | 不生成站点地图 |
| `--html-sitemap` | | 布尔值 | 生成 HTML 格式的站点地图 |
| `--no-html-sitemap` | | 布尔值 | 不生成 HTML 格式的站点地图 |
| `--resume` | | 布尔值 | 启用断点续传 |
| `--no-resume` | | 布尔值 | 禁用断点续传 |
| `--state-file` | | 字符串 | 状态文件路径 |
| `--incremental` | `-i` | 布尔值 | 启用增量抓取 |
| `--no-incremental` | | 布尔值 | 禁用增量抓取 |
| `--js-rendering` | | 布尔值 | 启用JavaScript渲染 |
| `--no-js-rendering` | | 布尔值 | 禁用JavaScript渲染 |
| `--js-timeout` | | 整数 | JavaScript渲染超时时间（秒） |
| `--lang` | | 字符串 | 语言代码，如 'en', 'zh_CN' 等 |
| `--user-agent` | | 字符串 | 自定义用户代理字符串 |
| `--plugins` | | 字符串 | 启用的插件列表，逗号分隔 |
| `--no-plugins` | | 布尔值 | 禁用插件系统 |

### 使用示例

#### 1. 基本使用（使用配置文件中的默认值）

```bash
python grab_the_site.py
```

#### 2. 指定目标 URL

```bash
python grab_the_site.py --url https://example.com
```

#### 3. 指定抓取深度和最大文件数

```bash
python grab_the_site.py --depth 2 --max-files 50
```

#### 4. 指定输出目录

```bash
python grab_the_site.py --output my_site
```

#### 5. 组合使用所有参数

```bash
python grab_the_site.py --url https://example.com --depth 3 --max-files 100 --output example_site
```

#### 6. 设置延迟参数

```bash
python grab_the_site.py --url https://example.com --delay 2 --no-random-delay
```

这将设置固定的 2 秒延迟，禁用随机延迟功能。

#### 7. 设置线程数

```bash
python grab_the_site.py --url https://example.com --threads 8
```

这将使用 8 个线程进行并行抓取，提高抓取速度。

#### 8. 启用增量抓取

```bash
python grab_the_site.py --url https://example.com --incremental
```

这将启用增量抓取功能，只下载比本地文件更新的内容。

#### 9. 禁用增量抓取

```bash
python grab_the_site.py --url https://example.com --no-incremental
```

这将禁用增量抓取功能，强制重新下载所有内容。

#### 10. 启用站点地图生成

```bash
python grab_the_site.py --url https://example.com --sitemap
```

这将启用站点地图生成功能，生成 XML 格式的站点地图。

#### 11. 禁用站点地图生成

```bash
python grab_the_site.py --url https://example.com --no-sitemap
```

这将禁用站点地图生成功能。

#### 12. 启用 HTML 格式的站点地图

```bash
python grab_the_site.py --url https://example.com --html-sitemap
```

这将启用 HTML 格式的站点地图生成功能。

#### 13. 禁用 HTML 格式的站点地图

```bash
python grab_the_site.py --url https://example.com --no-html-sitemap
```

这将禁用 HTML 格式的站点地图生成功能。

#### 14. 启用断点续传

```bash
python grab_the_site.py --url https://example.com --resume
```

这将启用断点续传功能，使用默认的状态文件路径。

#### 15. 禁用断点续传

```bash
python grab_the_site.py --url https://example.com --no-resume
```

这将禁用断点续传功能。

#### 16. 指定状态文件路径

```bash
python grab_the_site.py --url https://example.com --resume --state-file my_state.json
```

这将启用断点续传功能，并使用指定的状态文件路径。

#### 17. 启用JavaScript渲染

```bash
python grab_the_site.py --url https://example.com --js-rendering
```

这将启用JavaScript渲染功能，用于抓取使用JavaScript动态加载内容的网站。

#### 18. 禁用JavaScript渲染

```bash
python grab_the_site.py --url https://example.com --no-js-rendering
```

这将禁用JavaScript渲染功能，使用常规HTTP请求抓取网站。

#### 19. 设置JavaScript渲染超时时间

```bash
python grab_the_site.py --url https://example.com --js-rendering --js-timeout 45
```

这将启用JavaScript渲染功能，并设置渲染超时时间为45秒。

#### 20. 设置语言为英文

```bash
python grab_the_site.py --url https://example.com --lang en
```

这将使用英文作为界面语言。

#### 21. 设置语言为中文

```bash
python grab_the_site.py --url https://example.com --lang zh_CN
```

这将使用中文作为界面语言。

#### 22. 设置自定义用户代理

```bash
python grab_the_site.py --url https://example.com --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
```

这将使用指定的自定义用户代理字符串。

#### 23. 启用插件系统并指定启用的插件

```bash
python grab_the_site.py --url https://example.com --plugins example_plugin
```

这将启用插件系统，并只启用 example_plugin 插件。

#### 24. 禁用插件系统

```bash
python grab_the_site.py --url https://example.com --no-plugins
```

这将禁用插件系统，不加载任何插件。

### 注意事项

- 命令行参数优先级高于配置文件
- 未指定的参数将使用配置文件中的值
- 所有参数均为可选
- 参数值必须符合预期类型（如深度和文件数量必须为整数）

## 插件系统

### 插件系统简介

GrabTheSite 提供了一个灵活的插件系统，允许用户通过插件扩展工具的功能。插件系统基于钩子机制，在抓取过程的不同阶段触发相应的钩子方法，使插件能够介入抓取流程并执行自定义逻辑。

### 插件目录结构

插件系统使用以下目录结构：

```
grab_the_site/
├── plugins/
│   ├── __init__.py
│   └── example_plugin/
│       └── __init__.py
├── utils/
│   └── plugin_manager.py
└── ...
```

- `plugins/` 目录用于存放所有插件
- 每个插件是一个独立的目录，如 `example_plugin/`
- 每个插件目录下必须包含 `__init__.py` 文件，实现插件的核心功能

### 插件配置

插件系统的配置位于 `config/default.yaml` 文件中：

```yaml
# 插件系统配置
plugins:
  enable: true             # 是否启用插件系统
  enabled_plugins: []      # 启用的插件列表，为空时启用所有发现的插件
```

### 创建插件

要创建一个插件，需要按照以下步骤操作：

1. 在 `plugins/` 目录下创建一个新的目录，作为插件的名称
2. 在该目录下创建 `__init__.py` 文件
3. 在 `__init__.py` 文件中实现插件类，继承自 `Plugin` 基类
4. 实现需要的钩子方法

### 插件 API

插件系统提供了以下钩子方法，插件可以根据需要实现这些方法：

- `on_init(self, config)`: 插件初始化时调用
- `on_crawl_start(self, url, output_dir)`: 抓取开始时调用
- `on_page_crawled(self, url, local_path, content)`: 页面抓取完成时调用
- `on_crawl_end(self, crawled_urls)`: 抓取结束时调用
- `on_error(self, url, error)`: 抓取过程中发生错误时调用

### 示例插件

以下是一个简单的页面计数器插件示例：

```python
from utils.plugin_manager import Plugin

class PageCounterPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.page_count = 0
    
    def on_init(self, config):
        print("PageCounterPlugin initialized")
    
    def on_crawl_start(self, url, output_dir):
        print(f"Crawling started at {url}")
    
    def on_page_crawled(self, url, local_path, content):
        self.page_count += 1
        print(f"Page crawled: {url} (Total: {self.page_count})")
    
    def on_crawl_end(self, crawled_urls):
        print(f"Crawling finished. Total pages: {self.page_count}")

plugin = PageCounterPlugin()
```

### 插件开发指南

1. **插件命名**：插件目录名应该使用小写字母和下划线，避免使用特殊字符
2. **插件结构**：每个插件应该是一个独立的Python包，包含 `__init__.py` 文件
3. **钩子实现**：插件可以选择性地实现需要的钩子方法，不需要实现所有方法
4. **插件注册**：插件会被自动发现和注册，不需要手动注册
5. **配置管理**：插件可以通过 `on_init` 方法获取全局配置
6. **资源管理**：插件应该自行管理其使用的资源，确保在抓取结束时释放

### 启用和禁用插件

可以通过以下方式启用或禁用插件：

1. **配置文件**：在 `config/default.yaml` 文件中设置 `plugins.enabled_plugins` 列表
2. **命令行参数**：使用 `--plugins` 参数指定启用的插件，使用 `--no-plugins` 参数禁用插件系统

## 功能规划

1. **命令行参数支持** (已实现)
   - 允许用户通过命令行指定目标URL、深度、文件数量等参数
   - 支持帮助信息和参数验证

2. **配置文件支持** (已实现)
   - 使用YAML配置文件管理参数
   - 支持默认配置和用户自定义配置
   - 配置文件自动加载和合并
   - 取消硬编码配置，完全使用配置文件管理

3. **多线程/多进程支持** (已实现)
   - 实现并行抓取，提高抓取速度
   - 支持线程数配置

4. **断点续传功能** (已实现)
   - 在抓取中断后可以继续之前的抓取
   - 记录已下载的文件，避免重复下载
   - 保存抓取状态，包括已访问的URL和已下载的文件
   - 可通过配置文件或命令行参数启用/禁用
   - 可配置状态文件路径

5. **爬虫延迟设置** (已实现)
   - 支持设置请求间隔，避免对目标服务器造成过大压力
   - 支持随机延迟，模拟真实用户行为

6. **自定义用户代理** (已实现)
    - 支持通过配置文件或命令行参数设置自定义用户代理
    - 默认使用现代浏览器的用户代理字符串
    - 确保所有HTTP请求和JavaScript渲染都使用配置的用户代理

7. **JavaScript渲染支持** (已实现)
   - 使用Pyppeteer支持动态加载的内容
   - 可配置是否启用JavaScript渲染
   - 可配置渲染超时时间
   - 自动降级机制，当渲染失败时回退到常规HTTP请求
   - 支持通过配置文件或命令行参数启用/禁用

8. **高级排除列表**
   - 支持正则表达式匹配
   - 支持包含列表和排除列表

9. **代理支持**
   - 支持HTTP和HTTPS代理
   - 支持代理认证

10. **站点地图生成** (已实现)
    - 生成抓取内容的站点地图
    - 支持XML和HTML格式
    - 使用页面标题作为链接文本
    - 使用本地文件路径作为URL
    - 可通过配置文件或命令行参数启用/禁用

11. **压缩功能**
    - 支持压缩下载的内容，节省空间
    - 支持ZIP、TAR等格式

12. **增量抓取** (已实现)
    - 只抓取更新的内容
    - 基于时间戳的判断，不使用状态文件
    - 比较本地文件修改时间与远程服务器的 Last-Modified 头部

13. **高级错误处理** (已实现)
    - 更完善的错误处理和重试机制
    - 支持自定义重试策略
    - HTTP 请求失败时的自动重试
    - 网络超时的智能处理
    - 服务器错误（5xx）的重试策略
    - 支持自定义重试次数和间隔
    - 支持指数退避算法
    - 可配置的失败处理策略（仅记录、跳过、抛出异常）

14. **自定义文件命名规则**
    - 支持根据用户需求命名文件
    - 支持模板化命名

15. **多格式输出**
    - 支持MHTML、WARC等格式
    - 支持导出为静态网站生成器格式

16. **GUI界面**
    - 开发简单的图形界面
    - 支持拖拽操作和实时预览

17. **插件系统** (已实现)
    - 支持自定义插件扩展功能
    - 提供插件开发API
    - 支持插件的发现、加载、注册和管理
    - 提供丰富的钩子方法

18. **国际化支持** (已实现)
    - 支持英文和中文语言
    - 使用Python标准库gettext实现翻译功能
    - 可通过配置文件或命令行参数设置语言
    - 集成到主脚本和日志系统
    - 实现自动降级机制，当翻译文件不存在时使用默认语言
