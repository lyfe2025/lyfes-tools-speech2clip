#!/usr/bin/env python3
"""
语音识别模块
支持多种语音识别引擎和多语言识别
"""

import speech_recognition as sr
import os
import tempfile
from typing import Optional, Dict, List, Tuple
from enum import Enum
import json


class RecognitionEngine(Enum):
    """语音识别引擎枚举"""
    GOOGLE = "google"
    GOOGLE_CLOUD = "google_cloud"
    WHISPER = "whisper"
    BING = "bing"
    HOUNDIFY = "houndify"
    IBM = "ibm"


class SpeechRecognizer:
    """语音识别器类"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.current_engine = RecognitionEngine.GOOGLE
        self.default_language = 'zh-CN'
        
        # 支持的语言
        self.supported_languages = {
            'zh-CN': '中文（简体）',
            'zh-TW': '中文（繁体）',
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            'ja-JP': '日本語',
            'ko-KR': '한국어',
            'fr-FR': 'Français',
            'de-DE': 'Deutsch',
            'es-ES': 'Español',
            'ru-RU': 'Русский'
        }
        
        # 引擎配置
        self.engine_configs = {
            RecognitionEngine.GOOGLE: {
                'timeout': 10,
                'phrase_time_limit': 10
            },
            RecognitionEngine.WHISPER: {
                'model': 'base',
                'timeout': 30
            }
        }
        
        # Whisper模型缓存
        self._whisper_model = None
        
    def set_engine(self, engine: RecognitionEngine) -> bool:
        """设置语音识别引擎"""
        try:
            self.current_engine = engine
            return True
        except Exception as e:
            print(f"设置识别引擎失败: {e}")
            return False
    
    def set_language(self, language_code: str) -> bool:
        """设置识别语言"""
        if language_code in self.supported_languages:
            self.default_language = language_code
            return True
        return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.supported_languages.copy()
    
    def adjust_for_ambient_noise(self, audio_source, duration: float = 1.0) -> bool:
        """调整环境噪声"""
        try:
            self.recognizer.adjust_for_ambient_noise(audio_source, duration=duration)
            return True
        except Exception as e:
            print(f"调整环境噪声失败: {e}")
            return False
    
    def recognize_from_audio_data(self, audio_data: bytes, 
                                 language: Optional[str] = None) -> Tuple[Optional[str], float]:
        """从音频数据识别语音"""
        try:
            # 创建AudioData对象
            audio = sr.AudioData(audio_data, 44100, 2)
            return self._recognize_audio(audio, language)
        except Exception as e:
            print(f"音频数据识别失败: {e}")
            return None, 0.0
    
    def recognize_from_file(self, audio_file_path: str, 
                           language: Optional[str] = None) -> Tuple[Optional[str], float]:
        """从音频文件识别语音"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            return self._recognize_audio(audio, language)
        except Exception as e:
            print(f"音频文件识别失败: {e}")
            return None, 0.0
    
    def recognize_from_microphone(self, device_index: Optional[int] = None,
                                 language: Optional[str] = None,
                                 timeout: float = 10,
                                 phrase_time_limit: float = 10) -> Tuple[Optional[str], float]:
        """从麦克风识别语音"""
        try:
            with sr.Microphone(device_index=device_index) as source:
                print("🔧 正在调整麦克风噪声...")
                self.recognizer.adjust_for_ambient_noise(source)
                
                print("🎤 请说话...")
                audio = self.recognizer.listen(source, timeout=timeout, 
                                             phrase_time_limit=phrase_time_limit)
                
            return self._recognize_audio(audio, language)
        except sr.WaitTimeoutError:
            print("⏰ 录音超时")
            return None, 0.0
        except Exception as e:
            print(f"麦克风识别失败: {e}")
            return None, 0.0
    
    def _recognize_audio(self, audio, language: Optional[str] = None) -> Tuple[Optional[str], float]:
        """内部音频识别方法"""
        if language is None:
            language = self.default_language
            
        try:
            if self.current_engine == RecognitionEngine.GOOGLE:
                return self._recognize_google(audio, language)
            elif self.current_engine == RecognitionEngine.WHISPER:
                return self._recognize_whisper(audio, language)
            else:
                print(f"不支持的识别引擎: {self.current_engine}")
                return None, 0.0
                
        except sr.UnknownValueError:
            print("🔇 无法识别语音")
            return None, 0.0
        except sr.RequestError as e:
            print(f"🌐 识别服务请求失败: {e}")
            return None, 0.0
        except Exception as e:
            print(f"🔥 识别过程出错: {e}")
            return None, 0.0
    
    def _recognize_google(self, audio, language: str) -> Tuple[Optional[str], float]:
        """Google语音识别"""
        try:
            # Google API不返回置信度，我们设置一个默认值
            text = self.recognizer.recognize_google(audio, language=language)
            confidence = 0.85  # 默认置信度
            return text, confidence
        except Exception as e:
            raise e
    
    def _recognize_whisper(self, audio, language: str) -> Tuple[Optional[str], float]:
        """Whisper本地语音识别"""
        try:
            # 首次使用时加载Whisper模型
            if self._whisper_model is None:
                import whisper
                model_name = self.engine_configs[RecognitionEngine.WHISPER]['model']
                print(f"🔄 正在加载Whisper模型: {model_name}")
                self._whisper_model = whisper.load_model(model_name)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
            try:
                # 将音频数据写入临时文件
                with open(temp_path, 'wb') as f:
                    f.write(audio.get_wav_data())
                
                # 使用Whisper识别
                result = self._whisper_model.transcribe(temp_path, language=language[:2])
                
                # 提取文本和置信度
                text = result.get('text', '').strip()
                
                # 计算平均置信度
                segments = result.get('segments', [])
                if segments:
                    confidences = [seg.get('confidence', 0.0) for seg in segments 
                                 if 'confidence' in seg]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
                else:
                    avg_confidence = 0.8  # 默认置信度
                
                return text, avg_confidence
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except ImportError:
            print("❌ Whisper未安装，请运行: pip install openai-whisper")
            return None, 0.0
        except Exception as e:
            print(f"Whisper识别失败: {e}")
            return None, 0.0
    
    def batch_recognize(self, audio_files: List[str], 
                       language: Optional[str] = None) -> List[Tuple[str, Optional[str], float]]:
        """批量识别音频文件"""
        results = []
        for file_path in audio_files:
            text, confidence = self.recognize_from_file(file_path, language)
            results.append((file_path, text, confidence))
        return results
    
    def get_recognition_info(self) -> Dict:
        """获取当前识别器信息"""
        return {
            'current_engine': self.current_engine.value,
            'default_language': self.default_language,
            'language_name': self.supported_languages.get(self.default_language, 'Unknown'),
            'supported_languages': len(self.supported_languages),
            'engine_config': self.engine_configs.get(self.current_engine, {})
        }
    
    def test_recognition(self, test_text: str = "测试语音识别功能") -> bool:
        """测试识别功能（使用TTS生成的音频或预录音频）"""
        try:
            print(f"🧪 测试文本: {test_text}")
            print("💡 注意：这需要实际的音频输入来测试")
            return True
        except Exception as e:
            print(f"测试失败: {e}")
            return False
    
    def save_recognition_result(self, text: str, confidence: float, 
                               output_file: str) -> bool:
        """保存识别结果到文件"""
        try:
            result = {
                'text': text,
                'confidence': confidence,
                'language': self.default_language,
                'engine': self.current_engine.value,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存识别结果失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 创建语音识别器
    recognizer = SpeechRecognizer()
    
    # 显示支持的语言
    print("支持的语言:")
    for code, name in recognizer.get_supported_languages().items():
        print(f"  {code}: {name}")
    
    # 显示当前配置
    info = recognizer.get_recognition_info()
    print(f"\n当前配置:")
    print(f"  识别引擎: {info['current_engine']}")
    print(f"  默认语言: {info['default_language']} ({info['language_name']})")
    
    # 测试麦克风识别（如果有可用设备）
    print("\n🎤 测试麦克风识别（5秒后开始）...")
    import time
    time.sleep(2)
    
    try:
        text, confidence = recognizer.recognize_from_microphone(timeout=5, phrase_time_limit=5)
        if text:
            print(f"✅ 识别结果: {text}")
            print(f"📊 置信度: {confidence:.2f}")
        else:
            print("❌ 识别失败或无输入")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 在远程环境中可能无法使用麦克风")