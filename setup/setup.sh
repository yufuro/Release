#2025/11/15 PwCロボティクス体験で使用したパッケージです

cd 

#set up virtual environment
python3 -m venv --system-site-packages venv
. venv/bin/activate

#Japanease input system
sudo apt update
sudo apt install fcitx-mozc -y

#Thonny Configuration
cp ~/Release/setup/configuration.ini ~/.config/Thonny/

#install OPENCV
sudo apt update
sudo apt upgrade -y
sudo apt -y install libopencv-dev libopencv-core-dev python3-opencv libopencv-contrib-dev opencv-data
sudo apt -y install python-is-python3 python3-dev python-dev-is-python3 python3-pip python3-setuptools python3-venv build-essentialdmesg

#install voxvox
#mkdir Voicevox
cd ~/Release/Voicevox/
#python -m venv voicevox
#source voicevox/bin/activate
wget https://github.com/VOICEVOX/voicevox_core/releases/download/0.14.0/voicevox_core-0.14.0+cpu-cp38-abi3-linux_aarch64.whl
pip install voicevox_core-0.14.0+cpu-cp38-abi3-linux_aarch64.whl
#wget https://github.com/microsoft/onnxruntime/releases/download/v1.13.1/onnxruntime-linux-aarch64-1.13.1.tgz
#tar zxvf onnxruntime-linux-aarch64-1.13.1.tgz
ln -s onnxruntime-linux-aarch64-1.13.1/lib/libonnxruntime.so.1.13.1
#wget https://jaist.dl.sourceforge.net/project/open-jtalk/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_utf_8-1.11.tar.gz
#tar xzvf open_jtalk_dic_utf_8-1.11.tar.gz

cd 
#git clone https://github.com/yufuro/Release.git

#install Pyaudio
sudo apt-get install python3-pyaudio -y
pip install pyaudio

#install Mediapipe
sudo apt install libcap-dev -y
cd ~/Release/object_detection
sh ./setup.sh

