# GrabTheSite

一个 Python 工具，用于将网站抓取并保存到本地，支持离线浏览和 PDF 输出。
项目开发使用 Kimi 2.5，代码审核使用 GLM 5，人工极少干预代码细节。

## 项目简介

GrabTheSite 是一个轻量级的网站抓取工具，能够将指定网站的内容下载到本地，并智能处理相关链接，使您可以在离线环境中浏览网站。同时支持将网站内容生成为 PDF 文件，保留页面结构和书签导航。

## 功能特性

### 核心功能
- **智能链接处理**：只下载起始目录及其子目录下的内容，自动转换已下载页面的链接为本地路径
- **多线程抓取**：支持可配置线程数进行并行抓取，提高下载速度
- **增量抓取**：基于时间戳的增量抓取，只下载比本地文件更新的内容
- **断点续传**：在抓取中断后可以继续之前的抓取，记录已下载的文件

### 输出格式
- **离线浏览**：保存为 HTML 文件，保留原始目录结构，支持本地浏览
- **PDF 输出**：将抓取的网站内容生成 PDF 文件，支持书签导航和页面链接
- **站点地图**：生成 HTML 格式的站点地图，正确反映页面层次结构

### 高级功能
- **JavaScript 渲染**：使用 Playwright 支持动态加载的内容（支持 Windows、macOS、Linux）
- **高级错误处理**：HTTP 请求失败自动重试，支持指数退避算法
- **排除列表**：支持指定不需要下载的 URL 列表，支持通配符模式
- **代理支持**：支持 HTTP 和 HTTPS 代理
- **自定义用户代理**：支持设置自定义用户代理字符串

### 界面与扩展
- **GUI 界面**：使用 tkinter 开发的图形界面，支持实时日志显示
- **插件系统**：支持通过插件扩展功能，提供丰富的钩子方法
- **国际化支持**：支持英文和中文语言
- **日志系统**：支持控制台日志和文件日志，支持日志级别控制

### 代码质量
- **类型注解**：核心模块已添加完整的 Python 类型注解
- **单元测试**：140+ 单元测试覆盖核心功能
- **代码重构**：消除重复代码，提高可维护性
- **线程安全**：修复全局单例模式的线程安全问题

## 快速开始

### 基本使用

```bash
# 抓取网站并保存为 HTML
python grab_the_site.py --url https://example.com

# 生成 PDF 文件
python pdf_the_site.py --url https://example.com
```

### 更多示例

```bash
# 指定抓取深度和输出目录
python grab_the_site.py --url https://example.com --depth 3 --output ./my_site

# 使用多线程和代理
python grab_the_site.py --url https://example.com --threads 8 --proxy http://127.0.0.1:7890

# 启用详细日志
python grab_the_site.py --url https://example.com -v

# 生成指定格式的 PDF
python pdf_the_site.py --url https://example.com --pdf-filename output.pdf --pdf-format A4
```

详见 [命令行参数文档](docs/COMMAND_LINE.md)

## 文档目录

- [命令行参数](docs/COMMAND_LINE.md) - 完整的命令行参数说明和使用示例
- [插件系统](docs/PLUGINS.md) - 插件开发指南和 API 说明
- [GUI 界面](docs/GUI.md) - GUI 界面使用说明
- [PDF 功能](docs/PDF.md) - PDF 输出功能说明
- [PDF GUI](docs/PDF_GUI.md) - PDF 生成 GUI 使用说明
- [功能规划](docs/ROADMAP.md) - 已实现功能和未来计划
- [代码质量报告](docs/CODE_QUALITY_REPORT.md) - 代码审核报告和改进记录

## 系统要求

- Python 3.8+
- Windows / macOS / Linux

## 安装

```bash
# 克隆仓库
git clone https://github.com/jjzhang2000/GrabTheSite.git
cd GrabTheSite

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright（用于 JavaScript 渲染）
playwright install
```

## 配置文件

项目使用 YAML 格式的配置文件：

- **config/default.yaml** - 默认配置文件
- **config/config.yaml** - 用户配置文件（用于覆盖默认配置）

配置优先级：命令行参数 > 用户配置文件 > 默认配置文件

## 代码结构

```
GrabTheSite/
├── cli/                  # CLI 基类模块
├── crawler/              # 抓取模块
│   ├── crawl_site.py     # 主抓取逻辑
│   ├── downloader.py     # 文件下载器
│   ├── fetcher.py        # 页面获取器
│   ├── link_extractor.py # 链接提取器
│   └── url_filter.py     # URL 过滤器
├── config/               # 配置文件目录
├── gui/                  # GUI 界面模块
├── plugins/              # 插件目录
│   ├── save_plugin/      # 保存插件
│   └── pdf_plugin/       # PDF 输出插件
├── utils/                # 工具模块
├── docs/                 # 文档目录
├── tests/                # 测试目录
├── logger.py             # 日志系统
├── config.py             # 配置管理
├── grab_the_site.py      # 命令行主脚本（抓取）
├── pdf_the_site.py       # 命令行主脚本（PDF）
├── grab_gui.py           # GUI 应用程序入口
└── pdf_gui.py            # PDF 生成 GUI 入口
```

## 测试

```bash
# 运行所有单元测试
python -m pytest tests/unit -v

# 运行测试并生成覆盖率报告
python -m pytest tests/unit --cov=. --cov-report=html
```

## 许可证

[LICENSE](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### 最新改进
- ✅ 修复空异常处理问题，提高代码健壮性
- ✅ 移除弃用模块，清理代码库
- ✅ 重构主入口文件，消除重复代码（减少约 355 行）
- ✅ 修复全局单例模式线程安全问题
- ✅ 添加多平台浏览器支持（Windows、macOS、Linux）
- ✅ 添加日志级别控制参数（--verbose、--quiet）
- ✅ 为核心模块添加完整类型注解
- ✅ 删除未使用的导入，优化代码
