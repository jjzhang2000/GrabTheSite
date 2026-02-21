"""PDF 合并器

使用 pypdf 合并多个 PDF 文件并添加书签。
"""

from pypdf import PdfWriter, PdfReader


class PdfMerger:
    """PDF 合并器，使用 pypdf 合并多个 PDF 并添加书签"""

    def __init__(self):
        """初始化 PDF 合并器"""
        self.page_offsets = {}  # URL -> 起始页码映射
        self.total_pages = 0    # 总页数

    def merge_pdfs(self, pdf_files, output_path, bookmark_tree, url_to_page_map):
        """合并 PDF 文件并添加书签

        Args:
            pdf_files: PDF 文件列表，每项为 (url, file_path) 元组
            output_path: 输出文件路径
            bookmark_tree: 书签树（BookmarkNode 列表）
            url_to_page_map: URL 到页码的映射

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
            # 根据 URL 查找对应的页码
            # 这里需要根据实际逻辑来映射 URL 到页码
            for url, page_num in url_to_page_map.items():
                # 简化匹配：检查 URL 是否包含书签标题或反之
                if bookmark.title in url or url in bookmark.title:
                    # 计算在合并后 PDF 中的实际页码
                    offset = self.page_offsets.get(url, 0)
                    bookmark.page_number = offset  # PdfWriter 使用 0-based 页码
                    break

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
