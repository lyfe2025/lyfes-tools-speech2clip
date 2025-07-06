"""
Speech2Clip - 语音转文本剪贴板工具

一款高效的语音转文本工具，支持多种语音识别引擎，
可将语音实时转为文本并自动复制到系统剪贴板。

Author: lyfe2025
License: MIT
"""

__version__ = "1.0.0"
__author__ = "lyfe2025"
__email__ = ""
__license__ = "MIT"
__description__ = "Speech2Clip - 语音转文本剪贴板工具"
__url__ = "https://github.com/lyfe2025/lyfes-tools-speech2clip"

# 项目元信息
PROJECT_NAME = "Speech2Clip"
PROJECT_DESCRIPTION = "语音转文本剪贴板工具"
PROJECT_VERSION = __version__
PROJECT_AUTHOR = __author__
PROJECT_URL = __url__

# 支持的Python版本
PYTHON_REQUIRES = ">=3.8"

# 核心功能模块
__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "__description__",
    "__url__",
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "PROJECT_VERSION",
    "PROJECT_AUTHOR", 
    "PROJECT_URL",
    "PYTHON_REQUIRES"
]

from .tray_manager import TrayManager
from .hotkey_manager import HotkeyManager
