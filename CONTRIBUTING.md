# 贡献指南

感谢您对 Speech2Clip 项目的关注！我们欢迎各种形式的贡献。

## 📋 贡献方式

### 🐛 问题报告
如果您发现了bug或有改进建议：

1. **搜索现有Issues**：确认问题尚未被报告
2. **创建新Issue**：使用清晰的标题和详细描述
3. **提供信息**：
   - 操作系统和版本
   - Python版本
   - 错误复现步骤
   - 预期行为 vs 实际行为
   - 相关的错误日志

### 💡 功能建议
提出新功能想法：

1. **检查现有Issues**：确认功能尚未被建议
2. **详细描述**：说明功能的用途和价值
3. **使用场景**：提供具体的使用案例
4. **技术考虑**：如果有技术想法，请一并提出

### 🔧 代码贡献

#### 开发环境搭建
```bash
# 1. Fork 项目并克隆
git clone https://github.com/YOUR_USERNAME/lyfes-tools-speech2clip.git
cd lyfes-tools-speech2clip

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -e .  # 开发模式安装

# 4. 安装开发依赖
pip install pytest black flake8 mypy

# 5. 验证安装
python src/gui_main_qt.py
```

#### 开发流程
1. **创建分支**：`git checkout -b feature/your-feature-name`
2. **编写代码**：遵循项目编码规范
3. **测试代码**：确保新功能正常工作
4. **提交更改**：编写清晰的提交信息
5. **推送分支**：`git push origin feature/your-feature-name`
6. **创建PR**：详细描述更改内容

#### 代码规范

##### Python编码标准
- 遵循 **PEP 8** 规范
- 使用 **类型注解**（Type Hints）
- 编写 **文档字符串**（Docstrings）
- 保持 **函数和类的单一职责**

##### 命名约定
```python
# 类名：PascalCase
class SpeechRecognizer:
    pass

# 函数和变量：snake_case
def recognize_speech():
    audio_data = None

# 常量：UPPER_SNAKE_CASE
MAX_RECORDING_TIME = 30

# 私有方法：前缀下划线
def _internal_method():
    pass
```

##### 文件组织
- **单文件行数**：建议控制在500行以内
- **模块职责**：每个模块有明确的功能边界
- **导入顺序**：标准库 → 第三方库 → 本地模块

#### 测试要求
```bash
# 运行现有测试
python -m pytest tests/

# 运行特定模块测试
python src/test_modules.py

# 代码质量检查
black src/          # 代码格式化
flake8 src/         # 语法检查
mypy src/           # 类型检查
```

#### Git提交规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

**示例**：
```
feat(speech): add whisper model auto-download

- 实现whisper模型自动下载功能
- 支持tiny到large-v3所有官方模型
- 添加下载进度显示和错误处理

Closes #123
```

## 🏗️ 项目架构

### 核心模块
```
src/
├── gui_main_qt.py          # PyQt5主界面（1200+行）
├── speech_recognizer.py    # 语音识别引擎
├── config_manager.py       # 配置管理（500+行）
├── audio_recorder.py       # 音频录制
├── clipboard_manager.py    # 剪贴板管理
├── tray_manager.py         # 系统托盘
└── hotkey_manager.py       # 全局热键
```

### 设计原则
- **模块化**：高内聚低耦合
- **可扩展性**：易于添加新功能
- **稳定性**：渐进式改进，避免破坏性变更
- **用户体验**：界面友好，操作直观

## 🔍 代码审查标准

### Pull Request要求
- **清晰的标题和描述**
- **关联相关Issues**
- **包含必要的测试**
- **更新相关文档**
- **通过所有CI检查**

### 审查重点
1. **功能正确性**：是否解决了预期问题
2. **代码质量**：是否遵循项目规范
3. **性能影响**：是否引入性能问题
4. **兼容性**：是否影响现有功能
5. **安全性**：是否存在安全隐患

## 📚 开发资源

### 技术文档
- [PyQt5 官方文档](https://doc.qt.io/qtforpython/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [SpeechRecognition](https://github.com/Uberi/speech_recognition)

### 开发工具
- **IDE推荐**：VS Code、PyCharm
- **调试工具**：pdb、PyQt5调试器
- **性能分析**：cProfile、memory_profiler

## 🚀 发布流程

### 版本发布
1. **更新版本号**：`src/__init__.py`
2. **更新CHANGELOG**：记录所有变更
3. **创建发布标签**：`git tag v1.x.x`
4. **推送标签**：`git push origin v1.x.x`
5. **创建GitHub Release**

### 打包分发
```bash
# 创建分发包
python setup.py sdist bdist_wheel

# 上传到PyPI（维护者）
twine upload dist/*
```

## ❓ 获取帮助

### 联系方式
- **GitHub Issues**：报告问题和功能请求
- **GitHub Discussions**：技术讨论和想法交流
- **代码审查**：PR评论中进行技术讨论

### 响应时间
- **Issue响应**：通常1-3个工作日
- **PR审查**：通常2-5个工作日
- **紧急问题**：会优先处理

## 🎯 项目愿景

我们致力于创建一个：
- **易用**：界面友好，操作简单
- **可靠**：稳定运行，错误恢复
- **高效**：性能优秀，资源友好
- **开放**：社区驱动，持续改进

感谢您的贡献！让我们一起把 Speech2Clip 做得更好！ 🎉

---
*最后更新：2024年12月27日* 