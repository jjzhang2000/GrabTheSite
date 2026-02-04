# 文件下载模块

import os
import requests
from urllib.parse import urlparse
from logger import setup_logger

# 获取 logger 实例
logger = setup_logger(__name__)


def download_file(url, output_dir):
    """下载文件并保存到指定目录，保留原网站的目录结构
    
    Args:
        url: 文件URL
        output_dir: 输出目录
    
    Returns:
        str: 下载的文件路径，如果下载失败返回None
    """
    try:
        logger.info(f"下载文件: {url}")
        
        # 解析URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 获取文件名
        filename = os.path.basename(path)
        
        # 如果没有文件名，跳过
        if not filename:
            logger.info(f"跳过，无文件名: {url}")
            return None
        
        # 构建保存路径，保留目录结构
        file_path = os.path.join(output_dir, path.lstrip('/'))
        
        # 创建目录结构
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 下载文件
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()  # 检查HTTP错误
        
        # 保存文件
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"保存文件: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"下载失败: {url}, 错误: {str(e)}")
        return None
