#!/usr/bin/env python3
"""
配置管理模块
处理应用程序设置、用户偏好和设备配置
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import shutil


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        # 设置配置目录
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".speech2clip"
        
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.main_config_file = self.config_dir / "config.json"
        self.user_prefs_file = self.config_dir / "user_preferences.json"
        self.device_config_file = self.config_dir / "devices.json"
        
        # 默认配置
        self.default_config = {
            "version": "1.0",
            "app": {
                "name": "Speech2Clip",
                "auto_start": False,
                "minimize_to_tray": True,
                "show_notifications": True,
                "check_updates": True
            },
            "speech": {
                "engine": "google",
                "language": "zh-CN",
                "timeout": 10,
                "phrase_time_limit": 10,
                "auto_copy": True,
                "confidence_threshold": 0.5
            },
            "audio": {
                "sample_rate": 44100,
                "channels": 1,
                "chunk_size": 1024,
                "device_index": None,
                "auto_adjust_noise": True,
                "noise_duration": 1.0
            },
            "clipboard": {
                "max_history": 100,
                "auto_save_history": True,
                "monitor_changes": False,
                "monitor_interval": 1.0
            },
            "ui": {
                "theme": "system",
                "language": "zh-CN",
                "window_size": [400, 300],
                "window_position": "center",
                "always_on_top": False,
                "opacity": 1.0
            },
            "shortcuts": {
                "start_recording": "Ctrl+Shift+R",
                "stop_recording": "Ctrl+Shift+S",
                "toggle_window": "Ctrl+Shift+V",
                "paste_last": "Ctrl+Shift+P"
            },
            "advanced": {
                "log_level": "INFO",
                "debug_mode": False,
                "temp_dir": None,
                "backup_config": True,
                "backup_count": 5
            }
        }
        
        # 当前配置
        self.config = {}
        self.user_preferences = {}
        self.device_config = {}
        
        # 加载配置
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        self.load_main_config()
        self.load_user_preferences()
        self.load_device_config()
    
    def load_main_config(self) -> bool:
        """加载主配置文件"""
        try:
            if self.main_config_file.exists():
                with open(self.main_config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并默认配置和加载的配置
                self.config = self._merge_configs(self.default_config, loaded_config)
            else:
                # 使用默认配置并保存
                self.config = self.default_config.copy()
                self.save_main_config()
            
            return True
        except Exception as e:
            print(f"加载主配置失败: {e}")
            self.config = self.default_config.copy()
            return False
    
    def save_main_config(self) -> bool:
        """保存主配置文件"""
        try:
            # 备份现有配置
            if self.config.get("advanced", {}).get("backup_config", True):
                self._backup_config_file(self.main_config_file)
            
            # 添加保存时间戳
            config_to_save = self.config.copy()
            config_to_save["last_saved"] = datetime.now().isoformat()
            
            with open(self.main_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存主配置失败: {e}")
            return False
    
    def load_user_preferences(self) -> bool:
        """加载用户偏好设置"""
        try:
            if self.user_prefs_file.exists():
                with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            else:
                self.user_preferences = {
                    "recent_languages": ["zh-CN", "en-US"],
                    "favorite_shortcuts": [],
                    "custom_commands": {},
                    "usage_stats": {
                        "total_recordings": 0,
                        "total_characters": 0,
                        "favorite_language": "zh-CN",
                        "last_used": None
                    }
                }
                self.save_user_preferences()
            
            return True
        except Exception as e:
            print(f"加载用户偏好失败: {e}")
            return False
    
    def save_user_preferences(self) -> bool:
        """保存用户偏好设置"""
        try:
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户偏好失败: {e}")
            return False
    
    def load_device_config(self) -> bool:
        """加载设备配置"""
        try:
            if self.device_config_file.exists():
                with open(self.device_config_file, 'r', encoding='utf-8') as f:
                    self.device_config = json.load(f)
            else:
                self.device_config = {
                    "audio_devices": [],
                    "preferred_device": None,
                    "device_settings": {},
                    "last_scan": None
                }
                self.save_device_config()
            
            return True
        except Exception as e:
            print(f"加载设备配置失败: {e}")
            return False
    
    def save_device_config(self) -> bool:
        """保存设备配置"""
        try:
            with open(self.device_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设备配置失败: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值（支持点分隔的路径）"""
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key_path: str, value: Any, auto_save: bool = True) -> bool:
        """设置配置值（支持点分隔的路径）"""
        try:
            keys = key_path.split('.')
            current = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
            if auto_save:
                return self.save_main_config()
            
            return True
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False
    
    def get_user_pref(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        return self.user_preferences.get(key, default)
    
    def set_user_pref(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置用户偏好"""
        try:
            self.user_preferences[key] = value
            if auto_save:
                return self.save_user_preferences()
            return True
        except Exception as e:
            print(f"设置用户偏好失败: {e}")
            return False
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """获取设备信息"""
        devices = self.device_config.get("audio_devices", [])
        for device in devices:
            if device.get("id") == device_id:
                return device
        return None
    
    def add_audio_device(self, device_info: Dict) -> bool:
        """添加音频设备信息"""
        try:
            devices = self.device_config.get("audio_devices", [])
            
            # 检查是否已存在
            for i, device in enumerate(devices):
                if device.get("id") == device_info.get("id"):
                    devices[i] = device_info  # 更新现有设备
                    break
            else:
                devices.append(device_info)  # 添加新设备
            
            self.device_config["audio_devices"] = devices
            self.device_config["last_scan"] = datetime.now().isoformat()
            
            return self.save_device_config()
        except Exception as e:
            print(f"添加音频设备失败: {e}")
            return False
    
    def set_preferred_device(self, device_id: str) -> bool:
        """设置首选音频设备"""
        return self.set_device_config("preferred_device", device_id)
    
    def get_preferred_device(self) -> Optional[str]:
        """获取首选音频设备"""
        return self.device_config.get("preferred_device")
    
    def set_device_config(self, key: str, value: Any) -> bool:
        """设置设备配置"""
        try:
            self.device_config[key] = value
            return self.save_device_config()
        except Exception as e:
            print(f"设置设备配置失败: {e}")
            return False
    
    def update_usage_stats(self, recordings: int = 0, characters: int = 0, 
                          language: str = None) -> bool:
        """更新使用统计"""
        try:
            stats = self.user_preferences.get("usage_stats", {})
            
            stats["total_recordings"] = stats.get("total_recordings", 0) + recordings
            stats["total_characters"] = stats.get("total_characters", 0) + characters
            stats["last_used"] = datetime.now().isoformat()
            
            if language:
                stats["favorite_language"] = language
            
            self.user_preferences["usage_stats"] = stats
            return self.save_user_preferences()
        except Exception as e:
            print(f"更新使用统计失败: {e}")
            return False
    
    def add_recent_language(self, language: str, max_recent: int = 5) -> bool:
        """添加最近使用的语言"""
        try:
            recent = self.user_preferences.get("recent_languages", [])
            
            # 移除重复项
            if language in recent:
                recent.remove(language)
            
            # 添加到开头
            recent.insert(0, language)
            
            # 限制长度
            recent = recent[:max_recent]
            
            self.user_preferences["recent_languages"] = recent
            return self.save_user_preferences()
        except Exception as e:
            print(f"添加最近语言失败: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出所有配置"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "version": self.config.get("version", "1.0"),
                "main_config": self.config,
                "user_preferences": self.user_preferences,
                "device_config": self.device_config
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 备份当前配置
            self._backup_all_configs()
            
            # 导入配置
            if "main_config" in import_data:
                self.config = self._merge_configs(self.default_config, 
                                                import_data["main_config"])
                self.save_main_config()
            
            if "user_preferences" in import_data:
                self.user_preferences = import_data["user_preferences"]
                self.save_user_preferences()
            
            if "device_config" in import_data:
                self.device_config = import_data["device_config"]
                self.save_device_config()
            
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def reset_to_defaults(self, backup: bool = True) -> bool:
        """重置为默认配置"""
        try:
            if backup:
                self._backup_all_configs()
            
            self.config = self.default_config.copy()
            self.save_main_config()
            
            return True
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """合并配置（深度合并）"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _backup_config_file(self, config_file: Path):
        """备份单个配置文件"""
        try:
            if not config_file.exists():
                return
            
            backup_dir = self.config_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_file.stem}_{timestamp}.json"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(config_file, backup_path)
            
            # 清理旧备份
            self._cleanup_old_backups(backup_dir, config_file.stem)
            
        except Exception as e:
            print(f"备份配置文件失败: {e}")
    
    def _backup_all_configs(self):
        """备份所有配置文件"""
        self._backup_config_file(self.main_config_file)
        self._backup_config_file(self.user_prefs_file)
        self._backup_config_file(self.device_config_file)
    
    def _cleanup_old_backups(self, backup_dir: Path, file_prefix: str):
        """清理旧的备份文件"""
        try:
            max_backups = self.config.get("advanced", {}).get("backup_count", 5)
            
            # 获取匹配的备份文件
            backup_files = [f for f in backup_dir.glob(f"{file_prefix}_*.json")]
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除超出数量的备份
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                
        except Exception as e:
            print(f"清理备份文件失败: {e}")
    
    def get_config_summary(self) -> Dict:
        """获取配置摘要"""
        return {
            "config_dir": str(self.config_dir),
            "version": self.config.get("version", "unknown"),
            "speech_engine": self.get("speech.engine"),
            "speech_language": self.get("speech.language"),
            "ui_theme": self.get("ui.theme"),
            "audio_device": self.get_preferred_device(),
            "total_recordings": self.get_user_pref("usage_stats", {}).get("total_recordings", 0),
            "last_used": self.get_user_pref("usage_stats", {}).get("last_used")
        }


# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    config = ConfigManager()
    
    # 显示配置摘要
    summary = config.get_config_summary()
    print("📋 配置摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 测试配置操作
    print("\n🧪 测试配置操作:")
    
    # 设置一些配置
    config.set("speech.language", "en-US")
    config.set("ui.theme", "dark")
    config.set_user_pref("test_setting", "test_value")
    
    # 读取配置
    print(f"语音语言: {config.get('speech.language')}")
    print(f"UI主题: {config.get('ui.theme')}")
    print(f"测试设置: {config.get_user_pref('test_setting')}")
    
    # 更新使用统计
    config.update_usage_stats(recordings=1, characters=50, language="en-US")
    config.add_recent_language("en-US")
    
    # 显示更新后的统计
    stats = config.get_user_pref("usage_stats", {})
    print(f"\n📊 使用统计:")
    print(f"  总录音次数: {stats.get('total_recordings', 0)}")
    print(f"  总字符数: {stats.get('total_characters', 0)}")
    print(f"  最近语言: {config.get_user_pref('recent_languages', [])}")
    
    print("\n✅ 配置管理器测试完成")