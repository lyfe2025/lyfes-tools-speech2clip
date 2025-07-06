import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon

class TrayManager:
    def __init__(self, app, main_window, icon_path=None):
        """
        系统托盘管理器，负责显示托盘图标和菜单。
        :param app: QApplication实例
        :param main_window: 主窗口实例，用于显示/隐藏
        :param icon_path: 托盘图标路径（可选）
        """
        self.app = app
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon()
        # 增强：icon_path转为绝对路径，打印调试信息，检查QIcon.isNull()
        icon_set = False
        if icon_path:
            abs_icon_path = os.path.abspath(icon_path)
            print(f'[DEBUG] 托盘图标路径: {abs_icon_path}')
            icon = QIcon(abs_icon_path)
            print(f'[DEBUG] QIcon.isNull(): {icon.isNull()}')
            if not icon.isNull():
                self.tray_icon.setIcon(icon)
                icon_set = True
            else:
                print(f'[WARN] QIcon加载失败，回退为Qt默认图标')
        if not icon_set:
            self.tray_icon.setIcon(QIcon())
        self.menu = QMenu()
        # 添加菜单项
        self.show_action = QAction("显示主界面")
        self.exit_action = QAction("退出")
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.exit_action)
        self.tray_icon.setContextMenu(self.menu)
        # 绑定事件
        self.show_action.triggered.connect(self.show_main_window)
        self.exit_action.triggered.connect(self.exit_app)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_main_window(self):
        """显示主界面"""
        self.main_window.showNormal()
        self.main_window.activateWindow()

    def exit_app(self):
        """退出应用"""
        self.tray_icon.hide()
        self.app.quit()

    def on_tray_activated(self, reason):
        """托盘图标点击事件，双击显示主界面"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window() 