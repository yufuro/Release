プラットフォームは　Raspberry pi 4/4G

OSはBookworm(64bit)normal インストールにて実証済み

2025/11/14 ロボティクス体験講座にて使用 

セットアップ手順

個人のルートファイル上にReleaseファイルを展開
$ cd 
$ github clone https://github.com/yufuro/Release.git

1 システムファイルを設定します

$ sh ./Release/setup/setup_raspi.sh

2 自動再起動のちにインストール作業を行います

$ sh ./Release/setup/setup.sh
