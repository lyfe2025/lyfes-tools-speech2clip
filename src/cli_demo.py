#!/usr/bin/env python3
"""
Speech2Clip CLI Demo - 命令行演示版本
支持 Google/Whisper 两种语音识别引擎，默认本地Whisper
可通过 --device/-d 参数指定麦克风编号
"""

import sys
import time
import pyperclip
import argparse
from speech_recognizer import SpeechRecognizer, RecognitionEngine
import pyaudio
import wave
import numpy as np
from opencc import OpenCC
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

WHISPER_MODELS = ['tiny', 'base', 'small', 'medium', 'large']

cc = OpenCC('t2s')  # 繁体转简体

def list_devices():
    try:
        import speech_recognition as sr
        print('可用音频输入设备列表:')
        for i, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f'{i}: {name}')
    except Exception as e:
        print(f'❌ 设备列表获取失败: {e}')

def custom_record_with_silence_detection(device_index=None, silence_seconds=5, max_seconds=10, threshold=500):
    """
    用pyaudio采集音频流，连续silence_seconds静音则停止，否则最长max_seconds秒。
    threshold为静音判定阈值（可根据实际调整）。
    返回音频数据bytes。
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=device_index, frames_per_buffer=CHUNK)
    print(f"🎤 开始自定义录音，最长{max_seconds}秒，静音{silence_seconds}秒自动停止...")
    frames = []
    silent_chunks = 0
    max_chunks = int(RATE / CHUNK * max_seconds)
    silence_chunk_limit = int(RATE / CHUNK * silence_seconds)
    for i in range(max_chunks):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        audio_np = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_np ** 2))
        if rms < threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0
        if silent_chunks >= silence_chunk_limit:
            print(f"🛑 检测到连续{silence_seconds}秒静音，自动停止录音。")
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    # 保存为wav
    wf = wave.open('test_record.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print("录音已保存为 test_record.wav，请用播放器试听。")
    # 返回音频数据bytes
    return b''.join(frames)

def main():
    parser = argparse.ArgumentParser(description='Speech2Clip CLI Demo')
    parser.add_argument('engine', nargs='?', default='whisper', choices=['whisper', 'google'], help='语音识别引擎')
    parser.add_argument('--device', '-d', type=int, default=None, help='麦克风设备编号')
    parser.add_argument('--list-devices', action='store_true', help='列出所有可用音频输入设备')
    parser.add_argument('--whisper-model', type=str, default='base', choices=WHISPER_MODELS, help='Whisper模型名')
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    print("=" * 50)
    print("🎤 Speech2Clip CLI Demo")
    print("=" * 50)

    engine = RecognitionEngine.WHISPER if args.engine == 'whisper' else RecognitionEngine.GOOGLE
    print(f"🔄 识别引擎: {'Whisper 本地识别 (离线)' if engine == RecognitionEngine.WHISPER else 'Google 云端识别 (需联网)'}")
    if engine == RecognitionEngine.WHISPER:
        print(f"🧠 Whisper模型: {args.whisper_model}")
    if args.device is not None:
        print(f"🎧 使用麦克风设备编号: {args.device}")

    recognizer = SpeechRecognizer()
    recognizer.set_engine(engine)
    # 设置whisper模型
    if engine == RecognitionEngine.WHISPER:
        recognizer.engine_configs[RecognitionEngine.WHISPER]['model'] = args.whisper_model

    # 检查麦克风
    try:
        import speech_recognition as sr
        microphone = sr.Microphone(device_index=args.device)
        print(f"✅ 麦克风已检测到: {microphone.device_index} - {sr.Microphone.list_microphone_names()[microphone.device_index]}")
    except Exception as e:
        print(f"❌ 麦克风检测失败: {e}")
        print("📝 注意：在远程环境中，麦克风可能不可用")
        print("🔄 将使用模拟文本进行演示...")
        demo_text = "这是一个Speech2Clip演示文本，展示了语音转文本并复制到剪贴板的功能。"
        print(f"\n📝 模拟识别结果: {demo_text}")
        try:
            pyperclip.copy(demo_text)
            print("✅ 文本已复制到剪贴板")
            clipboard_content = pyperclip.paste()
            print(f"📋 剪贴板内容: {clipboard_content}")
        except Exception as e:
            print(f"❌ 剪贴板操作失败: {e}")
        return

    print("\n🎙️ 准备开始语音识别演示...")
    print("⏰ 5秒后开始录音，请准备说话...")
    for i in range(5, 0, -1):
        print(f"⏱️ {i}...")
        time.sleep(1)

    try:
        print("\n🔴 开始录音...")
        audio_data = custom_record_with_silence_detection(device_index=args.device, silence_seconds=5, max_seconds=10, threshold=500)
        # 送入识别（不再用内存流结果写剪贴板）
        text, confidence = recognizer.recognize_from_audio_data(audio_data, language='zh')
        if text:
            print(f"✅ 识别成功: {text}")
            print(f"🔢 置信度: {confidence:.2f}")
        else:
            print("❌ 识别失败或无语音内容")
        # 用文件方式再识别一次，并写入剪贴板
        file_text, file_conf = recognizer.recognize_from_file('test_record.wav', language='zh')
        simple_text = cc.convert(file_text) if file_text else ''
        print(f"[文件识别] 结果: {simple_text}, 置信度: {file_conf}")
        if simple_text:
            try:
                pyperclip.copy(simple_text)
                print("📋 [文件识别] 文本已复制到剪贴板")
                clipboard_content = pyperclip.paste()
                print(f"📋 剪贴板内容: {clipboard_content}")
            except Exception as e:
                print(f"❌ 剪贴板操作失败: {e}")
    except Exception as e:
        print(f"❌ 语音识别过程出错: {e}")
        if engine == RecognitionEngine.GOOGLE:
            print("💡 可能需要网络连接来使用Google语音识别")
        elif engine == RecognitionEngine.WHISPER:
            print("💡 Whisper模型需本地算力，首次运行会自动下载模型")

    print("\n" + "=" * 50)
    print("🎉 Speech2Clip CLI Demo 演示完成")
    print("=" * 50)

if __name__ == "__main__":
    main()