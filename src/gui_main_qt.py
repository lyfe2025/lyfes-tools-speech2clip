import sys
import os
import time
import traceback
import glob
import platform
import json
from datetime import datetime
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC_DIR)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QListWidget, QMessageBox, QHBoxLayout, QSizePolicy, QComboBox, QStyledItemDelegate, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QCoreApplication, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QIcon, QPen, QPixmap
import threading
import numpy as np
import pathlib
try:
    from speech_recognizer import SpeechRecognizer, RecognitionEngine
except ImportError:
    SpeechRecognizer = None
    RecognitionEngine = None
try:
    from clipboard_manager import set_clipboard_text
except ImportError:
    set_clipboard_text = None
from tray_manager import TrayManager
from hotkey_manager import HotkeyManager
# QHotkey全局热键支持
try:
    from qhotkey import QHotkey
except ImportError:
    QHotkey = None

def to_simplified(text):
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')
        result = cc.convert(text)
        print(f'[DEBUG] opencc转换: {text} -> {result}')
        return result
    except Exception as e:
        print(f'[WARN] opencc不可用，未转简体: {e}')
        # 用主线程弹窗
        def show_opencc_warning():
            try:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None, 'opencc未安装', '未安装opencc，无法自动转简体，请执行：python3 -m pip install opencc')
            except:
                pass
        QTimer.singleShot(0, show_opencc_warning)
        return text
try:
    import pyaudio
    import wave
except ImportError:
    pyaudio = None
    wave = None

class WaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0
        self.setMinimumHeight(40)
        self.setMaximumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    def setLevel(self, level):
        self.level = level
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        bar_count = 32
        bar_w = w // bar_count
        for i in range(bar_count):
            rel = abs(i - bar_count/2) / (bar_count/2)
            bar_h = int((1-rel**2) * self.level * h * 0.8 + 6)
            x = i * bar_w + 2
            y = h//2 - bar_h//2
            painter.setBrush(QBrush(QColor('#4a90e2')))
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.drawRect(x, y, bar_w-3, bar_h)

class CenteredComboDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter  # type: ignore

class CardWidget(QFrame):
    """卡片式容器组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet('''
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        ''')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

class Speech2ClipGUI(QWidget):
    recognitionFinished = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle(to_simplified('Speech2Clip 语音转文字'))
        self.setFixedWidth(520)
        self.setMinimumHeight(650)
        self.setStyleSheet('''
            QWidget {
                background: #f8f9fa;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            }
        ''')
        self.is_recording = False
        self.audio_frames = []
        self.history = []
        self.max_history = 10
        self.audio_level = 0
        self.record_thread = None
        self.local_models = self.get_local_models()
        
        # 历史记录文件路径
        self.history_file = os.path.expanduser("~/.speech2clip_history.json")
        
        self.init_data()
        self.load_history()  # 加载历史记录
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(50)
        self.recognitionFinished.connect(self.after_recognition)
        self.init_hotkey()
        self.flash_timer = None
        self.flash_state = True
    def init_data(self):
        self.model_status = '未就绪'
        self.mic_status = '未连接'
        self.progress = 0
        self.result_text = ''
        self.history_expanded = False
        self.current_model = None
    def get_local_models(self):
        # 扫描所有常见whisper模型缓存目录下的.pt文件
        model_dirs = [os.path.expanduser('~/.cache/whisper'), os.path.expanduser('~/.cache/whisper/models')]
        found = set()
        for d in model_dirs:
            if os.path.isdir(d):
                for f in glob.glob(os.path.join(d, '*.pt')):
                    name = os.path.basename(f).replace('.pt', '')
                    found.add(name)
        # 保持常用顺序
        order = ['tiny', 'base', 'small', 'medium', 'large', 'large-v3']
        ordered = [m for m in order if m in found]
        # 追加其它自定义模型
        ordered += sorted(found - set(order))
        return ordered
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 配置和状态卡片
        self.build_config_card(main_layout)
        
        # 主要功能卡片
        self.build_main_card(main_layout)
        
        # 历史记录卡片
        self.build_history_card(main_layout)
        
        # 底部操作区域
        self.build_bottom_area(main_layout)
        
        self.setLayout(main_layout)
        self.update_model_desc()
        if not self.model_map:
            self.record_btn.setEnabled(False)
            self.current_model = None
        else:
            self.current_model = self.model_map[self.model_combo.currentIndex()]['key']
        if self.current_model:
            self.check_model_status(self.current_model)
        self.update_mic_status()
        
        # 确保UI完全初始化后再更新历史记录显示
        QTimer.singleShot(100, self.update_history)
        
        # 额外保障：如果有历史记录，再次确保显示
        if self.history:
            QTimer.singleShot(500, self.force_update_history)
    def build_config_card(self, layout):
        """配置和状态卡片"""
        FONT_FAMILY = self.get_default_chinese_font()
        
        card = CardWidget()
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        
        # 模型配置部分
        model_section = QHBoxLayout()
        model_section.setSpacing(12)
        
        model_label = QLabel(to_simplified('模型：'))
        model_label.setFont(QFont(FONT_FAMILY, 13, QFont.Bold))
        model_label.setStyleSheet('color: #2c3e50; border: none;')
        model_section.addWidget(model_label)
        
        # 初始化模型映射
        self.model_map = []
        model_desc_dict = {
            'tiny':    'Whisper官方tiny模型，速度最快，适合实时转写，精度较低',
            'base':    'Whisper官方base模型，速度快，适合日常语音转写，精度适中',
            'small':   'Whisper官方small模型，精度较高，适合大部分场景',
            'medium':  'Whisper官方medium模型，精度高，适合高质量转写',
            'large':   'Whisper官方large模型，精度最高，速度最慢，需较大内存',
            'large-v3':'Whisper官方large-v3模型，多语种，极致精度，资源需求高',
        }
        for m in self.local_models:
            self.model_map.append({'key': m, 'label': m, 'desc': model_desc_dict.get(m, f'{m} (自定义模型)')})
        
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont(FONT_FAMILY, 13))
        self.model_combo.setFixedHeight(36)
        self.model_combo.setMinimumWidth(120)
        self.model_combo.setStyleSheet('''
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 8px 35px 8px 12px;
                color: #2c3e50;
                font-weight: 500;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QComboBox:focus {
                border-color: #007bff;
                background-color: #ffffff;
                outline: none;
            }
            QComboBox:on {
                border-color: #007bff;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background-color: transparent;
            }
            QComboBox::drop-down:hover {
                background-color: rgba(0, 123, 255, 0.08);
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                background-color: #6c757d;
                border: none;
                margin: 2px;
            }
            QComboBox::down-arrow:hover {
                background-color: #007bff;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: none;
                outline: none;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QComboBox QAbstractItemView::item {
                background-color: transparent;
                border: none;
                padding: 8px 12px;
                color: #2c3e50;
                font-weight: 500;
                min-height: 25px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e7f3ff;
                color: #007bff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #007bff;
                color: white;
            }
        ''')
        

        self.model_combo.setItemDelegate(CenteredComboDelegate(self.model_combo))
        for m in self.model_map:
            self.model_combo.addItem(m['label'], m['key'])
        if self.model_map:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.setToolTip(to_simplified('仅显示本地已下载模型，选择后可立即使用'))
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        

        model_section.addWidget(self.model_combo)
        model_section.addStretch(1)
        
        card_layout.addLayout(model_section)
        
        # 模型描述
        self.model_desc_label = QLabel()
        self.model_desc_label.setFont(QFont(FONT_FAMILY, 11))
        self.model_desc_label.setStyleSheet('color: #6c757d; margin-left: 2px; margin-bottom: 4px; border: none;')
        self.model_desc_label.setWordWrap(True)
        card_layout.addWidget(self.model_desc_label)
        
        # 状态部分
        status_section = QHBoxLayout()
        status_section.setSpacing(16)
        
        status_title = QLabel(to_simplified('状态：'))
        status_title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        status_title.setStyleSheet('color: #2c3e50; border: none;')
        status_section.addWidget(status_title)
        
        # 模型状态
        self.model_status_icon = QLabel()
        self.model_status_icon.setFixedSize(12, 12)
        self.model_status_icon.setStyleSheet('border: none; background: transparent;')
        self.model_status_icon.setPixmap(self.create_status_dot('#28a745'))
        status_section.addWidget(self.model_status_icon)
        
        self.model_status_label = QLabel(to_simplified('模型已就绪'))
        self.model_status_label.setFont(QFont(FONT_FAMILY, 11))
        self.model_status_label.setStyleSheet('color: #28a745; font-weight: 500; border: none;')
        status_section.addWidget(self.model_status_label)
        
        # 麦克风状态
        self.mic_status_icon = QLabel()
        self.mic_status_icon.setFixedSize(12, 12)
        self.mic_status_icon.setStyleSheet('border: none; background: transparent;')
        self.mic_status_icon.setPixmap(self.create_status_dot('#dc3545'))
        status_section.addWidget(self.mic_status_icon)
        
        self.mic_status_label = QLabel(to_simplified('未检测到麦克风'))
        self.mic_status_label.setFont(QFont(FONT_FAMILY, 11))
        self.mic_status_label.setStyleSheet('color: #dc3545; font-weight: 500; border: none;')
        status_section.addWidget(self.mic_status_label)
        
        # 刷新按钮
        self.refresh_mic_btn = QPushButton(to_simplified('刷新'))
        self.refresh_mic_btn.setFont(QFont(FONT_FAMILY, 10))
        self.refresh_mic_btn.setFixedSize(60, 28)
        self.refresh_mic_btn.setStyleSheet('''
            QPushButton {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #0056b3;
            }
            QPushButton:pressed {
                background: #004085;
            }
        ''')
        self.refresh_mic_btn.clicked.connect(self.update_mic_status)
        status_section.addWidget(self.refresh_mic_btn)
        
        status_section.addStretch(1)
        card_layout.addLayout(status_section)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
    def build_main_card(self, layout):
        """主要功能卡片：语音转文字"""
        FONT_FAMILY = self.get_default_chinese_font()
        
        card = CardWidget()
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        
        # 标题
        title_label = QLabel(to_simplified('语音转文字'))
        title_label.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        title_label.setStyleSheet('color: #2c3e50; margin-bottom: 4px; border: none;')
        card_layout.addWidget(title_label)
        
        # 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont(FONT_FAMILY, 14))
        self.result_text.setReadOnly(True)
        self.result_text.setFixedHeight(120)
        self.result_text.setStyleSheet('''
            QTextEdit {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                color: #495057;
                selection-background-color: #007bff;
            }
            QTextEdit:focus {
                border-color: #007bff;
                background: white;
            }
            /* 自定义滚动条样式 */
            QScrollBar:vertical {
                background: rgba(233, 236, 239, 0.5);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(108, 117, 125, 0.6);
                border-radius: 4px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 123, 255, 0.7);
            }
            QScrollBar::handle:vertical:pressed {
                background: #007bff;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: transparent;
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: rgba(233, 236, 239, 0.5);
                height: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: rgba(108, 117, 125, 0.6);
                border-radius: 4px;
                min-width: 20px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 123, 255, 0.7);
            }
            QScrollBar::handle:horizontal:pressed {
                background: #007bff;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: transparent;
                width: 0px;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        ''')
        self.result_text.setPlaceholderText(to_simplified('点击"开始说话"按钮开始语音转文字...'))
        card_layout.addWidget(self.result_text)
        
        # 状态信息 - 改为浮动提示，不占用卡片空间
        self.copy_status_label = QLabel("")
        self.copy_status_label.setFont(QFont(FONT_FAMILY, 11))
        self.copy_status_label.setStyleSheet('''
            QLabel {
                background: rgba(40, 167, 69, 0.9);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 500;
            }
        ''')
        self.copy_status_label.setAlignment(Qt.AlignCenter)
        self.copy_status_label.setVisible(False)  # 默认隐藏
        self.copy_status_label.setParent(self)   # 直接设置为主窗口的子控件，实现浮动效果
        
        # 波形动画区域
        self.wave_widget = WaveWidget()
        card_layout.addWidget(self.wave_widget)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
    def build_history_card(self, layout):
        """历史记录卡片"""
        FONT_FAMILY = self.get_default_chinese_font()
        
        card = CardWidget()
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        
        # 标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        history_label = QLabel(to_simplified('历史记录'))
        history_label.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        history_label.setStyleSheet('color: #2c3e50; border: none;')
        header_layout.addWidget(history_label)
        
        header_layout.addStretch(1)
        
        # 展开/收起按钮
        self.expand_history_btn = QPushButton(to_simplified('展开历史'))
        self.expand_history_btn.setFont(QFont(FONT_FAMILY, 10))
        self.expand_history_btn.setFixedSize(80, 30)
        self.expand_history_btn.setStyleSheet('''
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #545b62;
            }
            QPushButton:pressed {
                background: #495057;
            }
        ''')
        self.expand_history_btn.clicked.connect(self.toggle_history_expanded)
        header_layout.addWidget(self.expand_history_btn)
        
        # 清空历史按钮
        self.clear_history_btn = QPushButton(to_simplified('清空历史'))
        self.clear_history_btn.setFont(QFont(FONT_FAMILY, 10))
        self.clear_history_btn.setFixedSize(80, 30)
        self.clear_history_btn.setStyleSheet('''
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #c82333;
            }
            QPushButton:pressed {
                background: #bd2130;
            }
        ''')
        self.clear_history_btn.clicked.connect(self.clear_history_session)
        header_layout.addWidget(self.clear_history_btn)
        
        card_layout.addLayout(header_layout)
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setFont(QFont(FONT_FAMILY, 12))
        self.history_list.setFixedHeight(100)
        self.history_list.setStyleSheet('''
            QListWidget {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
                background: transparent;
            }
            QListWidget::item:hover {
                background: #e9ecef;
            }
            QListWidget::item:selected {
                background: #007bff;
                color: white;
            }
            /* 自定义滚动条样式 */
            QScrollBar:vertical {
                background: rgba(233, 236, 239, 0.5);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(108, 117, 125, 0.6);
                border-radius: 4px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 123, 255, 0.7);
            }
            QScrollBar::handle:vertical:pressed {
                background: #007bff;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: transparent;
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: rgba(233, 236, 239, 0.5);
                height: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: rgba(108, 117, 125, 0.6);
                border-radius: 4px;
                min-width: 20px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 123, 255, 0.7);
            }
            QScrollBar::handle:horizontal:pressed {
                background: #007bff;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: transparent;
                width: 0px;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        ''')
        self.history_list.itemClicked.connect(self.on_history_click)
        card_layout.addWidget(self.history_list)
        
        card.setLayout(card_layout)
        layout.addWidget(card)
        
        # 初始化历史记录状态
        self.update_history_collapsed()
    def build_bottom_area(self, layout):
        """底部操作区域"""
        FONT_FAMILY = self.get_default_chinese_font()
        
        # 添加一些间距
        layout.addSpacing(8)
        
        self.record_btn = QPushButton(to_simplified('开始说话'))
        self.record_btn.setFont(QFont(FONT_FAMILY, 18, QFont.Bold))
        self.record_btn.setMinimumHeight(64)
        self.record_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-weight: bold;
                padding: 16px 0;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
        ''')
        self.record_btn.clicked.connect(self.toggle_recording)
        # 添加快捷键提示
        self.record_btn.setToolTip(to_simplified('快捷键: Ctrl+Shift+R'))
        layout.addWidget(self.record_btn)
    def get_default_chinese_font(self):
        system = platform.system()
        if system == "Darwin":
            return "PingFang SC"
        elif system == "Windows":
            return "Microsoft YaHei"
        else:
            return "WenQuanYi Micro Hei"
    def update_model_desc(self):
        if not self.model_map:
            self.model_desc_label.setText('未检测到本地whisper模型')
            return
        idx = self.model_combo.currentIndex()
        desc = self.model_map[idx]['desc']
        # 只保留'-'后面的中文说明
        if ' - ' in desc:
            desc = desc.split(' - ', 1)[-1]
        self.model_desc_label.setText(to_simplified(desc))
    def on_model_changed(self, idx_or_text):
        if not self.model_map:
            return
        idx = self.model_combo.currentIndex()
        self.current_model = self.model_map[idx]['key']
        self.update_model_desc()
        self.check_model_status(self.current_model)
    def toggle_recording(self):
        if not pyaudio or not wave:
            self.run_on_main(lambda: QMessageBox.critical(self, to_simplified('错误'), to_simplified('未安装 pyaudio 或 wave，无法录音。')))
            return
        if self.is_recording:
            self.is_recording = False
            self.run_on_main(lambda: self.update_record_btn_ui(False))
            self.model_combo.setEnabled(True)
            self.stop_record_animation()
        else:
            self.is_recording = True
            self.audio_frames = []
            self.run_on_main(lambda: self.update_record_btn_ui(True))
            if hasattr(self, 'result_text') and isinstance(self.result_text, QTextEdit):
                self.result_text.clear()
            self.model_combo.setEnabled(False)
            self.start_record_animation()
            threading.Thread(target=self.record_audio, daemon=True).start()
    def update_record_btn_ui(self, is_recording):
        if is_recording:
            self.record_btn.setText(to_simplified('停止说话'))
            self.record_btn.setToolTip(to_simplified('正在录音中，点击停止\n快捷键: Ctrl+Shift+R'))
            self.record_btn.setStyleSheet('''
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333);
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 16px 0;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c82333, stop:1 #bd2130);
                }
                QPushButton:pressed {
                    background: #bd2130;
                }
                QPushButton:disabled {
                    background: #6c757d;
                    color: #adb5bd;
                }
            ''')
        else:
            self.record_btn.setText(to_simplified('开始说话'))
            self.record_btn.setToolTip(to_simplified('点击开始语音识别\n快捷键: Ctrl+Shift+R'))
            self.record_btn.setStyleSheet('''
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 16px 0;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
                }
                QPushButton:pressed {
                    background: #004085;
                }
                QPushButton:disabled {
                    background: #6c757d;
                    color: #adb5bd;
                }
            ''')
    def start_record_animation(self):
        if self.flash_timer is not None:
            self.flash_timer.stop()
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.toggle_record_btn_flash)
        self.flash_state = True
        self.flash_timer.start(400)
    def stop_record_animation(self):
        if self.flash_timer is not None:
            self.flash_timer.stop()
            self.flash_timer = None
        self.record_btn.setWindowOpacity(1.0)
    def toggle_record_btn_flash(self):
        if self.flash_state:
            self.record_btn.setWindowOpacity(0.7)
        else:
            self.record_btn.setWindowOpacity(1.0)
        self.flash_state = not self.flash_state
    def record_audio(self):
        if not pyaudio or not hasattr(pyaudio, 'PyAudio'):
            return
        pa = pyaudio.PyAudio()
        # 新增：检测输入设备
        try:
            input_info = pa.get_default_input_device_info()
        except Exception:
            self.run_on_main(lambda: QMessageBox.critical(self, '错误', '未检测到可用的麦克风输入设备，请检查系统音频设置。'))
            pa.terminate()
            return
        # 新增：检测输出设备
        try:
            output_info = pa.get_default_output_device_info()
        except Exception:
            self.run_on_main(lambda: QMessageBox.critical(self, '错误', '未检测到可用的音频输出设备，请检查系统音频设置。'))
            pa.terminate()
            return
        if not hasattr(pyaudio, 'paInt16'):
            return
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        self.audio_level = 0
        start_time = time.time()
        silence_count = 0
        max_silence = 5
        max_duration = 15
        while self.is_recording:
            data = stream.read(1024, exception_on_overflow=False)
            self.audio_frames.append(data)
            audio_np = np.frombuffer(data, dtype=np.int16)
            level = np.abs(audio_np).mean() / 32768
            self.audio_level = min(level * 10, 1.0)
            if level < 0.01:
                silence_count += 1
            else:
                silence_count = 0
            if silence_count > (max_silence * 16000 // 1024):
                break
            if time.time() - start_time > max_duration:
                break
        self.is_recording = False
        stream.stop_stream()
        stream.close()
        pa.terminate()
        self.run_on_main(self.on_record_finish)
    def on_record_finish(self):
        print('[DEBUG] on_record_finish called')
        self.run_on_main(lambda: self.update_record_btn_ui(False))
        self.stop_record_animation()
        if not self.audio_frames or not wave:
            print('[DEBUG] No valid audio frames')
            self.run_on_main(lambda: QMessageBox.information(self, '提示', '未检测到有效录音内容。'))
            return
        wav_path = 'temp_record.wav'
        wf = wave.open(wav_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
        print(f'[DEBUG] Audio saved to {wav_path}, start recognition')
        if hasattr(self, 'result_text') and isinstance(self.result_text, QTextEdit):
            self.run_on_main(lambda: self.result_text.setPlainText('正在识别，请稍候...'))
        threading.Thread(target=self.do_recognition, args=(wav_path,), daemon=True).start()
    def do_recognition(self, wav_path):
        print(f'[DEBUG] do_recognition called with {wav_path}')
        try:
            if SpeechRecognizer is None or RecognitionEngine is None:
                raise RuntimeError('未找到 speech_recognizer 模块！')
            recognizer = SpeechRecognizer()
            recognizer.current_engine = RecognitionEngine.WHISPER
            recognizer.engine_configs[RecognitionEngine.WHISPER]['model'] = self.current_model
            print(f'[DEBUG] Start recognize_from_file, model={self.current_model}')
            text, confidence = recognizer.recognize_from_file(wav_path)
            print(f'[DEBUG] Recognition result: {text}')
            text_simp = to_simplified(text)
            os.remove(wav_path)
            self.recognitionFinished.emit(text_simp)
        except Exception as e:
            import traceback
            print('[ERROR] Exception in do_recognition:')
            traceback.print_exc()
            self.run_on_main(lambda: self.recognitionFinished.emit(f'[识别失败] {str(e)}'))
    def show_result(self, text):
        text = to_simplified(text)
        if hasattr(self, 'result_text') and isinstance(self.result_text, QTextEdit):
            self.run_on_main(lambda: self.result_text.setPlainText(text if text else ""))
        QApplication.processEvents()
    def update_wave(self):
        if self.is_recording:
            level = self.audio_level
        else:
            level = 0.05
        self.run_on_main(lambda: self.wave_widget.setLevel(level))
    def update_history_collapsed(self):
        if callable(getattr(self, 'run_on_main', None)):
            self.run_on_main(self._update_history_collapsed_main)
        elif callable(getattr(self, '_update_history_collapsed_main', None)):
            self._update_history_collapsed_main()
    def _update_history_collapsed_main(self):
        # 确保history_list控件已正确初始化
        if hasattr(self, 'history_list') and self.history_list is not None:
            self.history_list.clear()
        else:
            # 如果控件还没准备好，延迟重试
            QTimer.singleShot(200, self._update_history_collapsed_main)
            return
            
        if not self.history:
            return
            
        if getattr(self, 'history_expanded', False):
            # 展开模式：显示所有历史记录
            for item in reversed(self.history):
                safe_item = to_simplified(item if item else "")
                display_text = safe_item[:50] + ("..." if len(safe_item) > 50 else "")
                self.history_list.addItem(display_text)
            if hasattr(self, 'expand_history_btn') and self.expand_history_btn:
                self.expand_history_btn.setText(to_simplified('收起历史'))
        else:
            # 收起模式：只显示最新的一条记录
            safe_item = to_simplified(self.history[-1] if self.history else "")
            display_text = safe_item[:50] + ("..." if len(safe_item) > 50 else "")
            self.history_list.addItem(display_text)
            if hasattr(self, 'expand_history_btn') and self.expand_history_btn:
                self.expand_history_btn.setText(to_simplified('展开历史'))
    def update_history(self):
        self.update_history_collapsed()
    def on_history_click(self, item):
        idx = self.history_list.row(item)
        text = list(reversed(self.history))[idx]
        text = to_simplified(text)
        if set_clipboard_text is not None:
            self.run_on_main(lambda: set_clipboard_text(text))
        else:
            clipboard = QApplication.clipboard() if hasattr(QApplication, 'clipboard') else None
            if clipboard and hasattr(clipboard, 'setText'):
                self.run_on_main(lambda: clipboard.setText(text))
        self.show_copy_status(to_simplified('历史内容已复制到剪贴板！'))
    def run_on_main(self, func):
        QTimer.singleShot(0, func)
    def after_recognition(self, text_simp):
        print('[DEBUG] after_recognition called')
        text_simp = to_simplified(text_simp)
        self.show_result(text_simp)
        QApplication.processEvents()
        if set_clipboard_text is not None:
            self.run_on_main(lambda: set_clipboard_text(text_simp))
        else:
            clipboard = QApplication.clipboard() if hasattr(QApplication, 'clipboard') else None
            if clipboard and hasattr(clipboard, 'setText'):
                self.run_on_main(lambda: clipboard.setText(text_simp))
        self.history.append(text_simp)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # 自动保存历史记录到文件
        self.save_history()
        
        self.update_history()
        QApplication.processEvents()
        self.model_combo.setEnabled(True)
        self.show_copy_status(to_simplified('识别结果已自动复制到剪贴板！'))
    def clear_history_session(self):
        self.history.clear()
        # 清空文件中的历史记录
        self.save_history()
        self.update_history()
        print("[DEBUG] 已清空历史记录和本地缓存")
    def show_copy_status(self, msg):
        """显示优雅的浮动状态提示"""
        if not hasattr(self, 'copy_status_label') or not self.copy_status_label:
            return
            
        def show_floating_toast():
            if self.copy_status_label:
                # 设置消息内容
                self.copy_status_label.setText(msg)
                
                # 计算位置：显示在窗口底部中央，略微上移
                self.copy_status_label.adjustSize()
                window_width = self.width()
                window_height = self.height()
                label_width = self.copy_status_label.width()
                label_height = self.copy_status_label.height()
                
                x = (window_width - label_width) // 2
                y = window_height - label_height - 80  # 距离底部80像素
                
                self.copy_status_label.move(x, y)
                self.copy_status_label.setVisible(True)
                self.copy_status_label.raise_()  # 确保在最上层
        
        def hide_floating_toast():
            if self.copy_status_label:
                self.copy_status_label.setVisible(False)
        
        # 显示提示
        if callable(getattr(self, 'run_on_main', None)):
            self.run_on_main(show_floating_toast)
        else:
            show_floating_toast()
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, hide_floating_toast)
    
    def resizeEvent(self, event):
        """窗口大小变化时重新定位浮动提示"""
        super().resizeEvent(event)
        if hasattr(self, 'copy_status_label') and self.copy_status_label and self.copy_status_label.isVisible():
            # 重新计算浮动提示的位置
            window_width = self.width()
            window_height = self.height()
            label_width = self.copy_status_label.width()
            label_height = self.copy_status_label.height()
            
            x = (window_width - label_width) // 2
            y = window_height - label_height - 80
            
            self.copy_status_label.move(x, y)
    def toggle_history_expanded(self):
        self.history_expanded = not self.history_expanded
        self.update_history_collapsed()
    def check_model_status(self, model_key):
        self.update_model_status_ui(False)
        self.model_status_label.setText('正在检测模型状态...')
        self.model_status_label.setStyleSheet('color: #2196F3;')
        def has_local_model():
            import os, glob
            cache_dirs = [os.path.expanduser('~/.cache/whisper'), os.path.expanduser('~/.cache/whisper/models')]
            for d in cache_dirs:
                if os.path.isdir(d):
                    for f in glob.glob(os.path.join(d, f'{model_key}*.pt')):
                        if os.path.getsize(f) > 10*1024*1024:
                            return True
            return False
        if has_local_model():
            self.run_on_main(lambda: self.update_model_status_ui(True))
            self.run_on_main(lambda: self.record_btn.setEnabled(True))
            if hasattr(self, 'retry_btn') and self.retry_btn:
                self.run_on_main(lambda: self.retry_btn.hide())
            return
        self.record_btn.setEnabled(False)
        if hasattr(self, 'retry_btn') and self.retry_btn:
            self.retry_btn.hide()
        def check_and_load():
            import time, whisper, os
            log_path = '/tmp/speech2clip_model_check.log'
            def log(msg):
                with open(log_path, 'a') as f:
                    f.write(msg + '\n')
            try:
                log(f'[DEBUG] 线程启动，检测模型: {model_key}')
                cache_dir = os.path.expanduser('~/.cache/whisper')
                model_files = [
                    os.path.join(cache_dir, f'{model_key}.pt'),
                    os.path.join(cache_dir, f'{model_key}-v3.pt')
                ]
                found = False
                for i in range(10):
                    if not any(os.path.exists(mf) and os.path.getsize(mf) > 10*1024*1024 for mf in model_files):
                        log(f'[DEBUG] 轮询等待模型文件...')
                        self.run_on_main(lambda: self.model_status_label.setText('模型未下载，正在自动下载中，请耐心等待...'))
                        self.run_on_main(lambda: self.record_btn.setEnabled(False))
                        time.sleep(1)
                    else:
                        found = True
                        break
                if not found:
                    log(f'[DEBUG] 超时未检测到模型文件')
                    self.run_on_main(lambda: self.model_status_label.setText('模型下载超时/失败，请检查网络或切换到已下载模型'))
                    if hasattr(self, 'retry_btn') and self.retry_btn:
                        self.run_on_main(lambda: self.retry_btn.show())
                    self.run_on_main(lambda: self.record_btn.setEnabled(False))
                    return
                try:
                    log(f'[DEBUG] 尝试加载模型: {model_key}')
                    whisper.load_model(model_key)
                    log(f'[DEBUG] 模型加载成功: {model_key}')
                    self.run_on_main(lambda: self.update_model_status_ui(True))
                    self.run_on_main(lambda: self.record_btn.setEnabled(True))
                    if hasattr(self, 'retry_btn') and self.retry_btn:
                        self.run_on_main(lambda: self.retry_btn.hide())
                except Exception as e:
                    log(f'[DEBUG] 模型加载失败: {e}')
                    self.run_on_main(lambda: self.model_status_label.setText('模型加载失败，请重试'))
                    if hasattr(self, 'retry_btn') and self.retry_btn:
                        self.run_on_main(lambda: self.retry_btn.show())
                    self.run_on_main(lambda: self.record_btn.setEnabled(False))
            except Exception as e:
                with open(log_path, 'a') as f:
                    f.write(f'[DEBUG] 线程异常: {e}\n')
        threading.Thread(target=check_and_load, daemon=True).start()
    def update_mic_status(self):
        """更新麦克风状态检测"""
        print('[DEBUG] 开始检测麦克风状态...')
        try:
            import pyaudio
            if pyaudio is None:
                msg = 'PyAudio 未安装或导入失败，请检查依赖。'
                self.update_mic_status_ui(False)
                print(msg)
                return
            pa = pyaudio.PyAudio()
            found = False
            detected_device_name = None
            device_names = []
            device_count = pa.get_device_count()
            if device_count == 0:
                msg = '未检测到任何音频设备（设备数为0）'
                self.update_mic_status_ui(False)
                print(msg)
                pa.terminate()
                return
            for i in range(device_count):
                info = pa.get_device_info_by_index(i)
                name = info.get('name', '')
                if not isinstance(name, str):
                    name = str(name)
                device_names.append(name)
                max_input_channels = info.get('maxInputChannels', 0)
                if not isinstance(max_input_channels, (int, float)):
                    try:
                        max_input_channels = float(max_input_channels)
                    except Exception:
                        max_input_channels = 0
                if (max_input_channels > 0) or ('microphone' in name.lower()) or ('input' in name.lower()) or ('麦克风' in name):
                    found = True
                    detected_device_name = name
                    break  # 找到第一个就可以了
            pa.terminate()
            
            print(f'[DEBUG] 设备总数: {device_count}, 设备名: {", ".join(device_names)}')
            
            if found:
                self.update_mic_status_ui(True)
                print(f'[DEBUG] 找到麦克风: {detected_device_name}')
            else:
                self.update_mic_status_ui(False)
                print('[DEBUG] 未找到可用麦克风')
        except Exception as e:
            import traceback
            err_msg = f'检测麦克风时发生异常: {e}\n{traceback.format_exc()}'
            self.update_mic_status_ui(False)
            print(err_msg)
    def create_status_dot(self, color):
        """创建状态指示器圆点"""
        pixmap = QPixmap(12, 12)
        pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.NoPen)  # 完全无边框
        painter.drawEllipse(0, 0, 12, 12)
        painter.end()
        return pixmap
    def update_model_status_ui(self, ready: bool):
        if ready:
            self.model_status_icon.setPixmap(self.create_status_dot('#28a745'))
            self.model_status_label.setText(to_simplified('模型已就绪'))
            self.model_status_label.setStyleSheet('color: #28a745; font-weight: 500; border: none;')
        else:
            self.model_status_icon.setPixmap(self.create_status_dot('#dc3545'))
            self.model_status_label.setText(to_simplified('模型未就绪'))
            self.model_status_label.setStyleSheet('color: #dc3545; font-weight: 500; border: none;')
    def update_mic_status_ui(self, ready: bool):
        if ready:
            self.mic_status_icon.setPixmap(self.create_status_dot('#28a745'))
            self.mic_status_label.setText(to_simplified('已检测到麦克风'))
            self.mic_status_label.setStyleSheet('color: #28a745; font-weight: 500; border: none;')
        else:
            self.mic_status_icon.setPixmap(self.create_status_dot('#dc3545'))
            self.mic_status_label.setText(to_simplified('未检测到麦克风'))
            self.mic_status_label.setStyleSheet('color: #dc3545; font-weight: 500; border: none;')
    def init_hotkey(self):
        # 集成QHotkey全局热键，支持macOS/Win/Linux
        if QHotkey is None:
            print('[WARN] QHotkey未安装，无法注册全局热键')
            return
        try:
            self.hotkey = QHotkey('ctrl+shift+r', parent=self, autoRegister=True)
            self.hotkey.activated.connect(self.on_hotkey_triggered)
            if self.hotkey.isRegistered():
                print('[INFO] 全局热键 ctrl+shift+r 注册成功，可在任意窗口触发录音')
            else:
                print('[WARN] 全局热键注册失败，可能缺少系统权限或被占用')
        except Exception as e:
            print(f'[WARN] QHotkey注册异常: {e}')
    def on_hotkey_triggered(self):
        # 全局热键触发时的回调，等价于点击"开始说话"按钮
        self.toggle_recording()
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 兼容旧格式和新格式
                if isinstance(data, list):
                    # 旧格式：直接是文本列表
                    self.history = data[-self.max_history:]
                    print(f"[DEBUG] 加载旧格式历史记录: {self.history}")
                elif isinstance(data, dict) and 'entries' in data:
                    # 新格式：包含元数据的字典格式
                    entries = data['entries'][-self.max_history:]
                    self.history = [entry.get('text', '') for entry in entries]
                else:
                    self.history = []
                
                print(f"[DEBUG] 成功加载 {len(self.history)} 条历史记录")
            else:
                self.history = []
                print("[DEBUG] 历史记录文件不存在，使用空历史记录")
        except Exception as e:
            print(f"[ERROR] 加载历史记录失败: {e}")
            import traceback
            traceback.print_exc()
            self.history = []
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            # 创建包含元数据的历史记录格式
            history_data = {
                'version': '1.0',
                'last_saved': datetime.now().isoformat(),
                'total_entries': len(self.history),
                'entries': []
            }
            
            # 转换历史记录为详细格式
            for i, text in enumerate(self.history):
                entry = {
                    'id': f"speech_{int(datetime.now().timestamp())}_{i}",
                    'text': text,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'speech_recognition',
                    'confidence': 0.8  # 默认置信度
                }
                history_data['entries'].append(entry)
            
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            print(f"[DEBUG] 已保存 {len(self.history)} 条历史记录到 {self.history_file}")
            return True
        except Exception as e:
            print(f"[ERROR] 保存历史记录失败: {e}")
            return False
    def force_update_history(self):
        """强制更新历史记录显示（启动时使用）"""
        if hasattr(self, 'history_list') and self.history_list is not None:
            self.update_history()
        else:
            QTimer.singleShot(500, self.force_update_history)

if __name__ == '__main__':
    with open('/tmp/speech2clip_model_check.log', 'a') as f:
        f.write('[DEBUG] __main__ 入口已执行\n')
    app = QApplication(sys.argv)
    app.setApplicationName("Speech2Clip")
    app.setApplicationDisplayName("Speech2Clip 语音转文字")
    # 设置Dock图标为大尺寸自定义图标
    app.setWindowIcon(QIcon(os.path.abspath('src/app_icon.png')))
    gui = Speech2ClipGUI()
    gui.show()
    tray_icon_path = os.path.abspath('src/tray_icon.png')
    tray = TrayManager(app, gui, icon_path=tray_icon_path)
    # 集成全局快捷键
    hotkey = HotkeyManager()
    def trigger_record():
        # 仅在主窗口可见时触发录音
        if not gui.is_recording:
            gui.toggle_recording()
    hotkey.register_hotkey('ctrl+shift+r', trigger_record)
    hotkey.start_listening()
    sys.exit(app.exec_()) 