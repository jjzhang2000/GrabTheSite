"""PDF 合并器

使用 pypdf 合并多个 PDF 文件并添加书签。
内部链接已在生成时移除，外部链接由 Playwright 正确保留。
"""

from pypdf import PdfWriter, PdfReader


class PdfMerger:
    """PDF 合并器，使用 pypdf 合并多个 PDF 并添加书签"""

    def __init__(self):
        """初始化 PDF 合并器"""
        self.page_offsets = {}  # URL -> 起始页码映射
        self.total_pages = 0    # 总页数

    def merge_pdfs(self, pdf_files, output_path, bookmark_tree, url_to_page_map, page_links_info=None):
        """合并 PDF 文件并添加书签

        Args:
            pdf_files: PDF 文件列表，每项为 (url, file_path) 元组
            output_path: 输出文件路径
            bookmark_tree: 书签树（BookmarkNode 列表）
            url_to_page_map: URL 到页码的映射
            page_links_info: 保留参数兼容性，不使用

        Returns:
            str: 输出文件路径

        Raises:
            Exception: 当合并失败时抛出
        """
        writer = PdfWriter()

        # 第一步：合并所有 PDF，记录每个文件的起始页码
        self.page_offsets = {}
        self.total_pages = 0

        for url, file_path in pdf_files:
            self.page_offsets[url] = self.total_pages

            # 读取 PDF 并追加到 writer
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            # 追加所有页面到 writer
            for page in reader.pages:
                writer.add_page(page)

            self.total_pages += num_pages

        # 第二步：更新书签树中的页码
        self._update_bookmark_pages(bookmark_tree, url_to_page_map)

        # 第三步：添加层级书签到 PDF
        self._add_bookmarks_to_writer(writer, bookmark_tree)

        # 设置书签默认展开（尝试修改 Count 属性）
        self._set_bookmark_expanded(writer)

        # 第四步：写入输出文件
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    def _update_bookmark_pages(self, bookmarks, url_to_page_map):
        """更新书签树中每个节点的实际页码

        Args:
            bookmarks: BookmarkNode 列表
            url_to_page_map: URL -> PDF页码 映射
        """
        for bookmark in bookmarks:
            # 如果书签有 URL，直接使用 URL 查找页码
            if bookmark.url and bookmark.url in url_to_page_map:
                page_num = url_to_page_map[bookmark.url]
                # 计算在合并后 PDF 中的实际页码
                offset = self.page_offsets.get(bookmark.url, 0)
                bookmark.page_number = offset  # PdfWriter 使用 0-based 页码
            # 递归处理子书签
            if bookmark.children:
                self._update_bookmark_pages(bookmark.children, url_to_page_map)

    def _add_bookmarks_to_writer(self, writer, bookmarks, parent_bookmark=None):
        """递归添加书签到 PDF Writer

        Args:
            writer: PdfWriter 实例
            bookmarks: BookmarkNode 列表
            parent_bookmark: 父书签对象（用于构建层级）
        """
        for bookmark in bookmarks:
            # 使用 add_outline_item 添加书签
            # page_number 是 0-based 索引
            page_number = bookmark.page_number if bookmark.page_number >= 0 else 0

            current = writer.add_outline_item(
                title=bookmark.title,
                page_number=page_number,
                parent=parent_bookmark
            )

            # 递归添加子书签
            if bookmark.children:
                self._add_bookmarks_to_writer(writer, bookmark.children, current)

    def _set_bookmark_expanded(self, writer):
        """设置所有书签默认展开

        通过修改 Outlines 字典中的 Count 属性。
        注意：PDF 阅读器可能不遵守此设置。

        Args:
            writer: PdfWriter 实例
        """
        # 获取文档的 Catalog
        if hasattr(writer, '_root_object') and '/Outlines' in writer._root_object:
            outlines = writer._root_object['/Outlines']
            if outlines:
                outlines_obj = outlines.get_object()
                self._update_outline_count(outlines_obj)

    def _update_outline_count(self, outline_obj):
        """递归更新书签的 Count 属性

        Args:
            outline_obj: 书签字典对象
        """
        from pypdf.generic import NameObject, NumberObject

        if not outline_obj:
            return

        # 获取子书签数量
        kids = outline_obj.get('/Kids', [])
        if kids:
            # 设置 Count 为正数，表示展开
            count = len(kids)
            outline_obj[NameObject('/Count')] = NumberObject(count)

            # 递归处理子书签
            for kid in kids:
                kid_obj = kid.get_object()
                self._update_outline_count(kid_obj)
