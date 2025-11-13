"""
TSL2591 照度センサ + OpenCV 可視化（初心者向けコメント付き）

機能:
- 現在のLux値を大きな文字とバーグラフで表示
- 直近の履歴（スパークライン）を折れ線で描画
- 表示レンジは固定MAXまたは自動レンジ（AUTO_RANGE）が選べる

依存:
- pip install TSL2591 opencv-python
- I2Cを有効化済み (raspi-config → Interface Options → I2C → Enable)
"""

import time
from collections import deque
import numpy as np
import cv2
import TSL2591

# ===================== 設定（ここを調整） =====================
WINDOW_NAME         = "Lux Monitor"
SAMPLE_INTERVAL_SEC = 0.1        # 取得間隔（秒）
HISTORY_LEN         = 300        # スパークラインに保持する点数（描画幅に応じて）
EMA_ALPHA           = 0.2        # 指数移動平均（0〜1、小さいほどなめらか）
AUTO_RANGE          = True       # Trueで自動レンジ、Falseで固定レンジ
MAX_LUX_DISPLAY     = 1000.0     # 固定レンジ時の最大Lux（AUTO_RANGE=Falseのとき使用）
AUTO_DECAY          = 0.995      # 自動レンジの上限を徐々に下げる減衰率（0.99〜0.999位）
MARGIN              = 20         # 余白（ピクセル）
IMG_W, IMG_H        = 800, 300   # ウィンドウのサイズ
BAR_H               = 60         # バーの高さ（ピクセル）
FONT                = cv2.FONT_HERSHEY_SIMPLEX
# ============================================================

# センサ初期化
sensor = TSL2591.TSL2591()

# 履歴とスムージング用
history = deque(maxlen=HISTORY_LEN)
lux_smooth = None
auto_max = 50.0  # 自動レンジの初期上限（暗い部屋想定で控えめに開始）

def lerp_color(a, b, t):
    """2色（BGR）をtで線形補間（0〜1）"""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_ui(img, lux, lux_disp_max, hist):
    """OpenCVでUIを描画"""
    # 背景
    img[:] = (245, 245, 245)

    # タイトル
    cv2.putText(img, "TSL2591 Lux Monitor", (MARGIN, 40),
                FONT, 0.9, (0, 0, 0), 2, cv2.LINE_AA)

    # 現在のLux表示（大きく）
    cv2.putText(img, f"Lux: {lux:.1f}", (MARGIN, 100),
                FONT, 1.2, (20, 20, 20), 3, cv2.LINE_AA)

    # レンジ表示
    range_text = f"Range: 0 - {lux_disp_max:.0f}  {'(AUTO)' if AUTO_RANGE else '(FIXED)'}"
    cv2.putText(img, range_text, (MARGIN, 135),
                FONT, 0.7, (60, 60, 60), 2, cv2.LINE_AA)

    # バーの枠
    bar_x1 = MARGIN
    bar_x2 = IMG_W - MARGIN
    bar_y1 = 160
    bar_y2 = bar_y1 + BAR_H
    cv2.rectangle(img, (bar_x1, bar_y1), (bar_x2, bar_y2), (180, 180, 180), 2)

    # バーの長さ（0〜1 に正規化）
    t = max(0.0, min(1.0, lux / max(lux_disp_max, 1e-6)))
    bar_w = int((bar_x2 - bar_x1 - 2) * t)

    # バーの色（暗→明で 青→緑→黄→赤 に近づく感じ）
    # 青(255,100,0) → 緑(0,200,0) → 黄(0,255,255) → 赤(0,0,255)
    if t < 0.33:
        c = lerp_color((255, 100, 0), (0, 200, 0), t / 0.33)
    elif t < 0.66:
        c = lerp_color((0, 200, 0), (0, 255, 255), (t - 0.33) / 0.33)
    else:
        c = lerp_color((0, 255, 255), (0, 0, 255), (t - 0.66) / 0.34)

    # バー本体
    cv2.rectangle(img, (bar_x1 + 1, bar_y1 + 1), (bar_x1 + 1 + bar_w, bar_y2 - 1), c, -1)

    # 目盛（25%, 50%, 75%, 100%）
    for frac in (0.25, 0.5, 0.75, 1.0):
        x = int(bar_x1 + (bar_x2 - bar_x1) * frac)
        cv2.line(img, (x, bar_y1), (x, bar_y2), (200, 200, 200), 1)
        cv2.putText(img, f"{int(lux_disp_max * frac)}", (x - 20, bar_y2 + 20),
                    FONT, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    # スパークライン（履歴）
    spark_x1 = MARGIN
    spark_x2 = IMG_W - MARGIN
    spark_y1 = bar_y2 + 40
    spark_y2 = IMG_H - MARGIN
    cv2.rectangle(img, (spark_x1, spark_y1), (spark_x2, spark_y2), (210, 210, 210), 2)

    if len(hist) >= 2:
        # ヒストリを0〜1に正規化して下から上へ描く
        vals = np.array(hist, dtype=np.float32)
        vmax = max(lux_disp_max, float(vals.max()), 1.0)
        vmin = 0.0
        norm = (vals - vmin) / (vmax - vmin + 1e-9)
        # 横方向は等間隔に敷き詰め
        w = spark_x2 - spark_x1 - 2
        h = spark_y2 - spark_y1 - 2
        xs = np.linspace(spark_x1 + 1, spark_x2 - 1, len(vals)).astype(int)
        ys = (spark_y2 - 1 - (norm * h)).astype(int)

        # 折れ線描画
        for i in range(1, len(xs)):
            cv2.line(img, (xs[i-1], ys[i-1]), (xs[i], ys[i]), (80, 80, 220), 2)

        # 最新点を強調
        cv2.circle(img, (xs[-1], ys[-1]), 4, (0, 0, 255), -1)


def main():
    global lux_smooth, auto_max

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, IMG_W, IMG_H)

    print("TSL2591 + OpenCV 可視化を開始します。ESCで終了。")

    try:
        while True:
            # ---- センサからLux取得 ----
            lux = float(sensor.Lux)

            # ---- スムージング（指数移動平均）----
            if lux_smooth is None:
                lux_smooth = lux
            else:
                lux_smooth = (1 - EMA_ALPHA) * lux_smooth + EMA_ALPHA * lux

            # ---- 履歴更新 ----
            history.append(lux_smooth)

            # ---- 表示レンジの決定 ----
            if AUTO_RANGE:
                # 新しい値で上限を押し上げ、徐々に減衰させて追従
                auto_max = max(auto_max * AUTO_DECAY, lux_smooth * 1.1, 10.0)
                lux_disp_max = auto_max
            else:
                lux_disp_max = MAX_LUX_DISPLAY

            # ---- 描画キャンバス作成 ----
            canvas = np.zeros((IMG_H, IMG_W, 3), dtype=np.uint8)
            draw_ui(canvas, lux_smooth, lux_disp_max, history)

            # ---- 表示 ----
            cv2.imshow(WINDOW_NAME, canvas)

            # ---- キー判定（ESCで終了）----
            if (cv2.waitKey(1) & 0xFF) == 27:
                break

            time.sleep(SAMPLE_INTERVAL_SEC)

    finally:
        cv2.destroyAllWindows()
        print("終了しました。")

if __name__ == "__main__":
    main()
