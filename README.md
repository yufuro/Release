プラットフォームは　Raspberry pi 4/4G

OSはBookworm(64bit)normal インストールにて実証済み

2025/11/14 ロボティクス体験講座にて使用 

[セットアップ手順]

① /home/<ユーザー名>上にReleaseリポジトリを展開　\n
$ cd 

$ github clone https://github.com/yufuro/Release.git

② システムファイルを設定します

$ sh ./Release/setup/setup_raspi.sh

③ 自動再起動のちにインストール作業を行います

$ sh ./Release/setup/setup.sh
