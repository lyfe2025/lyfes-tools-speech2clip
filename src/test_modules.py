#!/usr/bin/env python3
"""
Speech2Clip 模块测试脚本
测试所有核心模块的功能
"""

import sys
import os
import time
from typing import Dict, List

# 导入模块
try:
    from audio_recorder import AudioRecorder
    from speech_recognizer import SpeechRecognizer, RecognitionEngine
    from clipboard_manager import ClipboardManager
    from config_manager import ConfigManager
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)


class ModuleTester:
    """模块测试器"""
    
    def __init__(self):
        self.test_results = {}
        self.config = None
        self.audio_recorder = None
        self.speech_recognizer = None
        self.clipboard_manager = None
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 Speech2Clip 模块测试开始")
        print("=" * 50)
        
        # 测试各个模块
        self.test_config_manager()
        self.test_clipboard_manager()
        self.test_audio_recorder()
        self.test_speech_recognizer()
        self.test_integration()
        
        # 显示测试结果
        self.show_test_results()
    
    def test_config_manager(self):
        """测试配置管理器"""
        print("\n📋 测试配置管理器...")
        
        try:
            # 创建配置管理器
            self.config = ConfigManager()
            
            # 测试基本配置操作
            test_key = "test.setting"
            test_value = "test_value"
            
            # 设置配置
            assert self.config.set(test_key, test_value), "设置配置失败"
            
            # 读取配置
            retrieved_value = self.config.get(test_key)
            assert retrieved_value == test_value, "读取配置失败"
            
            # 测试用户偏好
            assert self.config.set_user_pref("test_pref", "pref_value"), "设置用户偏好失败"
            assert self.config.get_user_pref("test_pref") == "pref_value", "读取用户偏好失败"
            
            # 测试使用统计
            assert self.config.update_usage_stats(recordings=1, characters=10), "更新统计失败"
            
            # 测试配置摘要
            summary = self.config.get_config_summary()
            assert isinstance(summary, dict), "获取配置摘要失败"
            
            self.test_results["config_manager"] = "✅ 通过"
            print("  ✅ 配置管理器测试通过")
            
        except Exception as e:
            self.test_results["config_manager"] = f"❌ 失败: {e}"
            print(f"  ❌ 配置管理器测试失败: {e}")
    
    def test_clipboard_manager(self):
        """测试剪贴板管理器"""
        print("\n📋 测试剪贴板管理器...")
        
        try:
            # 创建剪贴板管理器
            self.clipboard_manager = ClipboardManager(max_history=10, auto_save=False)
            
            # 测试复制功能
            test_text = "这是测试文本"
            assert self.clipboard_manager.copy_text(test_text), "复制文本失败"
            
            # 测试历史记录
            history = self.clipboard_manager.get_history()
            assert len(history) > 0, "历史记录为空"
            assert history[0].content == test_text, "历史记录内容不匹配"
            
            # 测试搜索功能
            search_results = self.clipboard_manager.search_history("测试")
            assert len(search_results) > 0, "搜索功能失败"
            
            # 测试统计信息
            stats = self.clipboard_manager.get_statistics()
            assert isinstance(stats, dict), "获取统计信息失败"
            assert stats["total_entries"] > 0, "统计信息不正确"
            
            self.test_results["clipboard_manager"] = "✅ 通过"
            print("  ✅ 剪贴板管理器测试通过")
            
        except Exception as e:
            self.test_results["clipboard_manager"] = f"❌ 失败: {e}"
            print(f"  ❌ 剪贴板管理器测试失败: {e}")
    
    def test_audio_recorder(self):
        """测试音频录制器"""
        print("\n🎤 测试音频录制器...")
        
        try:
            # 创建音频录制器
            self.audio_recorder = AudioRecorder()
            
            # 测试音频配置
            config_info = self.audio_recorder.get_audio_info()
            assert isinstance(config_info, dict), "获取音频配置失败"
            
            # 测试设备检测
            devices = self.audio_recorder.get_audio_devices()
            print(f"  📱 检测到 {len(devices)} 个音频设备")
            
            # 测试设备测试功能
            device_test_result = self.audio_recorder.test_audio_device()
            print(f"  🔧 默认设备测试: {'通过' if device_test_result else '失败'}")
            
            # 测试音频配置设置
            self.audio_recorder.set_audio_config(sample_rate=22050)
            updated_config = self.audio_recorder.get_audio_info()
            assert updated_config["sample_rate"] == 22050, "音频配置设置失败"
            
            self.test_results["audio_recorder"] = "✅ 通过"
            print("  ✅ 音频录制器测试通过")
            
        except Exception as e:
            self.test_results["audio_recorder"] = f"❌ 失败: {e}"
            print(f"  ❌ 音频录制器测试失败: {e}")
    
    def test_speech_recognizer(self):
        """测试语音识别器"""
        print("\n🗣️ 测试语音识别器...")
        
        try:
            # 创建语音识别器
            self.speech_recognizer = SpeechRecognizer()
            
            # 测试支持的语言
            languages = self.speech_recognizer.get_supported_languages()
            assert isinstance(languages, dict), "获取支持语言失败"
            assert len(languages) > 0, "支持语言列表为空"
            print(f"  🌍 支持 {len(languages)} 种语言")
            
            # 测试语言设置
            assert self.speech_recognizer.set_language("en-US"), "设置语言失败"
            assert self.speech_recognizer.default_language == "en-US", "语言设置不正确"
            
            # 测试引擎设置
            assert self.speech_recognizer.set_engine(RecognitionEngine.GOOGLE), "设置引擎失败"
            assert self.speech_recognizer.current_engine == RecognitionEngine.GOOGLE, "引擎设置不正确"
            
            # 测试识别器信息
            info = self.speech_recognizer.get_recognition_info()
            assert isinstance(info, dict), "获取识别器信息失败"
            
            # 测试功能（不实际录音）
            assert self.speech_recognizer.test_recognition(), "测试识别功能失败"
            
            self.test_results["speech_recognizer"] = "✅ 通过"
            print("  ✅ 语音识别器测试通过")
            
        except Exception as e:
            self.test_results["speech_recognizer"] = f"❌ 失败: {e}"
            print(f"  ❌ 语音识别器测试失败: {e}")
    
    def test_integration(self):
        """测试模块集成"""
        print("\n🔗 测试模块集成...")
        
        try:
            # 测试配置与其他模块的集成
            if self.config and self.speech_recognizer:
                # 通过配置设置语音识别器
                self.config.set("speech.language", "zh-CN")
                language = self.config.get("speech.language")
                self.speech_recognizer.set_language(language)
                assert self.speech_recognizer.default_language == "zh-CN", "配置集成失败"
            
            # 测试模拟的完整工作流程
            if self.clipboard_manager and self.config:
                # 模拟识别结果
                mock_text = "这是模拟的语音识别结果"
                mock_confidence = 0.95
                
                # 复制到剪贴板
                metadata = {
                    'source': 'speech2clip_test',
                    'confidence': mock_confidence,
                    'language': 'zh-CN'
                }
                
                assert self.clipboard_manager.copy_text(mock_text, metadata), "工作流程集成失败"
                
                # 更新统计
                assert self.config.update_usage_stats(recordings=1, characters=len(mock_text)), "统计更新失败"
            
            self.test_results["integration"] = "✅ 通过"
            print("  ✅ 模块集成测试通过")
            
        except Exception as e:
            self.test_results["integration"] = f"❌ 失败: {e}"
            print(f"  ❌ 模块集成测试失败: {e}")
    
    def show_test_results(self):
        """显示测试结果"""
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for module, result in self.test_results.items():
            print(f"  {module}: {result}")
            if "✅" in result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n总计: {passed + failed} 个测试")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        
        if failed == 0:
            print("\n🎉 所有测试都通过了！项目模块运行正常。")
        else:
            print(f"\n⚠️ 有 {failed} 个测试失败，请检查相关模块。")
        
        return failed == 0
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.audio_recorder:
                self.audio_recorder.cleanup()
            if self.clipboard_manager:
                self.clipboard_manager.stop_monitoring()
        except Exception as e:
            print(f"清理资源时出错: {e}")


def main():
    """主函数"""
    tester = ModuleTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n✨ 模块测试完成，可以继续开发下一阶段功能！")
        else:
            print("\n🔧 请修复失败的模块后再继续开发。")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生意外错误: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()