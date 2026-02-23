# PDF 输出功能

GrabTheSite 支持将抓取的网站内容生成 PDF 文件，方便离线阅读和分享。

## 功能特点

- **高质量 PDF 输出**：使用 Playwright 渲染 HTML 并生成 PDF
- **智能书签生成**：自动生成 PDF 书签（目录），支持层级结构
- **书签优化显示**：空目录自动合并，多层目录显示为 `a/.../d` 格式
- **链接处理**：已下载页面通过书签导航，外部链接可点击跳转
- **图片处理**：自动处理相对路径图片，确保 PDF 中正确显示
- **多语言支持**：PDF 书签支持中英文

## 使用方法

### GUI 界面

运行 PDF 生成 GUI：

```bash
python pdf_gui.py
```

界面说明：
- **目标 URL**：要抓取的网站地址
- **抓取深度**：抓取链接的层级深度
- **最大文件数**：最多抓取的页面数量
- **PDF 文件名**：生成的 PDF 文件名
- **页面格式**：A4、Letter、Legal、Tabloid
- **页边距**：PDF 页面边距（毫米）

### 命令行

使用 `pdf_the_site.py` 脚本：

```bash
python pdf_the_site.py --url https://example.com --max-files 10 --pdf-filename output.pdf
```

参数说明：
- `--url`：目标网站 URL（必需）
- `--max-files`：最大抓取文件数
- `--pdf-filename`：PDF 输出文件名
- `--output`：输出目录
- `--depth`：抓取深度

## 书签结构

PDF 书签按照网站的目录结构生成：

- **目录**：使用 📁 图标，空目录自动合并
- **页面**：使用 📄 图标，点击跳转到对应页面

### 空目录合并示例

原始结构：
```
a/
  b/
    c/
      d/
        page1
```

书签显示：
```
📁 a/.../d
  📄 page1
```

## 技术实现

### 主要组件

- **PDFGenerator**：使用 Playwright 将 HTML 渲染为 PDF
- **BookmarkBuilder**：构建 PDF 书签树结构
- **PdfMerge**：合并多个 PDF 文件并添加书签

### 处理流程

1. 抓取网站页面
2. 处理 HTML（转换图片路径、处理链接）
3. 生成临时 PDF 文件
4. 合并 PDF 文件
5. 添加书签和页码映射

## 注意事项

- PDF 生成需要系统安装浏览器（Edge 或 Chrome）
- 大网站生成 PDF 可能需要较长时间
- 外部链接在 PDF 中可点击，但需要网络连接
