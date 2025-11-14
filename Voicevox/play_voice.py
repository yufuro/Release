import pyaudio
import wave


def play_wav(
    wav_path: str = "./output1.wav",
    output_device_index: int = 2,  # 例: HDMI=0, bcm2835 Headphones=2
    chunk: int = 1024,
    pre_silence_ms: int = 30       # 再生前に流す無音時間（ノイズ防止）
):
    """指定したWAVファイルを再生する。

    Args:
        wav_path (str): 再生するWAVファイルのパス
        output_device_index (int): 出力デバイス番号
        chunk (int): バッファサイズ
        pre_silence_ms (int): 再生前に流す無音時間（ms単位）
    """
    wf = wave.open(wav_path, "rb")
    pa = pyaudio.PyAudio()

    # 出力ストリームを開く
    stream = pa.open(
        format=pa.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True,
        output_device_index=output_device_index,
        input=False,  # 再生専用
        frames_per_buffer=chunk,
    )

    # 無音プライミング（再生開始時の「パチッ」ノイズ防止）
    silent = (
        b"\x00"
        * int(wf.getframerate() * pre_silence_ms / 1000)
        * wf.getnchannels()
        * wf.getsampwidth()
    )
    stream.start_stream()
    stream.write(silent)

    # WAVデータを再生
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    # 終了処理
    stream.stop_stream()
    stream.close()
    pa.terminate()
    wf.close()
    print(f"再生完了: {wav_path}")


# 使用例
if __name__ == "__main__":
    play_wav("./output1.wav", output_device_index=2)
