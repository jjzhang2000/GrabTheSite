"""网站保存类 - 已弃用

注意：此类已弃用，请使用 plugins.save_plugin.SavePlugin
保留此文件是为了向后兼容，将在未来版本中移除
"""

import warnings
from plugins.save_plugin import SavePlugin

warnings.warn(
    "SaveSite 类已弃用，请使用 plugins.save_plugin.SavePlugin。"
    "此模块将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2
)


class SaveSite(SavePlugin):
    """网站保存类 - 已弃用
    
    此类是 SavePlugin 的别名，仅用于向后兼容。
    请直接使用 plugins.save_plugin.SavePlugin。
    """
    
    def __init__(self, target_url, output_dir, static_resources):
        """初始化保存器
        
        Args:
            target_url: 目标URL
            output_dir: 输出目录
            static_resources: 已下载的静态资源URL集合
        """
        super().__init__(config=None)
        self.target_url = target_url
        self.output_dir = output_dir
        self.static_resources = static_resources
        
        # 提取并标准化起始目录路径
        from urllib.parse import urlparse
        parsed_target = urlparse(self.target_url)
        self.target_directory = parsed_target.path
        if not self.target_directory.endswith('/'):
            self.target_directory += '/'
        
        import logging
        logging.getLogger(__name__).warning(
            "SaveSite 类已弃用，请使用 SavePlugin"
        )
