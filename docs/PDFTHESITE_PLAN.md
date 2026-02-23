# PDFtheSite 分支开发计划

## 项目目标

将抓取的网站保存为 **PDF 文件**，同时保留：
1. **页面目录结构** - 在 PDF 中生成可点击的书签/目录
2. **页面内链接** - 保留页面之间的跳转链接

## 技术选型

### PDF 生成库对比

| 库 | 优点 | 缺点 | 适用性 |
|---|---|---|---|
| **Playwright + PDF** | 使用现有 Playwright 渲染引擎，保持样式一致性 | 每页需要单独渲染 | ⭐⭐⭐⭐⭐ |
| **WeasyPrint** | 纯 Python，易于集成 | 对复杂 CSS/JS 支持有限 | ⭐⭐⭐ |
| **pdfkit (wkhtmltopdf)** | 成熟稳定 | 需要额外安装二进制依赖 | ⭐⭐⭐⭐ |
| **ReportLab** | 完全可控 | 需要手动布局，工作量大 | ⭐⭐ |

### 推荐方案：**Playwright PDF 生成**

理由：
1. 项目已集成 Playwright 用于 JS 渲染
2. 可以保持与浏览器一致的渲染效果
3. 支持生成书签（Bookmarks）
4. 支持设置页眉页脚

## 架构设计

### 1. 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        抓取阶段 (CrawlSite)                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ 抓取页面 │ -> │ 解析链接 │ -> │ 收集资源 │ -> │ 暂存内容 │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PDF 生成阶段 (PDFPlugin)                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ 分析结构 │ -> │ 生成书签 │ -> │ 渲染PDF │ -> │ 合并文档 │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 模块设计

#### 2.1 PDF 插件 (plugins/pdf_plugin/)

参考 `save_plugin` 的结构设计：

```
plugins/pdf_plugin/
├── __init__.py           # 插件入口，导出 PdfPlugin 类
├── pdf_generator.py      # PDF 生成核心逻辑
├── bookmark_builder.py   # 书签/目录构建器
├── link_processor.py     # 链接处理器（处理页面内链接）
└── pdf_merger.py         # PDF 合并工具
```

#### 2.2 核心类设计（参考 save_plugin）

```python
class PdfPlugin(Plugin):
    """PDF 保存插件
    
    负责将抓取的页面保存为 PDF 文件，保留目录结构和页面链接。
    参考 save_plugin.SavePlugin 的实现方式。
    """
    
    name = "PDF Plugin"
    description = "将抓取的网站保存为 PDF 文件，保留目录结构和页面链接"
    
    def __init__(self, config=None):
        """初始化插件
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.target_url = None
        self.output_dir = None
        self.output_pdf_path = None
        self.pdf_config = config.get('pdf', {}) if config else {}
        
        # 页面数据
        self.pages = {}
        self.page_depths = {}
        self.saved_files = []
        
        # 工具类实例
        self.bookmark_builder = None
        self.link_processor = None
        self.pdf_generator = None
        self.pdf_merger = None
        
        # URL 到页码的映射（用于内部链接跳转）
        self.url_to_page_map = {}
        
    def on_init(self):
        """插件初始化时调用"""
        super().on_init()
        self.logger.info(_("PDF插件初始化完成"))
    
    def on_crawl_end(self, pages):
        """抓取结束时调用，准备保存参数
        
        Args:
            pages: 抓取的页面字典
        """
        self.logger.info(_("准备生成PDF，共") + f" {len(pages)} " + _("个页面"))
        self.pages = pages
    
    def on_save_start(self, saver_data):
        """保存开始时调用
        
        参考 save_plugin.on_save_start 的实现
        
        Args:
            saver_data: 保存器数据，包含target_url、output_dir等
        """
        self.target_url = saver_data.get('target_url')
        self.output_dir = saver_data.get('output_dir')
        
        # 获取页面深度信息
        self.page_depths = saver_data.get('page_depths', {})
        
        if self.target_url and self.output_dir:
            # 提取起始目录路径
            from urllib.parse import urlparse
            parsed_target = urlparse(self.target_url)
            self.target_directory = parsed_target.path
            if not self.target_directory.endswith('/'):
                self.target_directory += '/'
            
            # 初始化工具类
            self.bookmark_builder = BookmarkBuilder(self.target_url, self.output_dir)
            self.link_processor = LinkProcessor()
            self.pdf_generator = PdfGenerator(self.pdf_config)
            self.pdf_merger = PdfMerger()
            
            # 设置输出路径
            output_filename = self.pdf_config.get('output_filename', 'site.pdf')
            self.output_pdf_path = os.path.join(self.output_dir, output_filename)
            
            self.logger.info(_("PDF插件准备就绪，输出路径") + f": {self.output_pdf_path}")
        else:
            self.logger.error(_("PDF插件初始化失败：缺少必要参数"))
    
    def save_site(self, pages):
        """保存抓取的页面为 PDF
        
        参考 save_plugin.save_site 的实现方式
        
        Args:
            pages: 暂存的页面内容，键为URL，值为页面内容
            
        Returns:
            list: 保存的文件列表
        """
        if not pages:
            self.logger.warning(_("没有页面需要保存"))
            return []
        
        self.logger.info(_("开始生成PDF，共") + f" {len(pages)} " + _("个页面"))
        
        # 1. 分析页面结构，构建书签树
        bookmark_tree = self.bookmark_builder.build_bookmarks(pages, self.page_depths)
        self.logger.info(_("书签树构建完成"))
        
        # 2. 为每个页面生成单个 PDF（临时文件）
        temp_pdf_files = []
        page_count = 0
        
        for url, html_content in pages.items():
            try:
                # 处理页面内链接
                processed_html = self.link_processor.process_links(
                    html_content, url, pages.keys()
                )
                
                # 生成临时 PDF 文件
                temp_pdf_path = os.path.join(
                    self.output_dir, 
                    '.temp_pdf', 
                    f"page_{page_count:04d}.pdf"
                )
                os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
                
                self.pdf_generator.generate_pdf(processed_html, temp_pdf_path, url)
                temp_pdf_files.append((url, temp_pdf_path))
                
                # 记录 URL 到页码的映射
                self.url_to_page_map[url] = page_count + 1  # PDF 页码从 1 开始
                
                page_count += 1
                self.logger.info(_("生成页面PDF") + f": {url} ({page_count}/{len(pages)})")
                
            except Exception as e:
                self.logger.error(_("生成页面PDF失败") + f": {url}, " + _("错误") + f": {str(e)}")
        
        # 3. 合并所有 PDF 并添加书签
        if temp_pdf_files:
            try:
                self.pdf_merger.merge_pdfs(
                    temp_pdf_files, 
                    self.output_pdf_path, 
                    bookmark_tree,
                    self.url_to_page_map
                )
                self.saved_files.append((self.target_url, self.output_pdf_path))
                self.logger.info(_("PDF生成完成") + f": {self.output_pdf_path}")
                
                # 清理临时文件
                self._cleanup_temp_files(temp_pdf_files)
                
            except Exception as e:
                self.logger.error(_("合并PDF失败") + f": {str(e)}")
        
        return self.saved_files
    
    def _cleanup_temp_files(self, temp_pdf_files):
        """清理临时 PDF 文件"""
        import shutil
        temp_dir = os.path.join(self.output_dir, '.temp_pdf')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                self.logger.debug(_("清理临时文件完成"))
            except Exception as e:
                self.logger.warning(_("清理临时文件失败") + f": {str(e)}")
    
    def on_save_end(self, saved_files):
        """保存结束时调用
        
        Args:
            saved_files: 保存的文件列表
        """
        self.logger.info(_("PDF插件工作完成") + f", {_('共生成')} {len(saved_files)} {_('个文件')}")
```

## 功能规划

### 阶段一：基础 PDF 生成

#### 1.1 PDF 插件框架
- [ ] 创建 `plugins/pdf_plugin/__init__.py`
- [ ] 实现 `PdfPlugin` 基础类（参考 save_plugin 结构）
- [ ] 集成到插件系统

#### 1.2 单页 PDF 生成
- [ ] 使用 Playwright 将 HTML 渲染为 PDF
- [ ] 支持自定义页面尺寸（A4, Letter 等）
- [ ] 支持页眉页脚设置
- [ ] 支持页边距配置

#### 1.3 配置支持
- [ ] 在 `default.yaml` 中添加 PDF 配置项
- [ ] 支持配置输出文件名
- [ ] 支持配置页面格式

### 阶段二：书签/目录生成

#### 2.1 书签构建器
- [ ] 分析页面 URL 结构，构建层级书签（参考 sitemap_generator 的树结构）
- [ ] 根据页面深度生成书签层级
- [ ] 使用页面标题作为书签文本

#### 2.2 书签样式
- [ ] 支持展开/折叠层级
- [ ] 支持在 PDF 阅读器中默认展开特定层级

### 阶段三：链接处理

#### 3.1 页面内链接转换
- [ ] 将 HTML 中的 `<a>` 标签链接转换为 PDF 内部跳转
- [ ] 处理相对路径链接
- [ ] 处理绝对路径链接（同域名）

#### 3.2 外部链接处理
- [ ] 外部链接保留为可点击链接
- [ ] 可选：在 PDF 中添加外部链接注释

### 阶段四：PDF 合并与优化

#### 4.1 PDF 合并
- [ ] 使用 `pypdf` 合并多个 PDF
- [ ] 保留每个页面的书签信息
- [ ] 处理页面编号

#### 4.2 优化
- [ ] 压缩 PDF 文件大小
- [ ] 优化图片质量

### 阶段五：GUI 支持

#### 5.1 配置面板
- [ ] 添加 PDF 输出选项
- [ ] 页面格式选择
- [ ] 书签选项

#### 5.2 进度显示
- [ ] 显示 PDF 生成进度
- [ ] 显示当前处理的页面

## 配置设计

### default.yaml 新增配置

```yaml
# PDF 输出配置（默认启用）
pdf:
  output_filename: "site.pdf"       # 输出文件名
  
  # 页面设置
  page:
    format: "A4"                    # 页面格式: A4, Letter, Legal, Tabloid
    width: null                     # 自定义宽度（单位：mm，设置后 format 失效）
    height: null                    # 自定义高度（单位：mm）
    margin:
      top: 20                       # 上边距（mm）
      bottom: 20                    # 下边距（mm）
      left: 20                      # 左边距（mm）
      right: 20                     # 右边距（mm）
    
  # 页眉页脚
  header:
    enabled: true
    template: "{title}"             # 页眉模板: {title}, {url}, {page}, {total}
  footer:
    enabled: true
    template: "Page {page} of {total}"
    
  # 书签设置
  bookmarks:
    enabled: true                   # 是否生成书签
    max_depth: 3                    # 书签最大深度
    expand_level: 2                 # 默认展开层级
    
  # 链接处理
  links:
    internal: "jump"                # 内部链接处理: jump=跳转, none=不处理
    external: "keep"                # 外部链接处理: keep=保留, remove=移除
    
  # 优化选项
  optimization:
    compress: true                  # 压缩 PDF
    image_quality: 80               # 图片质量 (0-100)
```

## 依赖项

### 新增依赖

```txt
# PDF 处理（已确定使用 pypdf）
pypdf>=4.0.0           # PDF 合并和处理，支持书签/目录功能

# 已在项目中
# playwright>=1.40.0   # 用于 HTML 渲染为 PDF
```

### 选择 pypdf 的理由

1. **功能满足**：完全满足 PDF 合并和书签添加需求
2. **轻量级**：纯 Python 实现，安装包小 (~500KB)
3. **API 简洁**：书签添加接口直观易用
4. **许可证友好**：BSD-3-Clause，无商业限制
5. **社区活跃**：PyPDF2 的后继项目，维护良好

### 不使用 PyMuPDF 的原因

虽然 PyMuPDF 功能更强大（支持图片提取、PDF 渲染等），但对于本项目：
- 功能过剩：我们只需要合并 PDF 和添加书签
- 体积较大：安装包 ~20MB+
- 许可证限制：AGPL/商业许可

## 实现细节

### 1. PdfGenerator - PDF 生成器

```python
class PdfGenerator:
    """PDF 生成器，使用 Playwright 将 HTML 渲染为 PDF"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.page_config = self.config.get('page', {})
        self.header_config = self.config.get('header', {})
        self.footer_config = self.config.get('footer', {})
    
    def generate_pdf(self, html_content, output_path, source_url=None):
        """将 HTML 内容渲染为 PDF
        
        Args:
            html_content: HTML 内容
            output_path: 输出 PDF 文件路径
            source_url: 源 URL（用于日志）
        """
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # 加载 HTML 内容
            page.set_content(html_content)
            
            # 等待资源加载完成
            page.wait_for_load_state('networkidle')
            
            # 获取页面配置
            format_option = self.page_config.get('format', 'A4')
            margin_config = self.page_config.get('margin', {})
            
            # 生成 PDF
            page.pdf(
                path=output_path,
                format=format_option,
                margin={
                    'top': f"{margin_config.get('top', 20)}mm",
                    'bottom': f"{margin_config.get('bottom', 20)}mm",
                    'left': f"{margin_config.get('left', 20)}mm",
                    'right': f"{margin_config.get('right', 20)}mm"
                },
                display_header_footer=self.header_config.get('enabled', True),
                header_template=self._build_header_template(),
                footer_template=self._build_footer_template(),
                print_background=True
            )
            
            browser.close()
    
    def _build_header_template(self):
        """构建页眉模板"""
        if not self.header_config.get('enabled', True):
            return ''
        template = self.header_config.get('template', '{title}')
        # 返回 HTML 模板字符串
        return f'<div style="font-size: 9px; width: 100%; text-align: center;">{template}</div>'
    
    def _build_footer_template(self):
        """构建页脚模板"""
        if not self.footer_config.get('enabled', True):
            return ''
        template = self.footer_config.get('template', 'Page {page} of {total}')
        # Playwright 使用特殊格式：<span class="pageNumber"></span>
        template = template.replace('{page}', '<span class="pageNumber"></span>')
        template = template.replace('{total}', '<span class="totalPages"></span>')
        return f'<div style="font-size: 9px; width: 100%; text-align: center;">{template}</div>'
```

### 2. BookmarkBuilder - 书签构建器

```python
class BookmarkBuilder:
    """书签构建器，参考 sitemap_generator 的树结构"""
    
    def __init__(self, target_url, output_dir):
        self.target_url = target_url
        self.output_dir = output_dir
        self.parsed_target = urlparse(target_url)
    
    def build_bookmarks(self, pages, page_depths=None):
        """构建书签树
        
        Args:
            pages: 页面字典，键为 URL，值为 HTML 内容
            page_depths: 页面深度字典
            
        Returns:
            BookmarkNode: 书签树根节点
        """
        # 构建页面树结构（参考 sitemap_generator._build_page_tree）
        page_tree = {}
        
        for url, html_content in pages.items():
            depth = page_depths.get(url, 0) if page_depths else 0
            title = self._extract_title(html_content, url)
            path_parts = self._extract_path_parts(url)
            
            self._add_to_tree(page_tree, path_parts, url, title, depth)
        
        # 转换为书签节点
        return self._tree_to_bookmarks(page_tree)
    
    def _extract_title(self, html_content, url):
        """从 HTML 中提取标题（参考 sitemap_generator._extract_title）"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and title_tag.text.strip():
                return title_tag.text.strip()
        except Exception:
            pass
        
        # 默认标题
        from urllib.parse import urlparse
        import os
        parsed = urlparse(url)
        path = parsed.path
        if not path or path == '/':
            return 'Home'
        return os.path.basename(path) or 'Home'
    
    def _extract_path_parts(self, url):
        """提取 URL 路径层级（参考 sitemap_generator._extract_path_parts）"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            return []
        
        parts = path.strip('/').split('/')
        parts = [p for p in parts if p]
        
        # 移除 index.html
        if parts and parts[-1] in ['index.html', 'index.htm']:
            parts = parts[:-1]
        elif parts and '.' in parts[-1]:
            parts = parts[:-1]
        
        return parts
    
    def _add_to_tree(self, tree, path_parts, url, title, depth):
        """添加页面到树结构"""
        current = tree
        for part in path_parts:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        if '_pages' not in current:
            current['_pages'] = []
        
        current['_pages'].append({
            'url': url,
            'title': title,
            'depth': depth
        })
    
    def _tree_to_bookmarks(self, tree, level=0):
        """将树结构转换为书签节点"""
        bookmarks = []
        
        # 先处理页面
        if '_pages' in tree:
            for page in tree['_pages']:
                bookmarks.append(BookmarkNode(
                    title=page['title'],
                    page_number=0,  # 稍后填充
                    level=level
                ))
        
        # 再处理子目录
        for name, children in sorted(tree.items()):
            if name == '_pages':
                continue
            
            folder_bookmark = BookmarkNode(
                title=name + '/',
                page_number=0,
                level=level
            )
            folder_bookmark.children = self._tree_to_bookmarks(children, level + 1)
            bookmarks.append(folder_bookmark)
        
        return bookmarks


class BookmarkNode:
    """书签节点"""
    def __init__(self, title, page_number, level=0):
        self.title = title
        self.page_number = page_number
        self.level = level
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
```

### 3. LinkProcessor - 链接处理器

```python
class LinkProcessor:
    """处理 HTML 中的链接，转换为 PDF 内部跳转"""
    
    def __init__(self):
        self.url_to_page_map = {}
    
    def set_url_to_page_map(self, url_map):
        """设置 URL 到页码的映射"""
        self.url_to_page_map = url_map
    
    def process_links(self, html_content, base_url, all_page_urls):
        """处理 HTML 中的链接
        
        Args:
            html_content: HTML 内容
            base_url: 当前页面 URL
            all_page_urls: 所有页面 URL 集合
            
        Returns:
            str: 处理后的 HTML
        """
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # 规范化 URL
            normalized_url = self._normalize_url(full_url)
            
            # 检查是否为内部链接（在抓取范围内）
            if normalized_url in all_page_urls:
                # 添加标记，供 PDF 生成器处理
                link['data-internal-link'] = 'true'
                link['data-target-url'] = normalized_url
            else:
                # 外部链接，添加标识
                link['data-external-link'] = 'true'
        
        return str(soup)
    
    def _normalize_url(self, url):
        """规范化 URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
```

### 4. PdfMerger - PDF 合并器

```python
class PdfMerger:
    """PDF 合并器，使用 pypdf 合并多个 PDF 并添加书签"""
    
    def __init__(self):
        self.page_offsets = {}  # URL -> 起始页码映射
        self.total_pages = 0    # 总页数
    
    def merge_pdfs(self, pdf_files, output_path, bookmark_tree, url_to_page_map):
        """合并 PDF 文件并添加书签
        
        Args:
            pdf_files: PDF 文件列表，每项为 (url, file_path) 元组
            output_path: 输出文件路径
            bookmark_tree: 书签树（BookmarkNode 列表）
            url_to_page_map: URL 到页码的映射
        """
        from pypdf import PdfMerger as PyPdfMerger, PdfReader
        
        merger = PyPdfMerger()
        
        # 第一步：合并所有 PDF，记录每个文件的起始页码
        self.page_offsets = {}
        self.total_pages = 0
        
        for url, file_path in pdf_files:
            self.page_offsets[url] = self.total_pages
            
            # 读取 PDF 获取页数
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            
            # 追加到合并器
            merger.append(file_path)
            
            self.total_pages += num_pages
        
        # 第二步：更新书签树中的页码
        self._update_bookmark_pages(bookmark_tree, url_to_page_map)
        
        # 第三步：添加层级书签到 PDF
        self._add_bookmarks_to_merger(merger, bookmark_tree)
        
        # 第四步：写入输出文件
        merger.write(output_path)
        merger.close()
        
        return output_path
    
    def _update_bookmark_pages(self, bookmarks, url_to_page_map):
        """更新书签树中每个节点的实际页码
        
        Args:
            bookmarks: BookmarkNode 列表
            url_to_page_map: URL -> PDF页码 映射
        """
        for bookmark in bookmarks:
            # 根据 URL 查找对应的页码
            # 注意：这里需要根据实际逻辑来映射 URL 到页码
            # 简化示例：假设 bookmark.title 包含 URL 信息
            for url, page_num in url_to_page_map.items():
                if bookmark.title in url or url in bookmark.title:
                    # 计算在合并后 PDF 中的实际页码
                    offset = self.page_offsets.get(url, 0)
                    bookmark.page_number = offset + 1  # PDF 页码从 1 开始
                    break
            
            # 递归处理子书签
            if bookmark.children:
                self._update_bookmark_pages(bookmark.children, url_to_page_map)
    
    def _add_bookmarks_to_merger(self, merger, bookmarks, parent_bookmark=None):
        """递归添加书签到合并器
        
        Args:
            merger: PyPdfMerger 实例
            bookmarks: BookmarkNode 列表
            parent_bookmark: 父书签对象（用于构建层级）
        """
        for bookmark in bookmarks:
            # pypdf 4.0+ 使用 add_outline_item 添加书签
            # page_number 是 0-based 索引
            current = merger.add_outline_item(
                title=bookmark.title,
                page_number=bookmark.page_number - 1 if bookmark.page_number > 0 else 0,
                parent=parent_bookmark
            )
            
            # 递归添加子书签
            if bookmark.children:
                self._add_bookmarks_to_merger(merger, bookmark.children, current)
```

## 目录结构

```
GrabTheSite/
├── plugins/
│   ├── save_plugin/          # 现有 HTML 保存插件（原入口使用）
│   └── pdf_plugin/           # 新增 PDF 插件（新入口使用）
│       ├── __init__.py       # PdfPlugin 主类（参考 save_plugin 结构）
│       ├── pdf_generator.py  # PdfGenerator 类
│       ├── bookmark_builder.py  # BookmarkBuilder 和 BookmarkNode 类
│       ├── link_processor.py    # LinkProcessor 类
│       └── pdf_merger.py        # PdfMerger 类
├── config/
│   └── default.yaml          # 添加 PDF 配置（无 enabled 选项）
├── docs/
│   └── PDFTHESITE_PLAN.md    # 本计划文档
│
├── grab_the_site.py          # 原 CLI 入口（HTML保存，启用save_plugin）
├── grab_gui.py               # 原 GUI 入口（HTML保存，启用save_plugin）
├── pdf_the_site.py           # 新 CLI 入口（PDF保存，启用pdf_plugin）
└── pdf_gui.py                # 新 GUI 入口（PDF保存，启用pdf_plugin）
```

## 入口文件设计

### 入口文件对比

| 入口文件 | 类型 | 保存格式 | 启用插件 | 说明 |
|---------|------|---------|---------|------|
| `grab_the_site.py` | CLI | HTML | save_plugin | 原有功能不变 |
| `grab_gui.py` | GUI | HTML | save_plugin | 原有功能不变 |
| `pdf_the_site.py` | CLI | PDF | pdf_plugin | 新增，PDF输出 |
| `pdf_gui.py` | GUI | PDF | pdf_plugin | 新增，PDF输出 |

### pdf_the_site.py 设计

参考 `grab_the_site.py` 的结构，但：
1. 默认启用 `pdf_plugin`
2. 禁用 `save_plugin`
3. 添加 PDF 相关命令行参数
4. 修改日志和提示信息

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDFtheSite CLI 入口

网站抓取工具的 PDF 输出命令行入口：
1. 解析命令行参数
2. 加载和合并配置
3. 初始化插件系统（启用 pdf_plugin，禁用 save_plugin）
4. 启动抓取流程
5. 生成 PDF 文件
"""

import os
import sys
import argparse
from urllib.parse import urlparse
from config import load_config, CONFIG, TARGET_URL, MAX_DEPTH, MAX_FILES, DELAY, RANDOM_DELAY, THREADS, USER_AGENT, OUTPUT_DIR, I18N_CONFIG, JS_RENDERING_CONFIG
from crawler.crawl_site import CrawlSite
from logger import setup_logger
from utils.i18n import init_i18n, get_current_lang

def _(message):
    from utils.i18n import gettext
    return gettext(message)

from utils.plugin_manager import PluginManager

logger = setup_logger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="PDFtheSite - 网站抓取工具，输出PDF格式"
    )
    
    # 基础参数（与 grab_the_site.py 相同）
    parser.add_argument("--url", "-u", type=str, default=None, help="目标网站 URL")
    parser.add_argument("--depth", "-d", type=int, default=None, help="最大抓取深度")
    parser.add_argument("--max-files", "-m", type=int, default=None, help="最大文件数量")
    parser.add_argument("--output", "-o", type=str, default=None, help="输出目录")
    parser.add_argument("--delay", "-t", type=float, default=None, help="请求间隔（秒）")
    parser.add_argument("--no-random-delay", action="store_true", help="禁用随机延迟")
    parser.add_argument("--threads", "-p", type=int, default=None, help="线程数")
    parser.add_argument("--js-timeout", type=int, default=None, help="JavaScript渲染超时时间（秒）")
    parser.add_argument("--lang", type=str, default=None, help="语言代码")
    parser.add_argument("--user-agent", type=str, default=None, help="自定义用户代理字符串")
    parser.add_argument("--force-download", action="store_true", help="强制重新下载页面")
    parser.add_argument("--exclude-urls", type=str, nargs="*", default=None, help="不要下载的URL列表")
    
    # PDF 特有参数
    parser.add_argument(
        "--pdf-filename",
        type=str,
        default=None,
        help="PDF输出文件名（默认：site.pdf）"
    )
    parser.add_argument(
        "--pdf-format",
        type=str,
        choices=["A4", "Letter", "Legal", "Tabloid"],
        default=None,
        help="PDF页面格式"
    )
    parser.add_argument(
        "--pdf-margin",
        type=int,
        default=None,
        help="PDF页边距（mm）"
    )
    parser.add_argument(
        "--no-bookmarks",
        action="store_true",
        help="不生成PDF书签"
    )
    
    return parser.parse_args()


def main(args_list=None, stop_event=None):
    """主函数"""
    # 解析参数
    args = parse_args()
    
    # 加载配置
    config = load_config()
    
    # 更新配置（与 grab_the_site.py 类似）
    if args.url:
        config["target_url"] = args.url
        parsed_url = urlparse(args.url)
        site_name = parsed_url.netloc
        if "output" not in config:
            config["output"] = {}
        config["output"]["site_name"] = site_name
    
    # ... 其他配置更新 ...
    
    # PDF 特有配置
    if "pdf" not in config:
        config["pdf"] = {}
    if args.pdf_filename:
        config["pdf"]["output_filename"] = args.pdf_filename
    if args.pdf_format:
        config["pdf"]["page", "format"] = args.pdf_format
    if args.pdf_margin:
        config["pdf"]["page", "margin"] = {
            "top": args.pdf_margin,
            "bottom": args.pdf_margin,
            "left": args.pdf_margin,
            "right": args.pdf_margin
        }
    if args.no_bookmarks:
        config["pdf"]["bookmarks", "enabled"] = False
    
    # 初始化插件系统 - 关键区别：启用 pdf_plugin，禁用 save_plugin
    plugin_manager = PluginManager(config)
    plugin_manager.discover_plugins()
    
    # 只加载 pdf_plugin，跳过 save_plugin
    for plugin_class in plugin_manager.plugins.values():
        if plugin_class.__name__ == "PdfPlugin":
            plugin = plugin_class(config)
            plugin_manager.loaded_plugins[plugin.name] = plugin
            plugin_manager.enabled_plugins.append(plugin)
            logger.info(_("已启用PDF插件"))
        elif plugin_class.__name__ == "SavePlugin":
            logger.debug(_("跳过HTML保存插件"))
            continue
    
    # 启动抓取流程（与 grab_the_site.py 类似）
    # ...


if __name__ == "__main__":
    main()
```

### pdf_gui.py 设计

参考 `grab_gui.py` 的结构：
1. 创建新的主窗口类 `PdfMainWindow`
2. 默认启用 `pdf_plugin`，禁用 `save_plugin`
3. 添加 PDF 配置面板
4. 修改窗口标题和界面文本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDFtheSite GUI 应用程序入口

启动 PDFtheSite 的图形界面：
- 加载 PDF 主窗口
- 启用 pdf_plugin
- 禁用 save_plugin
- 启动事件循环
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.pdf_main_window import PdfMainWindow


def main():
    """主函数"""
    root = PdfMainWindow()
    root.mainloop()


if __name__ == "__main__":
    main()
```

## 开发顺序

| 优先级 | 任务 | 预计工作量 | 依赖 |
|---|---|---|---|
| P0 | 创建 PDF 插件框架（参考 save_plugin） | 1d | 无 |
| P0 | PdfGenerator 单页 PDF 生成 | 2d | P0 |
| P1 | BookmarkBuilder 书签构建（参考 sitemap_generator） | 2d | P0 |
| P1 | PdfMerger PDF 合并 | 1d | P0 |
| P2 | LinkProcessor 链接处理 | 2d | P1 |
| P2 | 配置集成（default.yaml） | 1d | P0 |
| P3 | GUI 支持 | 2d | P2 |
| P3 | 优化与压缩 | 1d | P1 |

## 测试计划

### 单元测试
- [ ] PdfGenerator 测试
- [ ] BookmarkBuilder 测试
- [ ] LinkProcessor 测试
- [ ] PdfMerger 测试

### 集成测试
- [ ] 完整流程测试（小站点）
- [ ] 大站点测试（100+ 页面）
- [ ] 复杂 CSS/JS 页面测试

### 兼容性测试
- [ ] 不同 PDF 阅读器测试（Adobe, Chrome, Edge, Foxit）
- [ ] 移动端 PDF 阅读器测试

## 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| Playwright 渲染大页面内存占用高 | 高 | 实现分页渲染，及时释放资源 |
| PDF 文件过大 | 中 | 提供压缩选项，优化图片 |
| 复杂页面样式丢失 | 中 | 使用 Playwright 确保渲染一致性 |
| 书签层级过深 | 低 | 限制最大书签深度 |
| 外部资源加载失败 | 中 | 添加超时处理，使用本地缓存 |

## 后续扩展

1. **多格式输出**：支持 EPUB、MOBI 等电子书格式
2. **PDF 加密**：支持密码保护和权限设置
3. **水印功能**：支持添加文字或图片水印
4. **批量处理**：支持同时生成多个 PDF（按目录分割）
