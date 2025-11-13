"""
Raspberry Pi + PiCamera2 + OpenCV + PCA9685 (2軸サーボ)
赤色物体を PID 制御でなめらかに追尾するサンプル（初心者向けコメント付き）

考え方
- 画面中心と赤物体の重心の差（px）= 誤差 e を計算
- PID（比例・積分・微分）で「1フレームあたりの角度変化 Δθ」を求める
- 現在角度に Δθ を足して更新（角度は物理範囲内にクリップ）
- 積分は風上制御（アンチワインドアップ）付き、微分は簡易フィルタ付き
"""

import time
import numpy as np
import cv2
from picamera2 import Picamera2
from libcamera import controls
from PCA9685 import PCA9685

# ====== 基本設定 ======
FRAME_SIZE = (640, 480)      # 取得フレーム (W, H)
WINDOW_MASK = 'Mask_Live'
WINDOW_CAMERA = 'RaspiCam_Live'

# サーボ設定
SERVO_FREQ_HZ = 50
SERVO_CH_X = 0                # 左右
SERVO_CH_Y = 1                # 上下
SERVO_MIN = 30
SERVO_MAX = 150
SERVO_CENTER_X = 90
SERVO_CENTER_Y = 90

# 画像処理（赤色抽出）用パラメータ
GAUSS_KERNEL = (5, 5)
MORPH_KERNEL = (3, 3)
HSV_RED_RANGE_1 = (np.array([0,   120, 70],  dtype=np.uint8),
                   np.array([10,  255, 255], dtype=np.uint8))
HSV_RED_RANGE_2 = (np.array([170, 120, 70],  dtype=np.uint8),
                   np.array([179, 255, 255], dtype=np.uint8))

# 追尾安定化
CENTER_DEADBAND_PX = 12       # 中心まわりのデッドバンド（この範囲内の誤差は0扱い）
MAX_DEG_PER_FRAME = 6.0       # 1フレームに追加できる角度の上限（暴れ防止）
SIGN_X = 1   # X方向の追従向き。逆なら -1、合っていれば +1
SIGN_Y = 1   # Y方向の追従向き。逆なら -1、合っていれば +1

# ====== PID コントローラ ======
class PIDController:
    """
    単純な離散PID（アンチワインドアップ＆微分フィルタつき）
    入力: 誤差 e (px)
    出力: 角度変化 Δθ (deg)
    """
    def __init__(self, kp, ki, kd,
                 out_min=-MAX_DEG_PER_FRAME, out_max=MAX_DEG_PER_FRAME,
                 i_min=-20.0, i_max=20.0,
                 d_alpha=0.2  # 0<α<=1（小さいほどなめらか）
                 ):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.out_min = out_min
        self.out_max = out_max
        self.i_min = i_min
        self.i_max = i_max

        self.integral = 0.0
        self.prev_meas = None     # Dを「測定値の変化」にかける（D on measurement）
        self.d_alpha = d_alpha
        self.d_filt = 0.0

    def reset(self):
        self.integral = 0.0
        self.prev_meas = None
        self.d_filt = 0.0

    def update(self, error, meas, dt):
        """
        error: 目標-実測（ここでは cx,cy と中心の差を「実測→目標0」に合わせて定義）
        meas : 実測値（ここでは重心座標の x または y ）…D on measurement用
        dt   : 経過秒（最小0.001で保護）
        """
        dt = max(dt, 1e-3)

        # P
        p = self.kp * error

        # I（アンチワインドアップ：積分の上下限をクリップ）
        self.integral += error * dt
        self.integral = max(self.i_min, min(self.i_max, self.integral))
        i = self.ki * self.integral

        # D（測定値の変化で微分 → 外乱やノイズに強め）
        d_raw = 0.0
        if self.prev_meas is not None:
            d_raw = -(meas - self.prev_meas) / dt  # error微分 ≒ -meas微分
        self.prev_meas = meas

        # 簡易一次フィルタ（ローパス）で微分値をなめらかに
        self.d_filt = (1.0 - self.d_alpha) * self.d_filt + self.d_alpha * d_raw
        d = self.kd * self.d_filt

        # 出力（角度変化）をクリップ
        u = p + i + d
        u = max(self.out_min, min(self.out_max, u))
        return u


# ====== 赤色マスク作成（入力はRGB） ======
def red_mask_rgb(img_rgb: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(img_rgb, GAUSS_KERNEL, 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    (l1, u1) = HSV_RED_RANGE_1
    (l2, u2) = HSV_RED_RANGE_2
    m1 = cv2.inRange(hsv, l1, u1)
    m2 = cv2.inRange(hsv, l2, u2)
    mask = cv2.bitwise_or(m1, m2)

    kernel = np.ones(MORPH_KERNEL, np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask


# ====== カメラ & サーボ初期化 ======
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": FRAME_SIZE}
))
picam2.start()
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

pwm = PCA9685()
pwm.setPWMFreq(SERVO_FREQ_HZ)

sx = SERVO_CENTER_X
sy = SERVO_CENTER_Y
pwm.setRotationAngle(SERVO_CH_X, sx)
pwm.setRotationAngle(SERVO_CH_Y, sy)

# ====== PID ゲイン（最初はPとDだけでOK） ======
# 画面誤差(px) → 角度変化(°)に換算する係数として機能します。
# 例：誤差100pxで 2° くらい動くイメージなら kp ≈ 0.02
pid_x = PIDController(kp=0.035, ki=0.000, kd=0.001,
                      out_min=-MAX_DEG_PER_FRAME, out_max=MAX_DEG_PER_FRAME,
                      i_min=-15.0, i_max=15.0, d_alpha=0.25)
pid_y = PIDController(kp=0.035, ki=0.000, kd=0.001,
                      out_min=-MAX_DEG_PER_FRAME, out_max=MAX_DEG_PER_FRAME,
                      i_min=-15.0, i_max=15.0, d_alpha=0.25)

# 時間計測
t_prev = time.perf_counter()

try:
    while True:
        # === フレーム取得（RGB） ===
        frame_rgb = picam2.capture_array()
        frame_rgb = cv2.flip(frame_rgb, 0)  # 取り付け向きに合わせて

        # === 赤マスク & ラベリング ===
        mask = red_mask_rgb(frame_rgb)
        nLabels, labelImg, stats, centroids = cv2.connectedComponentsWithStats(mask)

        # 表示用に変換（OpenCVのimshowはBGR）
        frame_bgr = frame_rgb
#        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        cv2.imshow(WINDOW_MASK, mask)

        # 画面中心
        x_center = FRAME_SIZE[0] / 2.0
        y_center = FRAME_SIZE[1] / 2.0

        # 経過時間
        t_now = time.perf_counter()
        dt = t_now - t_prev
        t_prev = t_now

        if nLabels > 1:
            # 背景を除いて最大面積のラベルを選択
            areas = stats[1:, cv2.CC_STAT_AREA]
            max_idx = int(np.argmax(areas)) + 1
            cx, cy = centroids[max_idx]

            # 可視化（バウンディングボックスなど）
            x = int(stats[max_idx, cv2.CC_STAT_LEFT])
            y = int(stats[max_idx, cv2.CC_STAT_TOP])
            w = int(stats[max_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[max_idx, cv2.CC_STAT_HEIGHT])
            area = int(stats[max_idx, cv2.CC_STAT_AREA])
            cv2.circle(frame_bgr, (int(cx), int(cy)), 10, (0, 255, 0), 2)
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame_bgr, f"area:{area}",
                        (x, max(0, y - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

            # 誤差定義の部分をこのまま維持し（右と下が + になる定義）…
            err_x = (cx - x_center)
            err_y = (cy - y_center)

            # …PIDの出力を適用するときに向きを乗じる
            dtheta_x = SIGN_X * pid_x.update(error=err_x, meas=cx, dt=dt)
            dtheta_y = SIGN_Y * pid_y.update(error=err_y, meas=cy, dt=dt)

            sx = float(np.clip(sx + dtheta_x, SERVO_MIN, SERVO_MAX))
            sy = float(np.clip(sy + dtheta_y, SERVO_MIN, SERVO_MAX))


            # 実機に反映
            pwm.setRotationAngle(SERVO_CH_X, sx)
            pwm.setRotationAngle(SERVO_CH_Y, sy)

        cv2.imshow(WINDOW_CAMERA, frame_bgr)

        # Escで終了
        if (cv2.waitKey(1) & 0xFF) == 27:
            break

finally:
    # 後始末（例外があっても必ず通る）
    pwm.exit_PCA9685()
    picam2.stop()
    cv2.destroyAllWindows()
