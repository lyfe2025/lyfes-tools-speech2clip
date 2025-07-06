#!/usr/bin/env python3
"""
剪贴板管理模块
处理剪贴板操作、历史记录和多格式支持
"""

import pyperclip
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading
import time


class ClipboardEntry:
    """剪贴板条目类"""
    
    def __init__(self, content: str, content_type: str = "text", metadata: Optional[Dict] = None):
        self.content = content
        self.content_type = content_type
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{hash(self.content) % 10000:04d}"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'content_type': self.content_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClipboardEntry':
        """从字典创建实例"""
        entry = cls(data['content'], data['content_type'], data.get('metadata', {}))
        entry.id = data['id']
        entry.timestamp = datetime.fromisoformat(data['timestamp'])
        return entry
    
    def __str__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {preview}"


class ClipboardManager:
    """剪贴板管理器类"""
    
    def __init__(self, max_history: int = 100, auto_save: bool = True):
        self.max_history = max_history
        self.auto_save = auto_save
        self.history: List[ClipboardEntry] = []
        self.history_file = os.path.expanduser("~/.speech2clip_clipboard_history.json")
        
        # 监控设置
        self.monitoring = False
        self.monitor_thread = None
        self.last_clipboard_content = ""
        
        # 回调函数
        self.on_clipboard_change = None
        self.on_copy_success = None
        self.on_copy_error = None
        
        # 加载历史记录
        if self.auto_save:
            self.load_history()
    
    def copy_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """复制文本到剪贴板"""
        try:
            # 复制到系统剪贴板
            pyperclip.copy(text)
            
            # 添加到历史记录
            entry = ClipboardEntry(text, "text", metadata)
            self._add_to_history(entry)
            
            # 触发成功回调
            if self.on_copy_success:
                self.on_copy_success(text)
            
            return True
            
        except Exception as e:
            error_msg = f"复制到剪贴板失败: {e}"
            if self.on_copy_error:
                self.on_copy_error(error_msg)
            print(error_msg)
            return False
    
    def paste_text(self) -> Optional[str]:
        """从剪贴板粘贴文本"""
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"从剪贴板获取文本失败: {e}")
            return None
    
    def copy_with_format(self, content: Any, content_type: str, metadata: Optional[Dict] = None) -> bool:
        """复制指定格式的内容"""
        try:
            if content_type == "text":
                return self.copy_text(str(content), metadata)
            elif content_type == "json":
                json_str = json.dumps(content, ensure_ascii=False, indent=2)
                json_metadata = (metadata or {}).copy()
                json_metadata['format'] = 'json'
                return self.copy_text(json_str, json_metadata)
            elif content_type == "html":
                # HTML格式暂时作为文本处理
                html_metadata = (metadata or {}).copy()
                html_metadata['format'] = 'html'
                return self.copy_text(str(content), html_metadata)
            else:
                print(f"不支持的内容类型: {content_type}")
                return False
        except Exception as e:
            print(f"复制格式化内容失败: {e}")
            return False
    
    def get_history(self) -> List[ClipboardEntry]:
        """获取剪贴板历史记录"""
        return self.history.copy()
    
    def get_recent_entries(self, count: int = 10) -> List[ClipboardEntry]:
        """获取最近的条目"""
        return self.history[:count]
    
    def search_history(self, keyword: str) -> List[ClipboardEntry]:
        """搜索历史记录"""
        results = []
        keyword_lower = keyword.lower()
        
        for entry in self.history:
            if keyword_lower in entry.content.lower():
                results.append(entry)
        
        return results
    
    def get_entry_by_id(self, entry_id: str) -> Optional[ClipboardEntry]:
        """根据ID获取条目"""
        for entry in self.history:
            if entry.id == entry_id:
                return entry
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除指定的历史条目"""
        for i, entry in enumerate(self.history):
            if entry.id == entry_id:
                del self.history[i]
                if self.auto_save:
                    self.save_history()
                return True
        return False
    
    def clear_history(self) -> bool:
        """清空历史记录"""
        try:
            self.history.clear()
            if self.auto_save:
                self.save_history()
            return True
        except Exception as e:
            print(f"清空历史记录失败: {e}")
            return False
    
    def _add_to_history(self, entry: ClipboardEntry):
        """添加条目到历史记录"""
        # 检查是否是重复内容
        if self.history and self.history[0].content == entry.content:
            return
        
        # 添加到开头
        self.history.insert(0, entry)
        
        # 限制历史记录长度
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # 自动保存
        if self.auto_save:
            self.save_history()
    
    def save_history(self) -> bool:
        """保存历史记录到文件"""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'entries': [entry.to_dict() for entry in self.history]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存历史记录失败: {e}")
            return False
    
    def load_history(self) -> bool:
        """从文件加载历史记录"""
        try:
            if not os.path.exists(self.history_file):
                return True
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entries_data = data.get('entries', [])
            self.history = [ClipboardEntry.from_dict(entry_data) for entry_data in entries_data]
            
            # 限制长度
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]
            
            return True
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return False
    
    def start_monitoring(self, interval: float = 1.0):
        """开始监控剪贴板变化"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_clipboard, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("📋 开始监控剪贴板变化")
    
    def stop_monitoring(self):
        """停止监控剪贴板"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        print("📋 停止监控剪贴板")
    
    def _monitor_clipboard(self, interval: float):
        """内部剪贴板监控循环"""
        try:
            self.last_clipboard_content = pyperclip.paste()
        except:
            self.last_clipboard_content = ""
        
        while self.monitoring:
            try:
                current_content = pyperclip.paste()
                
                if current_content != self.last_clipboard_content:
                    # 剪贴板内容发生变化
                    if current_content:  # 忽略空内容
                        entry = ClipboardEntry(current_content, "text", 
                                             {'source': 'system_monitor'})
                        self._add_to_history(entry)
                        
                        if self.on_clipboard_change:
                            self.on_clipboard_change(current_content)
                    
                    self.last_clipboard_content = current_content
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"监控剪贴板时出错: {e}")
                time.sleep(interval)
    
    def get_statistics(self) -> Dict:
        """获取使用统计"""
        if not self.history:
            return {
                'total_entries': 0,
                'average_length': 0,
                'longest_entry': 0,
                'shortest_entry': 0,
                'types': {}
            }
        
        lengths = [len(entry.content) for entry in self.history]
        types = {}
        
        for entry in self.history:
            content_type = entry.content_type
            types[content_type] = types.get(content_type, 0) + 1
        
        return {
            'total_entries': len(self.history),
            'average_length': sum(lengths) / len(lengths),
            'longest_entry': max(lengths),
            'shortest_entry': min(lengths),
            'types': types,
            'oldest_entry': self.history[-1].timestamp.isoformat() if self.history else None,
            'newest_entry': self.history[0].timestamp.isoformat() if self.history else None
        }
    
    def export_history(self, filename: str, format: str = "json") -> bool:
        """导出历史记录"""
        try:
            if format == "json":
                data = {
                    'export_time': datetime.now().isoformat(),
                    'total_entries': len(self.history),
                    'entries': [entry.to_dict() for entry in self.history]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif format == "txt":
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Speech2Clip 剪贴板历史记录\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"总条目数: {len(self.history)}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, entry in enumerate(self.history, 1):
                        f.write(f"条目 {i}:\n")
                        f.write(f"时间: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"类型: {entry.content_type}\n")
                        f.write(f"内容: {entry.content}\n")
                        f.write("-" * 30 + "\n\n")
            
            else:
                print(f"不支持的导出格式: {format}")
                return False
            
            return True
            
        except Exception as e:
            print(f"导出历史记录失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 创建剪贴板管理器
    clipboard = ClipboardManager(max_history=20)
    
    # 设置回调函数
    def on_copy_success(text):
        print(f"✅ 成功复制: {text[:30]}...")
    
    def on_clipboard_change(text):
        print(f"📋 剪贴板变化: {text[:30]}...")
    
    clipboard.on_copy_success = on_copy_success
    clipboard.on_clipboard_change = on_clipboard_change
    
    # 测试复制功能
    print("🧪 测试剪贴板功能")
    
    # 复制一些测试文本
    test_texts = [
        "这是第一个测试文本",
        "这是第二个测试文本",
        "Hello, this is English text",
        '{"name": "测试", "type": "JSON"}',
    ]
    
    for text in test_texts:
        success = clipboard.copy_text(text, {'source': 'test'})
        print(f"复制 {'成功' if success else '失败'}: {text[:20]}...")
    
    # 显示历史记录
    print(f"\n📜 历史记录 ({len(clipboard.get_history())} 条):")
    for entry in clipboard.get_recent_entries(5):
        print(f"  {entry}")
    
    # 显示统计信息
    stats = clipboard.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  总条目数: {stats['total_entries']}")
    print(f"  平均长度: {stats['average_length']:.1f} 字符")
    print(f"  类型分布: {stats['types']}")
    
    # 测试搜索
    search_results = clipboard.search_history("测试")
    print(f"\n🔍 搜索 '测试' 的结果: {len(search_results)} 条")
    
    print("\n🎉 剪贴板管理器测试完成")

# 兼容 GUI 直接调用的剪贴板复制函数
_clipboard_manager_instance = ClipboardManager(max_history=100, auto_save=True)
def set_clipboard_text(text):
    return _clipboard_manager_instance.copy_text(text)