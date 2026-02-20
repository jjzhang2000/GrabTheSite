"""站点地图生成模块"""

import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from logger import setup_logger


def _(message):
    """翻译函数"""
    from utils.i18n import gettext
    return gettext(message)


logger = setup_logger(__name__)


class SitemapGenerator:
    """站点地图生成器，用于生成 HTML 格式的站点地图"""
    
    def __init__(self, target_url, output_dir):
        """初始化站点地图生成器
        
        Args:
            target_url: 目标网站 URL
            output_dir: 输出目录
        """
        self.target_url = target_url
        self.output_dir = output_dir
        self.parsed_target = urlparse(self.target_url)
        self.base_url = f"{self.parsed_target.scheme}://{self.parsed_target.netloc}"
    
    def _extract_title(self, html_content, url):
        """从 HTML 内容中提取页面标题
        
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
        except Exception as e:
            logger.error(_("提取标题失败") + f": {url}, " + _("错误") + f": {str(e)}")
        
        # 如果没有找到标题，使用默认值
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path or path == '/':
            return _('Home')
        
        page_title = os.path.basename(path)
        if not page_title:
            return _('Home')
        elif page_title == 'index.html':
            return os.path.basename(os.path.dirname(path)) or _('Home')
        elif '.' in page_title:
            return page_title.split('.')[0]
        else:
            return page_title
    
    def _get_local_file_path(self, url):
        """获取文件保存路径，保留原网站的目录结构
        
        Args:
            url: 页面 URL
        
        Returns:
            str: 本地文件路径
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 如果路径为空，设置为/
        if not path:
            path = '/'
        
        # 如果路径以/结尾，添加index.html
        if path.endswith('/'):
            path += 'index.html'
        # 如果路径没有文件名，添加index.html
        elif not os.path.basename(path):
            path += 'index.html'
        # 如果路径没有扩展名，添加.html
        elif '.' not in os.path.basename(path):
            path += '.html'
        
        # 构建完整文件路径，保留目录结构
        file_path = os.path.join(self.output_dir, path.lstrip('/'))
        
        return file_path
    
    def _get_relative_path(self, file_path):
        """获取相对于站点地图文件的路径
        
        Args:
            file_path: 本地文件绝对路径
        
        Returns:
            str: 相对于站点地图文件的路径
        """
        sitemap_dir = os.path.dirname(os.path.join(self.output_dir, 'sitemap.html'))
        relative_path = os.path.relpath(file_path, sitemap_dir).replace('\\', '/')
        return relative_path
    
    def _extract_title_from_local_file(self, url):
        """从本地文件中提取页面标题
        
        Args:
            url: 页面 URL
        
        Returns:
            str: 页面标题
        """
        try:
            # 获取本地文件路径
            local_path = self._get_local_file_path(url)
            
            # 尝试读取本地文件内容
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 从 HTML 内容中提取标题
                return self._extract_title(html_content, url)
        except Exception as e:
            logger.error(_("从本地文件提取标题失败") + f": {url}, " + _("错误") + f": {str(e)}")
        
        # 如果读取文件失败或提取标题失败，使用默认值
        parsed_url = urlparse(url)
        path = parsed_url.path
        if not path or path == '/':
            return _('Home')
        
        page_title = os.path.basename(path)
        if not page_title:
            return _('Home')
        elif page_title == 'index.html':
            return os.path.basename(os.path.dirname(path)) or _('Home')
        elif '.' in page_title:
            return page_title.split('.')[0]
        else:
            return page_title
    
    def _build_page_tree(self, pages):
        """构建页面树结构
        
        Args:
            pages: 抓取的页面，可以是字典（键为 URL，值为页面内容）或集合（包含 URL）
        
        Returns:
            dict: 页面树结构
        """
        # 页面树结构
        page_tree = {}
        
        # 处理页面
        if isinstance(pages, dict):
            # 当 pages 是字典时
            for url, html_content in pages.items():
                # 提取页面标题
                page_title = self._extract_title(html_content, url)
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                
                # 提取路径层级
                path_parts = self._extract_path_parts(url)
                
                # 添加到树结构
                self._add_to_tree(page_tree, path_parts, relative_path, page_title)
        elif isinstance(pages, set):
            # 当 pages 是集合时
            for url in pages:
                # 尝试从本地文件中读取页面内容来提取标题
                page_title = self._extract_title_from_local_file(url)
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                
                # 提取路径层级
                path_parts = self._extract_path_parts(url)
                
                # 添加到树结构
                self._add_to_tree(page_tree, path_parts, relative_path, page_title)
        
        return page_tree
    
    def _extract_path_parts(self, url):
        """提取 URL 的路径层级
        
        Args:
            url: 页面 URL
        
        Returns:
            list: 路径层级列表，空列表表示根目录下的页面
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 处理路径
        if not path or path == '/':
            return []
        
        # 分割路径
        path_parts = path.strip('/').split('/')
        
        # 移除空字符串
        path_parts = [part for part in path_parts if part]
        
        # 对于以 index.html 或 index.htm 结尾的路径，移除文件名
        if path_parts:
            last_part = path_parts[-1]
            if last_part in ['index.html', 'index.htm']:
                path_parts = path_parts[:-1]
            # 对于其他带有扩展名的文件，移除文件名，保留目录结构
            elif '.' in last_part:
                path_parts = path_parts[:-1]
        
        return path_parts
    
    def _add_to_tree(self, tree, path_parts, relative_path, page_title):
        """将页面添加到树结构
        
        Args:
            tree: 页面树结构
            path_parts: 路径层级列表
            relative_path: 相对于站点地图文件的路径
            page_title: 页面标题
        """
        current = tree
        
        for i, part in enumerate(path_parts):
            if part not in current:
                current[part] = {}
            
            current = current[part]
        
        # 在叶子节点添加页面信息
        # 确保每个页面只出现一次
        if '_pages' not in current:
            current['_pages'] = []
        
        # 检查页面是否已经存在
        page_exists = False
        for page in current['_pages']:
            if page['path'] == relative_path:
                page_exists = True
                break
        
        # 如果页面不存在，添加到列表中
        if not page_exists:
            current['_pages'].append({
                'path': relative_path,
                'title': page_title
            })
    
    def _generate_tree_html(self, tree, level=0):
        """生成分级的 HTML 列表
        
        Args:
            tree: 页面树结构
            level: 当前层级
        
        Returns:
            str: 分级的 HTML 列表
        """
        html = ''
        
        # 生成缩进字符串
        indent = '    ' * level
        
        # 首先处理页面列表节点（_pages），确保页面在目录前面显示
        if '_pages' in tree:
            pages = tree['_pages']
            for page_info in sorted(pages, key=lambda x: x['title']):
                html += f'{indent}<li><a href="{page_info["path"]}">{page_info["title"]}</a></li>\n'
        
        # 然后处理目录节点
        for node, children in sorted(tree.items()):
            if node == '_pages':
                continue  # 已处理过页面列表
            else:
                # 如果是目录节点，生成子列表
                html += f'{indent}<li><span class="folder">{node}/</span>\n'
                html += f'{indent}    <ul>\n'
                html += self._generate_tree_html(children, level + 1)
                html += f'{indent}    </ul>\n'
                html += f'{indent}</li>\n'
        
        return html

    def generate_html_sitemap(self, pages, page_depths=None):
        """生成 HTML 格式的站点地图

        Args:
            pages: 抓取的页面，可以是字典（键为 URL，值为页面内容）或集合（包含 URL）
            page_depths: 已弃用，保留此参数仅用于向后兼容

        Returns:
            str: 生成的 HTML 站点地图文件路径
        """
        page_tree = self._build_page_tree(pages)

        html_content = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>站点地图</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            color: #333;
        }
        ul {
            list-style-type: none;
            padding-left: 20px;
        }
        ul:first-child {
            padding-left: 0;
        }
        li {
            margin: 5px 0;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .folder {
            font-weight: bold;
            color: #555;
        }
    </style>
</head>
<body>
    <h1>站点地图</h1>
    <ul>
'''
        
        # 使用树结构生成 HTML
        html_content += self._generate_tree_html(page_tree, level=0)
        html_content += """
    </ul>
</body>
</html>
"""
        sitemap_html_path = os.path.join(self.output_dir, 'sitemap.html')
        with open(sitemap_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(_("生成 HTML 站点地图") + f": {sitemap_html_path}")

        return sitemap_html_path