# 命令行参数支持

## 可用参数

| 参数 | 简写 | 类型 | 描述 |
|------|------|------|------|
| `--url` | `-u` | 字符串 | 目标网站 URL |
| `--depth` | `-d` | 整数 | 最大抓取深度 |
| `--max-files` | `-m` | 整数 | 最大文件数量 |
| `--output` | `-o` | 字符串 | 输出目录 |
| `--delay` | `-t` | 浮点数 | 请求间隔（秒） |
| `--no-random-delay` | | 布尔值 | 禁用随机延迟 |
| `--threads` | `-p` | 整数 | 线程数 |
| `--exclude-urls` | | 字符串列表 | 排除的URL列表，支持通配符 |
| `--incremental` | `-i` | 布尔值 | 启用增量抓取 |
| `--no-incremental` | | 布尔值 | 禁用增量抓取 |
| `--js-timeout` | | 整数 | JavaScript渲染超时时间（秒） |
| `--lang` | | 字符串 | 语言代码，如 'en', 'zh_CN' 等 |
| `--user-agent` | | 字符串 | 自定义用户代理字符串 |
| `--plugins` | | 字符串 | 启用的插件名称列表 |
| `--no-plugins` | | 布尔值 | 禁用插件系统 |
| `--force-download` | | 布尔值 | 强制重新下载页面 |

## 使用示例

### 1. 基本使用（使用配置文件中的默认值）

```bash
python grab_the_site.py
```

### 2. 指定目标 URL

```bash
python grab_the_site.py --url https://example.com
```

### 3. 指定抓取深度和最大文件数

```bash
python grab_the_site.py --depth 2 --max-files 50
```

### 4. 指定输出目录

```bash
python grab_the_site.py --output my_site
```

### 5. 组合使用所有参数

```bash
python grab_the_site.py --url https://example.com --depth 3 --max-files 100 --output example_site
```

### 6. 设置延迟参数

```bash
python grab_the_site.py --url https://example.com --delay 2 --no-random-delay
```

这将设置固定的 2 秒延迟，禁用随机延迟功能。

### 7. 设置线程数

```bash
python grab_the_site.py --url https://example.com --threads 8
```

这将使用 8 个线程进行并行抓取，提高抓取速度。

### 8. 排除特定URL

```bash
python grab_the_site.py --url https://example.com --exclude-urls "/admin/*" "/api/*" "*.pdf"
```

这将排除匹配通配符模式的URL，不进行下载。

### 9. 启用增量抓取

```bash
python grab_the_site.py --url https://example.com --incremental
```

这将启用增量抓取功能，只下载比本地文件更新的内容。

### 10. 禁用增量抓取

```bash
python grab_the_site.py --url https://example.com --no-incremental
```

这将禁用增量抓取功能，强制重新下载所有内容。

### 11. 设置JavaScript渲染超时时间

```bash
python grab_the_site.py --url https://example.com --js-timeout 45
```

这将设置JavaScript渲染超时时间为45秒。（JavaScript渲染默认已启用）

### 12. 设置语言为英文

```bash
python grab_the_site.py --url https://example.com --lang en
```

这将使用英文作为界面语言。

### 13. 设置语言为中文

```bash
python grab_the_site.py --url https://example.com --lang zh_CN
```

这将使用中文作为界面语言。

### 14. 设置自定义用户代理

```bash
python grab_the_site.py --url https://example.com --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
```

这将使用指定的自定义用户代理字符串。

### 15. 启用插件系统并指定启用的插件

```bash
python grab_the_site.py --url https://example.com --plugins save_plugin
```

这将启用插件系统，并只启用 save_plugin 插件。

### 16. 禁用插件系统

```bash
python grab_the_site.py --url https://example.com --no-plugins
```

这将禁用插件系统，不加载任何插件。

### 17. 强制重新下载页面

```bash
python grab_the_site.py --url https://example.com --force-download
```

这将强制重新下载页面，忽略页面的更新时间戳，以便测试保存插件的功能。

### 18. 使用保存插件并强制重新下载页面

```bash
python grab_the_site.py --url https://example.com --plugins save_plugin --force-download
```

这将使用保存插件处理保存功能，并强制重新下载页面，以便测试保存插件的完整工作流程。

## 注意事项

- 命令行参数优先级高于配置文件
- 未指定的参数将使用配置文件中的值
- 所有参数均为可选
- 参数值必须符合预期类型（如深度和文件数量必须为整数）
