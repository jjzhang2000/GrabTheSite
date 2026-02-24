"""CLI 模块

提供命令行接口的基类和实现。
"""

__version__ = "0.1.0"

from .base_cli import BaseCLI, main

__all__ = ["BaseCLI", "main"]
