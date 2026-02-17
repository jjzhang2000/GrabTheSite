# GrabTheSite

一个 Python 工具，用于将网站抓取并保存到本地，支持离线浏览。

## 项目简介

GrabTheSite 是一个轻量级的网站抓取工具，能够将指定网站的内容下载到本地，并智能处理相关链接，使您可以在离线环境中浏览网站。

## 功能特性

- **智能链接处理**：只下载起始目录及其子目录下的内容，自动转换已下载页面的链接为本地路径
- **日志系统**：支持控制台日志和文件日志，详细的日志输出
- **排除列表**：支持指定不需要下载的URL及其子目录
- **增量抓取**：基于时间戳的增量抓取，只下载比本地文件更新的内容
- **站点地图生成**：支持生成 XML 和 HTML 格式的站点地图
- **高级错误处理**：HTTP请求失败自动重试，支持指数退避算法
- **断点续传**：在抓取中断后可以继续之前的抓取
- **JavaScript渲染**：使用Playwright支持动态加载的内容
- **国际化支持**：支持英文和中文语言
- **自定义用户代理**：支持设置自定义用户代理字符串
- **插件系统**：支持通过插件扩展功能

## 快速开始

### 基本使用

```bash
python grab_the_site.py --url https://example.com
```

### 更多示例

详见 [命令行参数文档](docs/COMMAND_LINE.md)

## 文档目录

- [命令行参数](docs/COMMAND_LINE.md) - 完整的命令行参数说明和使用示例
- [插件系统](docs/PLUGINS.md) - 插件开发指南和API说明
- [GUI界面](docs/GUI.md) - GUI界面使用说明
- [功能规划](docs/ROADMAP.md) - 已实现功能和未来计划

## 配置文件

项目使用 YAML 格式的配置文件：

- **config/default.yaml** - 默认配置文件
- **config/config.yaml** - 用户配置文件（用于覆盖默认配置）

配置优先级：命令行参数 > 用户配置文件 > 默认配置文件

## 代码结构

```
GrabTheSite/
├── crawler/              # 抓取模块
├── config/               # 配置文件目录
├── gui/                  # GUI界面模块
├── plugins/              # 插件目录
├── utils/                # 工具模块
├── docs/                 # 文档目录
├── logger.py             # 日志系统
├── config.py             # 配置管理
├── grab_the_site.py      # 命令行主脚本
└── grab_gui.py           # GUI应用程序入口
```

## 依赖安装

```bash
pip install -r requirements.txt
```

## 许可证

[LICENSE](LICENSE)
