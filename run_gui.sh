#!/bin/bash
# Speech2Clip GUI 一键运行脚本（PyQt5 版）

# set -e  # 临时注释，便于调试

# 自动探测 pyenv 当前可用 python3 路径，允许通过环境变量覆盖
# 优先使用 pyenv which python3，找不到则用 which python3
# 如需强制指定，可 export PYTHON311_OVERRIDE=xxx
PYTHON311="${PYTHON311_OVERRIDE:-$(pyenv which python3 2>/dev/null || which python3)}"

echo "==== Speech2Clip GUI 启动脚本 ===="

if [ -z "$PYTHON311" ] || [ ! -x "$PYTHON311" ]; then
  echo "未检测到可用的 python3 解释器，请检查 pyenv 或系统环境。"
  exit 1
fi

echo "[DEBUG] 使用 python3 路径：$PYTHON311"

# 强制激活 pyenv 3.11.9 环境，确保依赖一致（如有需要可保留，否则可注释）
if command -v pyenv &>/dev/null; then
  pyenv shell 3.11.9
  echo "[DEBUG] 已强制激活 pyenv shell 3.11.9"
fi

echo "[DEBUG] 检查 pyenv 环境..."
# 优先激活 pyenv 环境，确保用 pyenv 的 python3
if command -v pyenv &>/dev/null; then
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init --path)"
  echo "[DEBUG] pyenv 环境已激活"
else
  echo "[DEBUG] 未检测到 pyenv，跳过 pyenv 激活"
fi

echo "[DEBUG] 检查主程序是否存在..."
# 检查主程序是否存在
if [ ! -f src/gui_main_qt.py ]; then
  echo "未找到 src/gui_main_qt.py，请确认已生成 PyQt5 主程序。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 10
fi

echo "[DEBUG] 检查 Python3 是否可用..."
# 检查 Python3 是否可用
if ! $PYTHON311 --version &>/dev/null; then
  echo "未检测到 $PYTHON311，请先安装 Python 3.11.9。"
  read -n 1 -s -r -p "按任意键退出..."
  exit 1
fi

echo "[DEBUG] 检查 PyQt5 支持..."
# 检查 PyQt5 支持
$PYTHON311 -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "当前 python3 缺少 PyQt5 支持。"
  echo "请执行：$PYTHON311 -m pip install pyqt5"
  read -n 1 -s -r -p "按任意键退出..."
  exit 2
fi

echo "[DEBUG] 检查 keyboard 支持..."
# 检查 keyboard 支持
$PYTHON311 -c "import keyboard" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "当前 python3 缺少 keyboard 支持。"
  echo "请执行：$PYTHON311 -m pip install keyboard"
  echo "[DEBUG] 当前 python3 路径：$PYTHON311"
  $PYTHON311 -c "import sys; print('sys.path:', sys.path)"
  $PYTHON311 -c "import site; print('site-packages:', site.getsitepackages())"
  read -n 1 -s -r -p "按任意键退出..."
  exit 3
fi

echo "[DEBUG] 检查 opencc 支持..."
# 检查 opencc 支持
$PYTHON311 -c "import opencc" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "当前 python3 缺少 opencc 支持。"
  echo "请执行：$PYTHON311 -m pip install opencc-python-reimplemented"
  read -n 1 -s -r -p "按任意键退出..."
  exit 4
fi

echo "[DEBUG] 检查 whisper 支持..."
# 检查 whisper 支持
$PYTHON311 -c "import whisper" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "当前 python3 缺少 whisper 支持。"
  echo "请执行：$PYTHON311 -m pip install -U openai-whisper"
  read -n 1 -s -r -p "按任意键退出..."
  exit 5
fi

# =================== 主菜单交互 ===================
# 支持的官方模型
ALL_MODELS=("tiny" "base" "small" "medium" "large" "large-v3")
WHISPER_MODEL_DIRS=("$HOME/.cache/whisper" "$HOME/.cache/whisper/models")

menu_loop=true
while [ "$menu_loop" = true ]; do
  # 刷新本地模型列表
  MODEL_PATHS=()
  MODEL_NAMES=()
  for d in "${WHISPER_MODEL_DIRS[@]}"; do
    if [ -d "$d" ]; then
      for f in "$d"/*.pt; do
        if [ -e "$f" ]; then
          model_name=$(basename "$f" .pt)
          MODEL_PATHS+=("$f")
          MODEL_NAMES+=("$model_name")
        fi
      done
    fi
  done
  echo "\n==== Speech2Clip 主菜单 ===="
  echo "1. 下载模型（仅显示未下载的）"
  echo "2. 查看当前已有模型"
  echo "3. 删除模型"
  echo "4. 运行GUI主程序"
  echo "5. 退出"
  read -p "请选择操作 [1-5]（直接回车默认运行GUI主程序）: " menu_choice
  # 新增：回车默认运行GUI
  if [ -z "$menu_choice" ]; then
    menu_choice=4
  fi
  case $menu_choice in
    1)
      # 下载模型
      echo "\n[可下载模型]:"
      idx=1
      DOWNLOADABLE_MODELS=()
      for m in "${ALL_MODELS[@]}"; do
        found=0
        for n in "${MODEL_NAMES[@]}"; do
          if [ "$m" = "$n" ]; then found=1; break; fi
        done
        if [ $found -eq 0 ]; then
          echo "  [$idx] $m"
          DOWNLOADABLE_MODELS+=("$m")
          idx=$((idx+1))
        fi
      done
      if [ ${#DOWNLOADABLE_MODELS[@]} -eq 0 ]; then
        echo "所有官方模型均已下载。"
      else
        read -p "请输入要下载的模型编号（如1或1,3），或回车跳过: " dl_idx
        if [ -n "$dl_idx" ]; then
          IFS=',' read -ra DL_ARR <<< "$dl_idx"
          for i in "${DL_ARR[@]}"; do
            idx=$((i-1))
            if [ $idx -ge 0 ] && [ $idx -lt ${#DOWNLOADABLE_MODELS[@]} ]; then
              m="${DOWNLOADABLE_MODELS[$idx]}"
              echo "[DEBUG] 开始下载 whisper 模型: $m ..."
              $PYTHON311 -c "import whisper; whisper.load_model('$m')"
              if [ $? -ne 0 ]; then
                echo "[错误] 模型 $m 下载失败，请检查网络或手动下载。"
              else
                echo "[DEBUG] 模型 $m 下载完成。"
              fi
            fi
          done
        fi
      fi
      ;;
    2)
      # 查看已有模型
      echo "\n[本地已存在的whisper模型]:"
      if [ ${#MODEL_NAMES[@]} -eq 0 ]; then
        echo "  (无)"
      else
        idx=1
        for m in "${MODEL_NAMES[@]}"; do
          echo "  [$idx] $m (${MODEL_PATHS[$((idx-1))]})"
          idx=$((idx+1))
        done
      fi
      ;;
    3)
      # 删除模型
      if [ ${#MODEL_NAMES[@]} -eq 0 ]; then
        echo "无可删除模型。"
      else
        echo "\n[本地已存在的whisper模型]:"
        idx=1
        for m in "${MODEL_NAMES[@]}"; do
          echo "  [$idx] $m (${MODEL_PATHS[$((idx-1))]})"
          idx=$((idx+1))
        done
        read -p "请输入要删除的模型编号（如1或1,3），或回车跳过: " del_idx
        if [ -n "$del_idx" ]; then
          IFS=',' read -ra IDX_ARR <<< "$del_idx"
          echo "你选择将删除以下模型："
          for i in "${IDX_ARR[@]}"; do
            idx=$((i-1))
            if [ $idx -ge 0 ] && [ $idx -lt ${#MODEL_PATHS[@]} ]; then
              echo "  - ${MODEL_NAMES[$idx]} (${MODEL_PATHS[$idx]})"
            fi
          done
          read -p "确认删除以上模型? 此操作不可恢复! [y/N] " confirm_del
          confirm_del=${confirm_del:-N}
          if [[ "$confirm_del" =~ ^[Yy]$ ]]; then
            for i in "${IDX_ARR[@]}"; do
              idx=$((i-1))
              if [ $idx -ge 0 ] && [ $idx -lt ${#MODEL_PATHS[@]} ]; then
                rm -f "${MODEL_PATHS[$idx]}"
                echo "已删除: ${MODEL_NAMES[$idx]} (${MODEL_PATHS[$idx]})"
              fi
            done
          else
            echo "已取消删除操作。"
          fi
        fi
      fi
      ;;
    4)
      # 运行GUI
      menu_loop=false
      ;;
    5)
      echo "已选择退出。"
      exit 0
      ;;
    *)
      echo "无效选项，请重新输入。"
      ;;
  esac
done
# =================== 主菜单交互 END ===================

# 检查麦克风设备（heredoc方式，输出友好）
MIC_CHECK_OUTPUT=$($PYTHON311 <<'EOF'
import sys
try:
    import pyaudio
    pa = pyaudio.PyAudio()
    found = False
    device_infos = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        device_infos.append(info)
        # 兼容macOS: hostApi为Core Audio且设备名包含Microphone/麦克风/Input等也判定为输入设备
        if (info.get('maxInputChannels', 0) > 0) or ('microphone' in info.get('name','').lower()) or ('input' in info.get('name','').lower()) or ('麦克风' in info.get('name','')):
            found = True
    pa.terminate()
    if found:
        print('OK')
    else:
        print('NO_MIC')
        print('==== 设备详细信息如下（供排查）====')
        for d in device_infos:
            print(d)
except Exception as e:
    print('NO_MIC')
    print('检测麦克风时发生异常:', e)
EOF
)
if echo "$MIC_CHECK_OUTPUT" | grep -q '^OK$'; then
  echo "[信息] 已检测到麦克风输入设备。"
else
  echo "[警告] 未检测到麦克风输入设备，语音功能可能无法使用。"
  echo "$MIC_CHECK_OUTPUT" | grep -v '^NO_MIC$' | grep -v '^OK$'
  read -p "是否仍要继续运行GUI主程序？[y/N] " mic_continue
  mic_continue=${mic_continue:-N}
  if [[ ! "$mic_continue" =~ ^[Yy]$ ]]; then
    echo "已选择退出。"
    exit 0
  fi
fi

echo "[DEBUG] 检查 macOS 热键兼容提示..."
# macOS 下 keyboard 热键不可用友好提示
if [[ "$(uname)" == "Darwin" ]]; then
  echo "[提示] macOS 下 keyboard 全局热键不可用，已自动兼容跳过，无需担心。"
fi

echo "[DEBUG] 依赖齐全，准备启动 GUI..."
echo "当前 python3 依赖齐全，直接运行 GUI"
$PYTHON311 src/gui_main_qt.py 2>&1 | tee /tmp/speech2clip_gui.log
status=${PIPESTATUS[0]}

echo "[DEBUG] GUI 进程退出码：$status"
if [ $status -ne 0 ]; then
  echo
  echo "GUI 启动失败，请检查终端输出的错误信息。"
  echo "--- 日志关键片段 ---"
  tail -n 30 /tmp/speech2clip_gui.log
  echo "---------------------"
  if grep -q 'AttributeError: .*record_btn' /tmp/speech2clip_gui.log; then
    echo
    echo "【友好提示】检测到 Python 代码初始化顺序问题（record_btn 未初始化）。"
    echo "请确认 src/gui_main_qt.py 已保存为最新修正版，并确保 check_model_status 的调用在 record_btn 创建后。"
  fi
  read -n 1 -s -r -p "按任意键退出..."
  exit 99
fi 