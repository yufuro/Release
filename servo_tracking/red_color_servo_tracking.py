"""
Raspberry Pi + PiCamera2 + OpenCV + PCA9685 (サーボ2軸) で
「赤色物体を検出して追尾する」サンプル（初学者向けコメント付き）

ポイント
- PiCamera2 は RGB でフレームを返すので、処理用は RGB のまま扱う。
- OpenCV の表示は BGR 前提なので、表示直前にだけ BGR に変換する。
- 例外が起きても確実にリソース解放できるよう try/finally を使う。
"""

# ===== ライブラリ読み込み =====
import time
import numpy as np
import cv2

# PiCamera2（カメラ制御）
from picamera2 import Picamera2
from libcamera import controls

# サーボ制御（PCA9685）
from PCA9685 import PCA9685

# ===== 定数（意味のある名前をつける） =====
FRAME_SIZE = (640, 480)          # 取得するフレームの解像度 (幅, 高さ)
HSV_RED_RANGE_1 = (np.array([0,   120, 70], dtype=np.uint8),
                   np.array([10,  255, 255], dtype=np.uint8))
HSV_RED_RANGE_2 = (np.array([170, 120, 70], dtype=np.uint8),
                   np.array([179, 255, 255], dtype=np.uint8))

SERVO_FREQ_HZ = 50               # PCA9685 のPWM周波数（サーボは一般に 50Hz）
SERVO_CH_X = 0                   # X方向（左右）サーボのチャンネル番号
SERVO_CH_Y = 1                   # Y方向（上下）サーボのチャンネル番号
SERVO_MIN = 30                   # 物理的に無理のない最小角度（環境に応じて調整）
SERVO_MAX = 150                  # 物理的に無理のない最大角度（環境に応じて調整）
SERVO_CENTER_X = 90              # 初期角度（X）
SERVO_CENTER_Y = 90              # 初期角度（Y）
SERVO_STEP = 2                   # 1回の更新で動かす角度（大きいと速いが振動しやすい）

CENTER_MARGIN_PX = 20            # 画面中心の「許容マージン」（ピクセル）
MORPH_KERNEL_SIZE = (3, 3)       # ノイズ除去のカーネルサイズ
GAUSS_KERNEL_SIZE = (5, 5)       # ぼかしのカーネルサイズ
WINDOW_MASK = 'Mask_Live'        # マスク表示ウィンドウ名
WINDOW_CAMERA = 'RaspiCam_Live'  # カメラ表示ウィンドウ名


# ===== 赤色領域を2値マスクで取り出す関数（入力は RGB） =====
def red_mask_rgb(img_rgb: np.ndarray) -> np.ndarray:
    """
    入力:  RGB画像 (H, W, 3)  例: dtype=uint8, 0-255
    出力:  赤色っぽい部分の2値マスク (uint8, 0 or 255)

    手順:
    1) ぼかしでノイズを軽減
    2) RGB -> HSV へ変換（OpenCVのHは0-179）
    3) 赤は色相が 0 近傍 と 179 近傍 に分布するため、2つの範囲を OR 結合
    4) 形態学的処理（開閉）で小ノイズ除去＆穴埋め
    """
    # 1) ノイズ軽減（ガウシアンぼかし）
    blur = cv2.GaussianBlur(img_rgb, GAUSS_KERNEL_SIZE, 0)

    # 2) 色空間変換（RGB -> HSV）
    hsv = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)

    # 3) 赤の2レンジを inRange でそれぞれ抽出して OR
    (lower1, upper1) = HSV_RED_RANGE_1
    (lower2, upper2) = HSV_RED_RANGE_2
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    # 4) 小ノイズ除去＆穴埋め（開→閉）
    kernel = np.ones(MORPH_KERNEL_SIZE, np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    return mask


# ===== 初期化：カメラ & サーボ =====
picam2 = Picamera2()
# 取得するフレームのフォーマットを「RGB888」、サイズを指定
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": FRAME_SIZE}
    )
)
picam2.start()

# オートフォーカスを連続モードに設定（レンズ付きモジュール向け）
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# PCA9685（PWMドライバ）初期化
pwm = PCA9685()
pwm.setPWMFreq(SERVO_FREQ_HZ)

# サーボの初期角度（中央）にセット
sx = SERVO_CENTER_X
sy = SERVO_CENTER_Y
pwm.setRotationAngle(SERVO_CH_X, sx)
pwm.setRotationAngle(SERVO_CH_Y, sy)

try:
    while True:
        # ===== フレーム取得（RGB） =====
        frame_rgb = picam2.capture_array()  # PiCamera2 は RGB で返す

        # 必要に応じて天地反転（カメラの取り付け向きに合わせる）
        # 0: X軸回りで上下反転、1: Y軸回りで左右反転, -1: 180度回転
        frame_rgb = cv2.flip(frame_rgb, 0)
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        # ===== 赤色マスクの作成 =====
        mask = red_mask_rgb(frame_rgb)

        # マスクのライブ表示（デバッグ用）
        cv2.imshow(WINDOW_MASK, mask)

        # ===== ラベリング（連結成分の抽出）=====
        # 返り値:
        # nLabels: ラベル数（背景を含む）
        # labelImg: 各画素のラベルID
        # stats: 各ラベルの外接矩形と面積など [x, y, w, h, area]
        # centroids: 重心座標 [cx, cy]
        nLabels, labelImg, stats, centroids = cv2.connectedComponentsWithStats(mask)

        # 描画用に BGR に変換（表示はBGR前提）
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        # 画面中心（ピクセル）
        x_center = FRAME_SIZE[0] / 2
        y_center = FRAME_SIZE[1] / 2

        if nLabels > 1:
            # 背景(ラベル0)を除いた領域の中で最も面積が大きいものを選択
            areas = stats[1:, cv2.CC_STAT_AREA]
            max_idx = int(np.argmax(areas)) + 1  # +1 で実ラベルに戻す

            # 重心座標
            cx, cy = centroids[max_idx]

            # 外接矩形と面積
            x = int(stats[max_idx, cv2.CC_STAT_LEFT])
            y = int(stats[max_idx, cv2.CC_STAT_TOP])
            w = int(stats[max_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[max_idx, cv2.CC_STAT_HEIGHT])
            area = int(stats[max_idx, cv2.CC_STAT_AREA])

            # 検出結果の描画（見やすさのため）
            cv2.circle(frame_bgr, (int(cx), int(cy)), 10, (0, 255, 0), 2)
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame_bgr, f"area:{area}",
                (x, max(0, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA
            )

            # ===== サーボ制御：重心が中心からどれだけズレているかで角度を微調整 =====
            # X方向（左右）
            if cx > x_center + CENTER_MARGIN_PX:
                sx += SERVO_STEP
            elif cx < x_center - CENTER_MARGIN_PX:
                sx -= SERVO_STEP

            # Y方向（上下）: 画像座標は下に行くほど y が大きくなる点に注意
            if cy > y_center + CENTER_MARGIN_PX:
                sy += SERVO_STEP
            elif cy < y_center - CENTER_MARGIN_PX:
                sy -= SERVO_STEP

            # 角度を物理範囲にクリップ（無理な角度を防止）
            sx = max(SERVO_MIN, min(SERVO_MAX, sx))
            sy = max(SERVO_MIN, min(SERVO_MAX, sy))

            # 実際にサーボを動かす
            pwm.setRotationAngle(SERVO_CH_X, sx)
            pwm.setRotationAngle(SERVO_CH_Y, sy)

        # カメラ画像の表示（BGR）
        cv2.imshow(WINDOW_CAMERA, frame_bgr)

        # ===== キー受付：Esc(27) で終了 =====
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Esc
            break

finally:
    # ===== 後始末：例外があっても必ず通る =====
    pwm.exit_PCA9685()
    picam2.stop()
    cv2.destroyAllWindows()
