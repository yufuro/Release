"""
PiCamera2 + OpenCV でカメラ映像をリアルタイム表示するサンプル
（初心者向けコメント付き）

ポイント:
- Picamera2 のプレビュー設定を使って画像を取得
- OpenCV (cv2) の imshow() で表示
- ESCキーで終了
"""

import cv2
from picamera2 import Picamera2
from libcamera import controls

# ===== カメラの初期化 =====
picam2 = Picamera2()

# カメラ設定:
# main={"format": 'XRGB8888', "size": (640, 480)}
# → XRGB8888 は 4ch (透明度含む) のRGB形式
# → 640x480 は標準的なVGAサイズ（軽くて速い）
config = picam2.create_preview_configuration(
    main={"format": 'XRGB8888', "size": (640, 480)}
)
picam2.configure(config)

# カメラ起動
picam2.start()

# オートフォーカスを連続モードに設定（レンズ付きモジュールのみ有効）
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})


try:
    while True:
        # ==== フレームを取得 ====
        im = picam2.capture_array()  # 現在のカメラ映像を取得 (RGB配列)
        im = cv2.flip(im, 0)         # 上下反転（取り付け向きに合わせて）
        # im = cv2.flip(im, 1)       # 左右反転したい場合はこちら

        # ==== ウィンドウに表示 ====
        cv2.imshow("Camera", im)

        # ==== キー入力をチェック ====
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESCキー
            break

finally:
    # ==== 後始末（安全に停止） ====
    picam2.stop()
    cv2.destroyAllWindows()
 