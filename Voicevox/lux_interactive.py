import time
import wave
import pyaudio
import TSL2591              # 照度センサ TSL2591
from PCA9685 import PCA9685  # サーボ制御用


# ===== サーボ設定 =====
SERVO_FREQ_HZ   = 50
SERVO_CH_X      = 0          # 左右
SERVO_CH_Y      = 1          # 上下
SERVO_MIN       = 30         # 暗いときの向きなどに利用
SERVO_MAX       = 150        # 明るいときの向き
SERVO_CENTER_X  = 90
SERVO_CENTER_Y  = 90

# ===== センサ初期化 =====
sensor = TSL2591.TSL2591()

# ===== サーボ初期化 =====
pwm = PCA9685()
pwm.setPWMFreq(SERVO_FREQ_HZ)

sx = SERVO_CENTER_X
sy = SERVO_CENTER_Y
pwm.setRotationAngle(SERVO_CH_X, sx)
pwm.setRotationAngle(SERVO_CH_Y, sy)


def play_wav(
    path: str,
    output_device_index: int = 2,
    chunk: int = 1024,
    pre_silence_ms: int = 30
) -> None:
    """WAVファイルを再生する。

    Args:
        path: WAVファイルパス
        output_device_index: 出力デバイス番号（HDMIなら0, ヘッドホンなら2など）
        chunk: バッファサイズ
        pre_silence_ms: 再生前に流す無音時間（ノイズ防止）
    """
    wf = wave.open(path, "rb")
    pa = pyaudio.PyAudio()

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

    # WAV再生
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    # 終了処理
    stream.stop_stream()
    stream.close()
    pa.terminate()
    wf.close()
    print(f"再生完了: {path}")


# ===== メインループ =====
prev_state = None  # "bright" / "dark" / "normal"

try:
    while True:
        # ---- Lux値（照度）を取得 ----
        lux = sensor.Lux
        print(f"現在の照度: {lux} lux")

        # 状態判定
        if lux > 500:
            state = "bright"
            # 明るいときのサーボ姿勢（例: どちらも最大側）
            sx = SERVO_MAX
            sy = SERVO_MAX
            pwm.setRotationAngle(SERVO_CH_X, sx)
            pwm.setRotationAngle(SERVO_CH_Y, sy)

        elif lux < 10:
            state = "dark"
            # 暗いときのサーボ姿勢（例: どちらも最小側）
            sx = SERVO_MIN
            sy = SERVO_MIN
            pwm.setRotationAngle(SERVO_CH_X, sx)
            pwm.setRotationAngle(SERVO_CH_Y, sy)

        else:
            state = "normal"
            # ふつうの明るさのときは中央
            sx = SERVO_CENTER_X
            sy = SERVO_CENTER_Y
            pwm.setRotationAngle(SERVO_CH_X, sx)
            pwm.setRotationAngle(SERVO_CH_Y, sy)

        # 状態が変わったときだけ音声を再生
        if state != prev_state:
            if state == "bright":
                play_wav("./output1.wav", output_device_index=2)
            elif state == "dark":
                play_wav("./output2.wav", output_device_index=2)
            # normal になったときは何も再生しない例
            prev_state = state

        # ---- 割り込み閾値を設定（任意）----
        # 例: 暗すぎる（50以下）または明るすぎる（200以上）でハード側割り込み
        sensor.TSL2591_SET_LuxInterrupt(50, 200)

        # ---- 取得間隔 ----
        time.sleep(1.0)  # 1秒ごとに更新

except KeyboardInterrupt:
    print("\n停止しました。プログラムを終了します。")
    pwm.exit_PCA9685()
