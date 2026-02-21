# 插件系统

## 插件系统简介

GrabTheSite 提供了一个灵活的插件系统，允许用户通过插件扩展工具的功能。插件系统基于钩子机制，在抓取过程的不同阶段触发相应的钩子方法，使插件能够介入抓取流程并执行自定义逻辑。

## 插件目录结构

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

## 插件配置

插件系统**不需要在配置文件中配置**。插件通过以下方式管理：

1. **自动发现**：插件系统自动发现并加载 `plugins/` 目录下的所有插件
2. **默认启用**：所有发现的插件默认都会被启用
3. **模块名识别**：插件通过目录名（模块名）进行识别

### 插件启用/禁用机制

当前实现中：
- **所有发现的插件默认启用** - 无需配置即可使用
- 插件通过 `PluginManager.enable_plugins(plugin_config)` 方法控制启用状态
- 如果传入 `plugin_config=None`，则启用所有插件（向后兼容模式）
- 如果传入具体的配置字典 `{plugin_name: True/False}`，则只启用指定为 `True` 的插件

### 程序化控制插件

```python
from utils.plugin_manager import PluginManager

# 创建插件管理器
plugin_manager = PluginManager(config)

# 发现插件
plugin_manager.discover_plugins()

# 加载插件
plugin_manager.load_plugins()

# 启用所有插件（默认行为）
plugin_manager.enable_all_plugins()

# 或通过配置选择性启用
plugin_config = {
    'save_plugin': True,      # 启用保存插件
    'my_plugin': False        # 禁用我的插件
}
plugin_manager.enable_plugins(plugin_config)
```

## 创建插件

要创建一个插件，需要按照以下步骤操作：

1. 在 `plugins/` 目录下创建一个新的目录，作为插件的名称
2. 在该目录下创建 `__init__.py` 文件
3. 在 `__init__.py` 文件中实现插件类，继承自 `Plugin` 基类
4. 实现需要的钩子方法

## 插件 API

插件系统提供了以下钩子方法，插件可以根据需要实现这些方法：

- `on_init(self, config)`: 插件初始化时调用
- `on_crawl_start(self, url, output_dir)`: 抓取开始时调用
- `on_page_crawled(self, url, local_path, content)`: 页面抓取完成时调用
- `on_crawl_end(self, crawled_urls)`: 抓取结束时调用
- `on_error(self, url, error)`: 抓取过程中发生错误时调用

## 示例插件

### 1. 页面计数器插件

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

### 2. 保存插件

保存插件是一个核心插件，负责将抓取的页面保存到磁盘：

```python
from utils.plugin_manager import Plugin

class SavePlugin(Plugin):
    """保存插件，负责保存抓取的页面到磁盘"""
    
    # 插件名称
    name = "Save Plugin"
    
    # 插件描述
    description = "负责保存抓取的页面到磁盘的插件"
    
    def __init__(self, config=None):
        """初始化插件
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.target_url = None
        self.output_dir = None
        self.static_resources = None
        self.saved_files = []
    
    def on_init(self):
        """插件初始化时调用"""
        super().on_init()
        self.logger.info("保存插件初始化完成")
    
    def on_crawl_end(self, pages):
        """抓取结束时调用，准备保存参数
        
        Args:
            pages: 抓取的页面字典
        """
        self.logger.info(f"准备保存 {len(pages)} 个页面")
    
    def on_save_start(self, saver_data):
        """保存开始时调用
        
        Args:
            saver_data: 保存器数据，包含target_url、output_dir和static_resources
        """
        self.target_url = saver_data.get('target_url')
        self.output_dir = saver_data.get('output_dir')
        self.static_resources = saver_data.get('static_resources', set())
        
        if self.target_url and self.output_dir:
            # 提取起始目录路径
            parsed_target = urlparse(self.target_url)
            self.target_directory = parsed_target.path
            # 确保路径以/结尾
            if not self.target_directory.endswith('/'):
                self.target_directory += '/'
            self.logger.info("保存插件准备就绪")
        else:
            self.logger.error("保存插件初始化失败：缺少必要参数")
    
    def save_site(self, pages):
        """保存抓取的页面到磁盘
        
        Args:
            pages: 暂存的页面内容，键为URL，值为页面内容
        """
        # 统一处理所有页面的链接
        self.logger.info(f"开始统一处理链接，共 {len(pages)} 个页面")
        processed_pages = self._process_all_links(pages)
        
        # 将处理后的页面保存到磁盘
        self.logger.info(f"开始保存页面到磁盘，共 {len(processed_pages)} 个页面")
        saved_count = self._save_pages(processed_pages)
        
        self.logger.info(f"保存完成，共保存 {saved_count} 个页面")
        return self.saved_files

plugin = SavePlugin()
```

## 插件开发指南

1. **插件命名**：插件目录名应该使用小写字母和下划线，避免使用特殊字符
2. **插件结构**：每个插件应该是一个独立的Python包，包含 `__init__.py` 文件
3. **钩子实现**：插件可以选择性地实现需要的钩子方法，不需要实现所有方法
4. **插件注册**：插件会被自动发现和注册，不需要手动注册
5. **配置管理**：插件可以通过 `on_init` 方法获取全局配置
6. **资源管理**：插件应该自行管理其使用的资源，确保在抓取结束时释放

## 启用和禁用插件

当前版本插件系统**自动启用所有发现的插件**，暂不支持通过命令行参数或配置文件控制。

如需选择性启用/禁用插件，请参考上文「程序化控制插件」部分的代码示例。

## 保存插件的使用

保存插件（Save Plugin）是一个核心插件，负责将抓取的页面保存到磁盘。使用方法如下：

1. **默认使用**：保存插件会自动被插件系统发现和启用，无需额外配置
2. **强制下载**：使用 `--force-download` 参数强制重新下载页面，以便测试保存功能

例如：
```bash
python grab_the_site.py --url https://example.com --force-download
```

## 保存插件的工作原理

1. **初始化**：插件系统初始化时，保存插件会被发现和加载
2. **准备**：抓取结束后，保存插件会接收保存参数，包括目标URL、输出目录和静态资源
3. **处理**：保存插件会处理页面链接，将其转换为本地路径
4. **保存**：保存插件会将处理后的页面保存到磁盘，创建必要的目录结构
5. **完成**：保存完成后，保存插件会返回保存的文件列表

通过将保存功能重构为插件形式，我们获得了更好的模块化和可扩展性，便于未来的维护和扩展。
