"""站点地图生成模块

生成XML和HTML格式的站点地图：
- 从页面内容提取标题
- 构建页面树结构
- 支持多语言标题
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from logger import setup_logger
from utils.i18n import gettext as _

# 获取 logger 实例
logger = setup_logger(__name__)


class SitemapGenerator:
    """站点地图生成器，用于生成 XML 格式的站点地图"""
    
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
            logger.error(f"提取标题失败: {url}, 错误: {str(e)}")
        
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
            logger.error(f"从本地文件提取标题失败: {url}, 错误: {str(e)}")
        
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
            list: 路径层级列表
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 处理路径
        if not path or path == '/':
            return ['']
        
        # 分割路径
        path_parts = path.strip('/').split('/')
        
        # 移除空字符串
        path_parts = [part for part in path_parts if part]
        
        # 对于以 index.html 或 index.htm 结尾的路径，移除文件名
        if path_parts:
            last_part = path_parts[-1]
            if last_part in ['index.html', 'index.htm']:
                path_parts = path_parts[:-1]
            # 对于其他带有扩展名的文件，移除文件名
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
        indent = '        ' * level
        
        # 对节点进行排序
        for node, children in sorted(tree.items()):
            if node == '_pages':
                # 如果是页面列表节点，生成每个页面的链接
                for page_info in sorted(children, key=lambda x: x['title']):
                    html += f'{indent}<li><a href="{page_info["path"]}">{page_info["title"]}</a></li>\n'
            else:
                # 特殊处理根路径
                if node == '':
                    # 如果是根路径节点，直接生成其子节点的内容
                    html += self._generate_tree_html(children, level)
                else:
                    # 如果是目录节点，生成子列表
                    html += f'{indent}<li>{node}\n'
                    html += f'{indent}    <ul>\n'
                    html += self._generate_tree_html(children, level + 1)
                    html += f'{indent}    </ul>\n'
                    html += f'{indent}</li>\n'
        
        return html
    
    def generate_sitemap(self, pages):
        """生成站点地图
        
        Args:
            pages: 抓取的页面，可以是字典（键为 URL，值为页面内容）或集合（包含 URL）
        
        Returns:
            str: 生成的站点地图文件路径
        """
        # 创建站点地图根元素
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # 为每个页面创建 URL 元素
        if isinstance(pages, dict):
            # 当 pages 是字典时，使用本地文件路径
            for url, html_content in pages.items():
                url_elem = ET.SubElement(urlset, 'url')
                loc_elem = ET.SubElement(url_elem, 'loc')
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                loc_elem.text = relative_path
                
                # 添加最后修改时间
                lastmod_elem = ET.SubElement(url_elem, 'lastmod')
                lastmod_elem.text = datetime.now().strftime('%Y-%m-%d')
                
                # 添加更改频率
                changefreq_elem = ET.SubElement(url_elem, 'changefreq')
                changefreq_elem.text = 'weekly'
                
                # 添加优先级
                priority_elem = ET.SubElement(url_elem, 'priority')
                priority_elem.text = '0.5'
        elif isinstance(pages, set):
            # 当 pages 是集合时，为每个 URL 计算本地文件路径
            for url in pages:
                url_elem = ET.SubElement(urlset, 'url')
                loc_elem = ET.SubElement(url_elem, 'loc')
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                loc_elem.text = relative_path
                
                # 添加最后修改时间
                lastmod_elem = ET.SubElement(url_elem, 'lastmod')
                lastmod_elem.text = datetime.now().strftime('%Y-%m-%d')
                
                # 添加更改频率
                changefreq_elem = ET.SubElement(url_elem, 'changefreq')
                changefreq_elem.text = 'weekly'
                
                # 添加优先级
                priority_elem = ET.SubElement(url_elem, 'priority')
                priority_elem.text = '0.5'
        
        # 创建 ElementTree 对象
        tree = ET.ElementTree(urlset)
        
        # 生成站点地图文件路径
        sitemap_path = os.path.join(self.output_dir, 'sitemap.xml')
        
        # 写入文件
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"生成站点地图: {sitemap_path}")
        
        return sitemap_path
    
    def generate_html_sitemap(self, pages):
        """生成 HTML 格式的站点地图
        
        Args:
            pages: 抓取的页面，可以是字典（键为 URL，值为页面内容）或集合（包含 URL）
        
        Returns:
            str: 生成的 HTML 站点地图文件路径
        """
        # 创建 HTML 内容
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
            padding: 0;
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
    </style>
</head>
<body>
    <h1>站点地图</h1>
    <ul>
'''
        
        # 按照下载顺序添加页面链接
        if isinstance(pages, dict):
            # 当 pages 是字典时，按照字典的顺序（下载顺序）遍历
            for url, html_content_page in pages.items():
                # 提取页面标题
                page_title = self._extract_title(html_content_page, url)
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                
                html_content += f'        <li><a href="{relative_path}">{page_title}</a></li>\n'
        elif isinstance(pages, set):
            # 当 pages 是集合时，按照字母顺序排序（集合本身无序）
            for url in sorted(pages):
                # 尝试从本地文件中读取页面内容来提取标题
                page_title = self._extract_title_from_local_file(url)
                
                # 获取本地文件路径
                local_path = self._get_local_file_path(url)
                # 获取相对于站点地图文件的路径
                relative_path = self._get_relative_path(local_path)
                
                html_content += f'        <li><a href="{relative_path}">{page_title}</a></li>\n'

        
        # 闭合 HTML 标签
        html_content += """
    </ul>
</body>
</html>
"""
        
        # 生成 HTML 站点地图文件路径
        sitemap_html_path = os.path.join(self.output_dir, 'sitemap.html')
        
        # 写入文件
        with open(sitemap_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"生成 HTML 站点地图: {sitemap_html_path}")
        
        return sitemap_html_path