#!/usr/bin/env python3
"""
Speech2Clip 安装配置
"""

import os
import sys
from setuptools import setup, find_packages

# 确保当前目录在Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src import __version__, __author__, __description__, __url__
except ImportError:
    __version__ = "1.0.0"
    __author__ = "lyfe2025"
    __description__ = "Speech2Clip - 语音转文本剪贴板工具"
    __url__ = "https://github.com/lyfe2025/lyfes-tools-speech2clip"

# 读取 README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取 requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="speech2clip",
    version=__version__,
    author=__author__,
    description=__description__,
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url=__url__,
    project_urls={
        "Bug Reports": "https://github.com/lyfe2025/lyfes-tools-speech2clip/issues",
        "Source": "https://github.com/lyfe2025/lyfes-tools-speech2clip",
        "Documentation": "https://github.com/lyfe2025/lyfes-tools-speech2clip/blob/main/README.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=0.991",
        ],
        "full": [
            "keyboard>=0.13.5",
            "opencc-python-reimplemented>=0.1.7",
            "QHotkey",
            "psutil",
            "plyer",
        ],
    },
    entry_points={
        "console_scripts": [
            "speech2clip=gui_main_qt:main",
            "speech2clip-cli=cli_demo:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.png", "*.ico", "*.md", "*.txt"],
    },
    keywords="speech recognition voice text clipboard whisper google audio",
    zip_safe=False,
) 