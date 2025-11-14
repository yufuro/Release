"""
TSL2591 照度センサ テストプログラム（初心者向けコメント付き）

概要:
- I2C 接続の高感度照度センサ TSL2591 を使用。
- 周囲光の明るさ（Lux）を一定周期で取得して表示。
- （必要に応じて）閾値を設定して割り込み検出も可能。

注意:
- I2C が有効化されている必要があります（raspi-config → Interface Options → I2C → Enable）
- Python用のライブラリ "TSL2591" がインストール済みであること。
"""

import time
import TSL2591  # センサドライバモジュールの読み込み

# ===== センサ初期化 =====
sensor = TSL2591.TSL2591()  # TSL2591クラスのインスタンスを作成

# 必要に応じて割り込み閾値を設定（下限値, 上限値）
# センサがこの範囲を超えるとハードウェア割り込み信号が出る
# ここではデフォルトのままコメントアウトしています
# sensor.SET_InterruptThreshold(0xff00, 0x0010)

print("TSL2591 照度センサのテストを開始します。Ctrl+C で終了できます。")

try:
    while True:
        # ---- Lux値（照度）を取得 ----
        lux = sensor.Lux  # 現在の照度を Lux 単位で取得

        # ---- 結果を表示 ----
        print(f"現在の照度: {lux} lux")

        # ---- 割り込み閾値を設定（任意）----
        # 例えば、暗すぎる（50以下）または明るすぎる（200以上）で反応
        sensor.TSL2591_SET_LuxInterrupt(50, 200)

        # ---- 詳細データを個別に読みたい場合 ----
        # 以下のコメントを外すと、各チャンネルの値を取得できます。
        # infrared = sensor.Read_Infrared
        # print(f"赤外線成分: {infrared}")
        # visible = sensor.Read_Visible
        # print(f"可視光成分: {visible}")
        # full_spectrum = sensor.Read_FullSpectrum
        # print(f"全光成分(IR+可視光): {full_spectrum}")

        # ---- 取得間隔 ----
        time.sleep(1.0)  # 1秒ごとに更新（必要に応じて調整）

except KeyboardInterrupt:
    # Ctrl+Cで安全に終了
    print("\n停止しました。プログラムを終了します。")
