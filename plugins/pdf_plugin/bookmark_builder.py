"""书签构建器

根据页面 URL 结构和深度构建 PDF 书签树。
参考 sitemap_generator 的树结构实现。
"""

import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class BookmarkNode:
    """书签节点"""

    def __init__(self, title, page_number=0, level=0):
        """初始化书签节点

        Args:
            title: 书签标题
            page_number: 页码（从1开始）
            level: 层级深度（0为根层级）
        """
        self.title = title
        self.page_number = page_number
        self.level = level
        self.children = []

    def add_child(self, child):
        """添加子书签

        Args:
            child: BookmarkNode 实例
        """
        self.children.append(child)


class BookmarkBuilder:
    """书签构建器，参考 sitemap_generator 的树结构"""

    def __init__(self, target_url, output_dir):
        """初始化书签构建器

        Args:
            target_url: 目标网站 URL
            output_dir: 输出目录
        """
        self.target_url = target_url
        self.output_dir = output_dir
        self.parsed_target = urlparse(target_url)

    def build_bookmarks(self, pages, page_depths=None):
        """构建书签树

        Args:
            pages: 页面字典，键为 URL，值为 HTML 内容
            page_depths: 页面深度字典，键为 URL，值为深度

        Returns:
            list: BookmarkNode 列表（根层级书签）
        """
        # 构建页面树结构（参考 sitemap_generator._build_page_tree）
        page_tree = {}

        for url, html_content in pages.items():
            depth = page_depths.get(url, 0) if page_depths else 0
            title = self._extract_title(html_content, url)
            path_parts = self._extract_path_parts(url)

            self._add_to_tree(page_tree, path_parts, url, title, depth)

        # 转换为书签节点列表
        return self._tree_to_bookmarks(page_tree)

    def _extract_title(self, html_content, url):
        """从 HTML 中提取标题（参考 sitemap_generator._extract_title）

        Args:
            html_content: HTML 内容
            url: 页面 URL

        Returns:
            str: 页面标题
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and title_tag.text.strip():
                return title_tag.text.strip()
        except Exception:
            pass

        # 默认标题
        parsed = urlparse(url)
        path = parsed.path
        if not path or path == '/':
            return 'Home'

        # 从路径中提取文件名或目录名
        basename = os.path.basename(path)
        if basename and basename not in ['index.html', 'index.htm']:
            # 移除扩展名
            if '.' in basename:
                return os.path.splitext(basename)[0]
            return basename

        # 使用上级目录名
        dirname = os.path.basename(os.path.dirname(path))
        return dirname if dirname else 'Home'

    def _extract_path_parts(self, url):
        """提取 URL 路径层级（参考 sitemap_generator._extract_path_parts）

        Args:
            url: 页面 URL

        Returns:
            list: 路径层级列表
        """
        parsed = urlparse(url)
        path = parsed.path

        if not path or path == '/':
            return []

        parts = path.strip('/').split('/')
        parts = [p for p in parts if p]

        # 移除 index.html 等默认文档名
        if parts and parts[-1] in ['index.html', 'index.htm']:
            parts = parts[:-1]
        elif parts and '.' in parts[-1]:
            # 其他带扩展名的文件，保留目录结构
            parts = parts[:-1]

        return parts

    def _add_to_tree(self, tree, path_parts, url, title, depth):
        """添加页面到树结构

        Args:
            tree: 树字典
            path_parts: 路径层级列表
            url: 页面 URL
            title: 页面标题
            depth: 页面深度
        """
        current = tree

        for part in path_parts:
            if part not in current:
                current[part] = {}
            current = current[part]

        # 在叶子节点存储页面信息
        if '_pages' not in current:
            current['_pages'] = []

        current['_pages'].append({
            'url': url,
            'title': title,
            'depth': depth
        })

    def _tree_to_bookmarks(self, tree, level=0):
        """将树结构转换为书签节点列表

        Args:
            tree: 页面树字典
            level: 当前层级

        Returns:
            list: BookmarkNode 列表
        """
        bookmarks = []

        # 先处理页面节点（_pages）
        if '_pages' in tree:
            for page in tree['_pages']:
                bookmark = BookmarkNode(
                    title=page['title'],
                    page_number=0,  # 稍后填充实际页码
                    level=level
                )
                bookmarks.append(bookmark)

        # 再处理子目录节点（按字母顺序排序）
        for name in sorted(tree.keys()):
            if name == '_pages':
                continue

            # 创建目录书签
            folder_bookmark = BookmarkNode(
                title=name,
                page_number=0,
                level=level
            )

            # 递归处理子节点
            children = self._tree_to_bookmarks(tree[name], level + 1)
            for child in children:
                folder_bookmark.add_child(child)

            bookmarks.append(folder_bookmark)

        return bookmarks
