"""书签构建器

根据页面 URL 结构和深度构建 PDF 书签树。
参考 sitemap_generator 的树结构实现。
"""

import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class BookmarkNode:
    """书签节点"""

    def __init__(self, title, page_number=0, level=0, url=None):
        """初始化书签节点

        Args:
            title: 书签标题
            page_number: 页码（从1开始）
            level: 层级深度（0为根层级）
            url: 页面 URL（用于页码映射）
        """
        self.title = title
        self.page_number = page_number
        self.level = level
        self.url = url  # 存储原始 URL 用于页码映射
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

    def _get_empty_dir_chain(self, tree, name, middle_pages=None):
        """获取空目录链

        递归查找空目录链，返回 (最终目录名, 最终子树, 中间页面列表)。
        例如 a/b/c -> ("a/b/c", c的子树, [a的页面, b的页面])

        Args:
            tree: 当前子树
            name: 当前目录名
            middle_pages: 累积的中间页面列表

        Returns:
            tuple: (合并后的路径, 最终子树, 中间页面列表)
        """
        if middle_pages is None:
            middle_pages = []

        has_pages = '_pages' in tree and tree['_pages']
        subdirs = [k for k in tree.keys() if k != '_pages']

        # 收集当前目录的页面（不包括最终子树的页面）
        current_pages = tree.get('_pages', [])

        # 如果有页面或没有子目录，返回当前
        if has_pages or not subdirs:
            return name, tree, middle_pages

        # 空目录，继续递归
        subdir_name = subdirs[0]
        combined_name = f"{name}/{subdir_name}"

        # 将当前目录的页面加入中间页面列表
        middle_pages.extend(current_pages)

        return self._get_empty_dir_chain(tree[subdir_name], combined_name, middle_pages)

    def _format_path(self, path):
        """格式化路径，多层目录显示为 a/.../d

        Args:
            path: 路径字符串，如 "a/b/c/d"

        Returns:
            str: 格式化后的路径，如 "a/.../d"
        """
        parts = path.split('/')
        if len(parts) <= 2:
            return path
        return f"{parts[0]}/.../{parts[-1]}"

    def _tree_to_bookmarks(self, tree, level=0, is_root=True):
        """将树结构转换为书签节点列表

        目录结构显示为 "📁 目录名"，页面链接显示为 "📄 页面标题"。
        空目录（没有页面）会递归合并到下层目录显示。

        Args:
            tree: 页面树字典
            level: 当前层级
            is_root: 是否是根调用（用于区分空目录链的中间调用）

        Returns:
            list: BookmarkNode 列表
        """
        bookmarks = []

        # 处理页面节点（_pages）- 只在非空目录链中间调用时处理
        if '_pages' in tree:
            for page in tree['_pages']:
                bookmark = BookmarkNode(
                    title=f"📄 {page['title']}",
                    page_number=0,
                    level=level,
                    url=page['url']
                )
                bookmarks.append(bookmark)

        # 处理子目录节点（按字母顺序排序）
        for name in sorted(tree.keys()):
            if name == '_pages':
                continue

            subtree = tree[name]
            has_pages = '_pages' in subtree and subtree['_pages']
            subdirs = [k for k in subtree.keys() if k != '_pages']

            # 检查是否是空目录（没有页面）
            if not has_pages and subdirs and is_root:
                # 空目录，递归合并所有空目录
                for subdir_name in sorted(subdirs):
                    combined_name, final_tree, middle_pages = self._get_empty_dir_chain(
                        subtree[subdir_name], f"{name}/{subdir_name}"
                    )
                    # 格式化路径：多层显示为 a/.../d
                    display_name = self._format_path(combined_name)
                    # 创建合并后的目录书签
                    folder_bookmark = BookmarkNode(
                        title=f"📁 {display_name}",
                        page_number=0,
                        level=level,
                        url=None
                    )
                    # 添加中间目录的页面
                    for page in middle_pages:
                        page_bookmark = BookmarkNode(
                            title=f"📄 {page['title']}",
                            page_number=0,
                            level=level + 1,
                            url=page['url']
                        )
                        folder_bookmark.add_child(page_bookmark)
                    # 递归处理最终子树（is_root=False 避免重复处理页面）
                    children = self._tree_to_bookmarks(final_tree, level + 1, is_root=False)
                    for child in children:
                        folder_bookmark.add_child(child)
                    bookmarks.append(folder_bookmark)
            elif not is_root:
                # 空目录链的最终子树处理 - 只处理子目录，不创建新的目录节点
                children = self._tree_to_bookmarks(subtree, level, is_root=True)
                bookmarks.extend(children)
            else:
                # 普通目录处理
                folder_bookmark = BookmarkNode(
                    title=f"📁 {name}",
                    page_number=0,
                    level=level,
                    url=None
                )
                # 递归处理子节点
                children = self._tree_to_bookmarks(subtree, level + 1, is_root=True)
                for child in children:
                    folder_bookmark.add_child(child)
                bookmarks.append(folder_bookmark)

        return bookmarks
