#!/usr/bin/python3
"""
PCA9685 を使ってサーボモーターを動かすサンプル
（初心者向けコメント付き）

ポイント:
- PCA9685 は I2C 接続の 16チャネルPWMドライバ
- setRotationAngle(チャネル, 角度) で簡単にサーボを動かせる
- 角度は 0〜180 の範囲（サーボによって有効範囲は異なる）
"""

import time
from PCA9685 import PCA9685


# ==========================================
# ① PCA9685 の初期化
# ==========================================
pwm = PCA9685()          # PCA9685 クラスのインスタンスを作成
pwm.setPWMFreq(50)       # サーボの制御周波数は通常 50Hz

print("PCA9685 サーボテスト開始")


try:
    # --------------------------------------
    # 初期姿勢：サーボを0度にしておく
    # --------------------------------------
    pwm.setRotationAngle(0, 0)   # サーボ0 を 0度へ
    pwm.setRotationAngle(1, 0)   # サーボ1 を 0度へ
    time.sleep(1)

    # ==========================================
    # ② メインループ：角度をゆっくり往復させる
    # ==========================================
    while True:

        # ---- 0度 → 150度 へゆっくり動かす ----
        for angle in range(30, 150, 1):
            pwm.setRotationAngle(0, angle)   # チャネル0を動かす
            pwm.setRotationAngle(1, angle)   # チャネル1も同じ動作
            time.sleep(0.1)                  # 100ms待つ（ゆっくり動かすため）

        # ---- 150度 → 30度 に戻す ----
        for angle in range(150, 30, -1):
            pwm.setRotationAngle(0, angle)
            pwm.setRotationAngle(1, angle)
            time.sleep(0.1)

except KeyboardInterrupt:
    # Ctrl+C で止めたときに安全に終了
    print("\n停止しました。プログラムを終了します。")

finally:
    # ==========================================
    # ③ 後片付け
    # ==========================================
    pwm.exit_PCA9685()
    print("Program end")
