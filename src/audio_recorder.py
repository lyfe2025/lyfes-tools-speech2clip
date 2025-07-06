#!/usr/bin/env python3
"""
音频录制模块
负责处理音频设备检测、录制和音频格式转换
"""

import pyaudio
import wave
import threading
import time
from typing import Optional, List, Callable
import tempfile
import os


class AudioRecorder:
    """音频录制器类"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.channels = 1
        self.sample_format = pyaudio.paInt16
        self.recording_thread = None
        
        # 回调函数
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
    def get_audio_devices(self) -> List[dict]:
        """获取可用的音频设备列表"""
        devices = []
        try:
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate'])
                    })
        except Exception as e:
            if self.on_error:
                self.on_error(f"获取音频设备失败: {e}")
        return devices
    
    def get_default_input_device(self) -> Optional[dict]:
        """获取默认输入设备"""
        try:
            device_info = self.audio.get_default_input_device_info()
            return {
                'index': device_info['index'],
                'name': device_info['name'],
                'channels': device_info['maxInputChannels'],
                'sample_rate': int(device_info['defaultSampleRate'])
            }
        except Exception as e:
            if self.on_error:
                self.on_error(f"获取默认输入设备失败: {e}")
            return None
    
    def test_audio_device(self, device_index: Optional[int] = None) -> bool:
        """测试音频设备是否可用"""
        try:
            test_stream = self.audio.open(
                format=self.sample_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            test_stream.close()
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"音频设备测试失败: {e}")
            return False
    
    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """开始录音"""
        if self.is_recording:
            return False
            
        try:
            self.frames = []
            self.stream = self.audio.open(
                format=self.sample_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            if self.on_recording_start:
                self.on_recording_start()
                
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"开始录音失败: {e}")
            return False
    
    def stop_recording(self) -> Optional[bytes]:
        """停止录音并返回音频数据"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        # 等待录音线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # 关闭音频流
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.on_recording_stop:
            self.on_recording_stop()
        
        # 返回录音数据
        if self.frames:
            return b''.join(self.frames)
        return None
    
    def _record_audio(self):
        """内部录音循环"""
        try:
            while self.is_recording and self.stream:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
        except Exception as e:
            if self.on_error:
                self.on_error(f"录音过程出错: {e}")
    
    def save_audio_to_file(self, audio_data: bytes, filename: str) -> bool:
        """将音频数据保存到文件"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.sample_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"保存音频文件失败: {e}")
            return False
    
    def create_temp_audio_file(self, audio_data: bytes) -> Optional[str]:
        """创建临时音频文件"""
        try:
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            # 保存音频数据
            if self.save_audio_to_file(audio_data, temp_path):
                return temp_path
            else:
                os.unlink(temp_path)
                return None
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"创建临时音频文件失败: {e}")
            return None
    
    def get_audio_info(self) -> dict:
        """获取当前音频配置信息"""
        return {
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'sample_format': self.sample_format,
            'chunk_size': self.chunk_size,
            'is_recording': self.is_recording
        }
    
    def set_audio_config(self, sample_rate: int = None, channels: int = None, 
                        chunk_size: int = None):
        """设置音频配置"""
        if not self.is_recording:
            if sample_rate:
                self.sample_rate = sample_rate
            if channels:
                self.channels = channels
            if chunk_size:
                self.chunk_size = chunk_size
    
    def cleanup(self):
        """清理资源"""
        if self.is_recording:
            self.stop_recording()
        
        if self.audio:
            self.audio.terminate()


# 使用示例
if __name__ == "__main__":
    def on_start():
        print("🔴 开始录音...")
    
    def on_stop():
        print("⏹️ 停止录音")
    
    def on_error(error_msg):
        print(f"❌ 错误: {error_msg}")
    
    # 创建录音器
    recorder = AudioRecorder()
    recorder.on_recording_start = on_start
    recorder.on_recording_stop = on_stop
    recorder.on_error = on_error
    
    # 获取设备列表
    devices = recorder.get_audio_devices()
    print("可用音频设备:")
    for device in devices:
        print(f"  {device['index']}: {device['name']}")
    
    # 测试录音
    if devices:
        print("\n开始5秒录音测试...")
        if recorder.start_recording():
            time.sleep(5)
            audio_data = recorder.stop_recording()
            if audio_data:
                print(f"录音完成，数据长度: {len(audio_data)} 字节")
            else:
                print("录音失败")
        else:
            print("无法启动录音")
    
    recorder.cleanup()