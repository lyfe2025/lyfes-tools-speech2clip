import threading
import sys
import keyboard  # 需提前 pip install keyboard

class HotkeyManager:
    def __init__(self):
        """
        全局快捷键管理器，负责注册和注销快捷键。
        """
        self.registered_hotkeys = {}
        self.listener_thread = None
        self.running = False

    def register_hotkey(self, hotkey, callback):
        """
        注册全局快捷键。
        :param hotkey: 快捷键组合字符串，如 'ctrl+shift+r'
        :param callback: 快捷键触发时调用的回调函数
        """
        if sys.platform == 'darwin':
            print(f"[HotkeyManager] macOS 下全局热键不可用，已跳过注册：{hotkey}")
            return
        if hotkey in self.registered_hotkeys:
            try:
                keyboard.remove_hotkey(self.registered_hotkeys[hotkey])
            except Exception as e:
                print(f"[HotkeyManager] 移除旧热键异常: {e}")
        try:
            hotkey_id = keyboard.add_hotkey(hotkey, callback)
            self.registered_hotkeys[hotkey] = hotkey_id
        except Exception as e:
            print(f"[HotkeyManager] 注册热键失败({hotkey}): {e}")

    def unregister_hotkey(self, hotkey):
        """
        注销指定快捷键。
        """
        if hotkey in self.registered_hotkeys:
            keyboard.remove_hotkey(self.registered_hotkeys[hotkey])
            del self.registered_hotkeys[hotkey]

    def start_listening(self):
        """
        启动监听线程，保持快捷键响应。
        """
        if self.listener_thread and self.listener_thread.is_alive():
            return
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

    def _listen(self):
        """
        监听主循环，阻塞直到 stop_listening 被调用。
        """
        while self.running:
            keyboard.wait()

    def stop_listening(self):
        """
        停止监听线程。
        """
        self.running = False
        keyboard.unhook_all_hotkeys()
        self.registered_hotkeys.clear() 