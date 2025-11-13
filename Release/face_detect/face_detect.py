"""
PiCamera2 + OpenCV 顔検出サンプル（初心者向けコメント付き）

概要:
- Haar Cascade を使ってカメラ映像から顔を検出する。
- 検出された顔を矩形で囲んで表示。
- ESCキーで終了。
"""

import cv2
from picamera2 import Picamera2
from libcamera import controls

# ===== 顔検出器の設定 =====
# OpenCV の Haar Cascade（顔検出モデル）のパスを指定
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

# 分類器を読み込み
face_detector = cv2.CascadeClassifier(CASCADE_PATH)

# ロード確認
if face_detector.empty():
    print("顔検出器の読み込みに失敗しました。パスを確認してください。")
else:
    print("顔検出器を読み込みました。")

# ===== OpenCV のウィンドウ初期化 =====
cv2.startWindowThread()

# ===== カメラ初期化 =====
picam2 = Picamera2()

# 640x480, XRGB8888 形式でプレビュー設定
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": 'XRGB8888', "size": (640, 480)}
    )
)

picam2.start()

# オートフォーカスを連続モードに（レンズ付きモジュールの場合）
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

print("カメラ起動中。ESCキーで終了します。")

try:
    while True:
        # ---- カメラ画像を取得 ----
        im = picam2.capture_array()  # RGB (XRGB8888形式)
        im = cv2.flip(im, 0)         # 上下反転（取り付け方向により必要）

        # ---- 顔検出のためにグレースケール変換 ----
        grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        # ---- 顔検出 ----
        # detectMultiScale(image, scaleFactor, minNeighbors)
        # scaleFactor : 画像を縮小しながら探索する倍率（1.1で10%ずつ）
        # minNeighbors: 何回検出されたら顔とみなすか（値が大きいほど厳密）
        faces = face_detector.detectMultiScale(grey, scaleFactor=1.1, minNeighbors=10)

        # ---- 検出結果の描画 ----
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(im, "Face", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # ---- 表示 ----
        cv2.imshow("Camera", im)

        # ---- 終了キー判定 ----
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESCキー
            print("終了指令を受けました。停止します。")
            break

finally:
    # ===== 終了処理 =====
    picam2.stop()
    cv2.destroyAllWindows()
    print("カメラを停止し、ウィンドウを閉じました。")
