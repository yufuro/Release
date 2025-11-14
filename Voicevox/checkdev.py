import pyaudio

# PyAudio を使うための準備（初期化）
p = pyaudio.PyAudio()

# --------------------------------------------
#  利用できる入出力デバイス（マイク・スピーカー）を一覧表示
# --------------------------------------------
for i in range(p.get_device_count()):
    # デバイス番号 i の情報を取得
    info = p.get_device_info_by_index(i)

    # 取得した情報の中から、
    # ・デバイス名
    # ・入力チャンネル数（録音ができるか）
    # ・出力チャンネル数（音を出せるか）
    # を表示する
    print(
        f"{i}: {info.get('name')}",
        f" | 入力(in): {info.get('maxInputChannels')}",
        f" | 出力(out): {info.get('maxOutputChannels')}"
    )

# PyAudio を終了（後片付け）
p.terminate()
