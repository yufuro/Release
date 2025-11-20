#!/bin/bash
# 2025/11/15 PwCロボティクス体験で使用したパッケージです

set -e  # エラーが出たらそこで止める（任意）

cd "$HOME"

# set up virtual environment
python3 -m venv --system-site-packages venv
. venv/bin/activate

# install OPENCV
sudo apt update
sudo apt upgrade -y
sudo apt -y install libopencv-dev libopencv-core-dev python3-opencv libopencv-contrib-dev opencv-data
sudo apt -y install python-is-python3 python3-dev python-dev-is-python3 python3-pip python3-setuptools python3-venv build-essential

# install voicevox
cd "$HOME/Release/Voicevox/"
wget https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.0/voicevox_core-0.14.0+cpu-cp38-abi3-linux_aarch64.whl
pip install voicevox_core-0.14.0+cpu-cp38-abi3-linux_aarch64.whl
# onnxruntime の tar を展開している前提
ln -s onnxruntime-linux-aarch64-1.13.1/lib/libonnxruntime.so.1.13.1
wget https://jaist.dl.sourceforge.net/project/open-jtalk/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_utf_8-1.11.tar.gz
tar xzvf open_jtalk_dic_utf_8-1.11.tar.gz

# Japanese input system
sudo apt update
sudo apt install fcitx-mozc -y

# Thonny Configuration
mkdir -p "$HOME/.config/Thonny"
/usr/bin/cp "$HOME/Release/setup/configuration.ini" "$HOME/.config/Thonny/"

cd "$HOME"

# install Pyaudio
sudo apt-get install python3-pyaudio -y
pip install pyaudio

# install Mediapipe
sudo apt install libcap-dev -y
cd "$HOME/Release/object_detection"
sh ./setup.sh
