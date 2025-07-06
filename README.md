# Speech2Clip - 语音转文本剪贴板工具

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/lyfe2025/lyfes-tools-speech2clip/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/Status-功能完善-green.svg)]()
[![GitHub Release](https://img.shields.io/github/v/release/lyfe2025/lyfes-tools-speech2clip?include_prereleases)](https://github.com/lyfe2025/lyfes-tools-speech2clip/releases)
[![GitHub Issues](https://img.shields.io/github/issues/lyfe2025/lyfes-tools-speech2clip)](https://github.com/lyfe2025/lyfes-tools-speech2clip/issues)
[![GitHub Stars](https://img.shields.io/github/stars/lyfe2025/lyfes-tools-speech2clip)](https://github.com/lyfe2025/lyfes-tools-speech2clip/stargazers)

---

## 项目简介
Speech2Clip 是一款高效的语音转文本工具，支持多种语音识别引擎（Whisper、Google Speech API），可将语音实时转为文本并自动复制到系统剪贴板，极大提升输入效率。项目采用模块化设计，提供完整的桌面GUI应用和命令行工具。

## 核心功能
- 🎤 **多引擎语音识别** - 支持 Whisper（本地）和 Google（在线）引擎，多语言识别
- 📋 **智能剪贴板管理** - 自动复制识别结果，支持历史记录查看和管理
- 🌏 **多语言支持** - 支持中文简体/繁体、英语、日语、韩语、法语、德语等多种语言
- ⚡ **全局快捷键** - 支持 Ctrl+Shift+R 全局启动语音识别（Windows/Linux使用keyboard库，macOS需授权"辅助功能"权限）
- 🎯 **系统托盘集成** - 支持托盘最小化、右键菜单、双击唤起主界面
- 🔧 **智能配置管理** - 完整的配置系统，支持用户偏好、设备配置、使用统计等
- 🎨 **现代化界面** - 基于PyQt5的卡片式设计，支持实时音频波形显示
- 📊 **Whisper模型管理** - 内置模型下载、查看、删除功能，支持多种模型规格

## 技术栈
- **核心语言**: Python 3.8+
- **语音识别**: OpenAI Whisper（本地）、Google Speech Recognition（在线）
- **音频处理**: PyAudio、SpeechRecognition、librosa、soundfile
- **界面框架**: PyQt5（现代化桌面GUI）
- **剪贴板**: pyperclip（跨平台剪贴板操作）
- **全局热键**: keyboard（Windows/Linux）、QHotkey（跨平台，可选）
- **文本处理**: opencc-python-reimplemented（繁简转换）
- **系统集成**: 系统托盘、通知、文件管理

## 项目结构
```
lyfes-tools-speech2clip/
├── src/                        # 源代码目录
│   ├── gui_main_qt.py          # PyQt5主界面（1200+行，功能完整）
│   ├── speech_recognizer.py    # 语音识别引擎（支持多引擎切换）
│   ├── audio_recorder.py       # 音频录制模块
│   ├── clipboard_manager.py    # 剪贴板管理模块
│   ├── config_manager.py       # 配置管理模块（500+行，功能丰富）
│   ├── tray_manager.py         # 系统托盘管理
│   ├── hotkey_manager.py       # 全局热键管理
│   ├── cli_demo.py             # 命令行演示工具
│   ├── test_modules.py         # 模块测试工具
│   ├── app_icon.png            # 应用图标
│   └── tray_icon.png           # 托盘图标
├── tests/                      # 测试目录
├── requirements.txt            # 核心依赖列表
├── run_gui.sh                  # 智能启动脚本（300行，功能丰富）
└── README.md                   # 项目文档
```

## 快速启动

### 1. 环境准备
建议使用conda或venv虚拟环境：
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 或使用conda
conda create -n speech2clip python=3.11
conda activate speech2clip
```

### 2. 依赖安装
```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装额外依赖（根据需要）
pip install keyboard                    # 全局热键支持
pip install opencc-python-reimplemented # 繁简转换
pip install QHotkey                     # 跨平台热键（可选）
```

### 3. 快速启动
- **推荐方式（智能启动脚本）**：
  ```bash
  bash run_gui.sh
  ```
  启动脚本提供交互式主菜单：
  ```
  ==== Speech2Clip 主菜单 ====
  1. 下载模型（仅显示未下载的）
  2. 查看当前已有模型  
  3. 删除模型
  4. 运行GUI主程序
  5. 退出
  ```
  
- **直接启动GUI**：
  ```bash
  python src/gui_main_qt.py
  ```

- **命令行模式**：
  ```bash
  python src/cli_demo.py [whisper|google] [选项]
  
  # 示例
  python src/cli_demo.py whisper --whisper-model small
  python src/cli_demo.py google --device 1 --list-devices
  ```

## 功能特性详解

### 语音识别引擎
- **Whisper引擎**（推荐）：
  - 本地运行，无需网络，隐私安全
  - 支持模型：tiny, base, small, medium, large, large-v3
  - 自动模型管理（下载、缓存、切换）
  - 多语言支持，识别准确度高
  
- **Google引擎**：
  - 在线识别，需要网络连接
  - 响应速度快，适合实时场景
  - 支持多种语言识别

### 用户界面特性
- **现代化设计**：卡片式布局，圆角边框，渐变按钮
- **实时反馈**：音频波形显示，语音状态指示
- **智能提示**：按钮悬停显示快捷键提示，状态变化实时提示
- **配置管理**：模型选择、语言设置、设备配置
- **历史管理**：识别历史查看，一键复制，会话清理
- **状态显示**：模型状态、麦克风状态实时监控

### 系统集成
- **全局快捷键**：任意界面按 `Ctrl+Shift+R` 开始语音识别，GUI界面提供快捷键提示
- **系统托盘**：最小化到托盘，右键菜单快速操作
- **自动启动**：支持开机自启（通过配置管理）
- **通知提示**：识别完成、错误提示等系统通知

## 配置说明

### 主要配置项
项目使用完整的配置管理系统，配置文件位于 `~/.speech2clip/`：

- **语音识别配置**：引擎选择、语言设置、超时参数
- **音频配置**：采样率、声道数、设备选择、噪声调整
- **界面配置**：主题、语言、窗口大小、透明度
- **快捷键配置**：自定义全局热键组合
- **剪贴板配置**：历史记录数量、自动保存、监控设置

### 语言支持
- 中文：zh-CN（简体）、zh-TW（繁体）
- 英语：en-US、en-GB
- 其他：ja-JP（日语）、ko-KR（韩语）、fr-FR（法语）、de-DE（德语）、es-ES（西班牙语）、ru-RU（俄语）

## 依赖说明

### 核心依赖（requirements.txt）
```
openai-whisper>=20231117    # Whisper语音识别
SpeechRecognition>=3.10.0   # 语音识别框架
pyaudio>=0.2.11             # 音频录制
pyperclip>=1.8.2            # 剪贴板操作
PyQt5>=5.15.10              # GUI框架
librosa>=0.10.1             # 音频处理
soundfile>=0.12.1           # 音频文件处理
numpy>=1.24.3               # 数值计算
matplotlib>=3.7.1           # 可视化（波形显示）
```

### 可选依赖
```bash
# 全局热键支持
pip install keyboard                    # Windows/Linux
pip install QHotkey                     # 跨平台（可选）

# 繁简转换
pip install opencc-python-reimplemented

# 系统增强
pip install psutil                      # 系统信息
pip install plyer                       # 跨平台通知
```

## 使用指南

### 基本使用流程
1. **启动应用**：运行 `bash run_gui.sh` 或直接启动GUI
2. **配置检查**：确认麦克风状态和模型状态为"就绪"
3. **选择配置**：根据需要选择识别引擎、语言、模型
4. **开始说话**：点击"🎤 开始说话"按钮或按快捷键 `Ctrl+Shift+R`
   - 💡 **快捷键提示**：鼠标悬停在按钮上即可查看快捷键提示
5. **查看结果**：识别结果自动复制到剪贴板，可在历史记录查看

### 高级功能
- **批量识别**：命令行模式支持批量音频文件处理
- **自定义模型**：支持加载自定义Whisper模型
- **配置导出**：支持配置备份和恢复
- **使用统计**：记录使用次数、识别字符数等统计信息
- **用户体验**：界面提示优化，鼠标悬停查看操作指南

## 开发状态与进展

### 已完成功能 ✅
- [x] 完整的模块化架构设计
- [x] 多引擎语音识别（Whisper + Google）
- [x] 现代化PyQt5界面（1200+行完整实现）
- [x] 系统托盘和全局热键集成
- [x] 完整的配置管理系统（500+行）
- [x] 智能启动脚本和模型管理
- [x] 音频录制和剪贴板管理
- [x] 多语言支持和繁简转换
- [x] 历史记录管理和数据持久化
- [x] GUI和CLI双模式支持
- [x] 用户体验优化（快捷键提示、状态指示、操作引导）

### 进行中 🔄
- [ ] 完整的单元测试覆盖
- [ ] 性能优化和内存管理
- [ ] 打包发布和自动更新

### 规划中 📋
- [ ] 插件系统和扩展接口
- [ ] 云端同步和多设备支持
- [ ] 更多语音识别引擎集成

## 故障排除

### 常见问题
- **Q: 依赖安装失败？**
  - A: 确保Python版本>=3.8，激活虚拟环境，检查网络连接。macOS可能需要安装Xcode命令行工具。

- **Q: 语音识别无响应？**
  - A: 检查麦克风权限、网络连接（Google引擎），或尝试更换识别引擎。确认模型状态为"就绪"。

- **Q: 全局热键无效？**
  - A: macOS需在"系统设置→隐私与安全性→辅助功能"中授权。Windows/Linux确认keyboard库已安装且无权限冲突。

- **Q: 检测不到麦克风？**
  - A: 确认系统麦克风权限，尝试重启应用或系统。可在CLI模式使用 `--list-devices` 查看可用设备。

- **Q: Whisper模型下载失败？**
  - A: 检查网络连接，或手动下载模型文件到 `~/.cache/whisper/` 目录。

- **Q: Qt字体警告？**
  - A: 已自动适配中文字体（macOS: PingFang SC，Windows: Microsoft YaHei，Linux: WenQuanYi Micro Hei）。

- **Q: 如何快速了解界面操作？**
  - A: 将鼠标悬停在任何按钮上可查看操作提示和快捷键，状态指示器会显示系统就绪状态。

### 调试模式
启动时添加调试参数：
```bash
export DEBUG=1
python src/gui_main_qt.py
```

## 贡献指南
欢迎参与开发！您可以：
1. 🐛 [报告bug和使用问题](https://github.com/lyfe2025/lyfes-tools-speech2clip/issues/new?template=bug_report.md)
2. 💡 [提出新功能建议](https://github.com/lyfe2025/lyfes-tools-speech2clip/issues/new?template=feature_request.md)  
3. 📝 完善文档和使用指南
4. 🔧 提交代码（请遵循[贡献指南](CONTRIBUTING.md)）
5. 🧪 编写测试用例和性能优化

详细的贡献指南请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 开发环境搭建
```bash
# 克隆项目
git clone https://github.com/lyfe2025/lyfes-tools-speech2clip.git
cd lyfes-tools-speech2clip

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 运行项目
python src/gui_main_qt.py
```

## 更新日志
- **2024-12**：完成核心功能开发，模块化重构，GUI界面优化，配置系统完善
- **2024-06**：完成核心模块化重构，支持多引擎、多语言，完善GUI/CLI双模式
- **2024-05**：实现MVP版本，支持基础语音转文本与剪贴板功能
- **2024-04**：项目初始化，完成环境搭建与依赖配置

## 致谢
感谢以下开源项目的支持：
- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的本地语音识别
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Python语音识别框架
- [PyQt5](https://riverbankcomputing.com/software/pyqt/) - 跨平台GUI框架
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Python音频I/O

---

## 📞 技术支持

- **GitHub Issues**: [报告问题](https://github.com/lyfe2025/lyfes-tools-speech2clip/issues) | [功能建议](https://github.com/lyfe2025/lyfes-tools-speech2clip/issues/new?template=feature_request.md)
- **项目主页**: https://github.com/lyfe2025/lyfes-tools-speech2clip
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)

> **编码说明**: 本项目所有文件均采用UTF-8编码，支持完整的中文显示。