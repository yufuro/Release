"""
PiCamera2 + OpenCV で「赤色領域を検出→最大領域を表示する」最小サンプル
初心者向けコメント付き／RGB-BGRの混乱を解消

ポイント
- PiCamera2 は RGB でフレームを返す → 画像処理は RGB のまま実施
- OpenCV の imshow は BGR 前提 → 表示直前だけ RGB→BGR 変換
- connectedComponentsWithStats で最大面積のラベルを選び、矩形・重心を描く
"""

import numpy as np
import cv2
from picamera2 import Picamera2
from libcamera import controls

# ===== 画面サイズや表示名などの定数 =====
FRAME_SIZE = (640, 480)               # フレームサイズ (幅, 高さ)
WINDOW_MASK = 'Mask_Live'             # マスク表示ウィンドウ名
WINDOW_CAMERA = 'RaspiCam_Live'       # カメラ表示ウィンドウ名

def red_mask_rgb(img_rgb: np.ndarray) -> np.ndarray:
    """
    入力: RGB画像 (H, W, 3), dtype=uint8
    出力: 赤色領域の2値マスク (0 or 255, dtype=uint8)

    手順:
    1) ガウシアンぼかしでノイズ軽減
    2) RGB -> HSV 変換  ※OpenCVのHは0~179
    3) 赤は 0 近傍 と 179 近傍の2レンジを inRange で抽出し OR 結合
    4) 形態学的処理（開→閉）で小ノイズ除去＆穴埋め
    """
    # 1) ノイズ軽減
    blur = cv2.GaussianBlur(img_rgb, (5, 5), 0)

    # 2) 色空間変換（RGB→HSV）
    hsv = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)

    # 3) 赤の2レンジを抽出
    lower1 = np.array([0,   120, 70],  dtype=np.uint8)
    upper1 = np.array([10,  255, 255], dtype=np.uint8)
    lower2 = np.array([170, 120, 70],  dtype=np.uint8)
    upper2 = np.array([179, 255, 255], dtype=np.uint8)

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    # 4) 小ノイズ除去＆穴埋め（開→閉）
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask


# ===== カメラ初期化 =====
picam2 = Picamera2()
# 取得するフレームは RGB888（=RGBの8bit×3ch）で 640x480
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": FRAME_SIZE}
))
picam2.start()

# レンズ付きモジュールの場合に有効：AFを連続モードに
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

try:
    while True:
        # ---- フレーム取得（PiCamera2はRGBで返す） ----
        frame_rgb = picam2.capture_array()

        # 取り付け向きにより上下/左右が逆なら flip で補正
        # 引数: 0=上下反転, 1=左右反転, -1=上下左右反転
        frame_rgb = cv2.flip(frame_rgb, 0)  
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        
        # ---- 赤マスク作成（処理はRGBで統一）----
        mask = red_mask_rgb(frame_rgb)

        # ---- マスクを表示（デバッグ用）----
        cv2.imshow(WINDOW_MASK, mask)

        # ---- ラベリング（連結成分）----
        # nLabels: ラベル数（背景を含む）
        # stats:   各ラベルの [x, y, w, h, area]
        # centroids: 各ラベルの重心 (cx, cy)
        nLabels, labelImg, stats, centroids = cv2.connectedComponentsWithStats(mask)

        # 表示用に BGR へ変換（imshowはBGR前提）
        disp_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        if nLabels > 1:
            # 背景(0)以外の面積を取り出し、最大のラベルを選ぶ
            areas = stats[1:, cv2.CC_STAT_AREA]
            max_idx = int(np.argmax(areas)) + 1  # +1で実ラベル番号に戻す

            # 最大ラベルの重心と外接矩形
            cx, cy = centroids[max_idx]
            x = int(stats[max_idx, cv2.CC_STAT_LEFT])
            y = int(stats[max_idx, cv2.CC_STAT_TOP])
            w = int(stats[max_idx, cv2.CC_STAT_WIDTH])
            h = int(stats[max_idx, cv2.CC_STAT_HEIGHT])
            area = int(stats[max_idx, cv2.CC_STAT_AREA])

            # 可視化（重心マーク、矩形、面積テキスト）
            cv2.circle(disp_bgr, (int(cx), int(cy)), 10, (0, 255, 0), 2)
            cv2.rectangle(disp_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(disp_bgr, f"area:{area}",
                        (x, max(0, y - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 1, cv2.LINE_AA)

        # ---- カメラ画像を表示（BGR）----
        cv2.imshow(WINDOW_CAMERA, disp_bgr)

        # ---- Escキー(27)で終了 ----
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

finally:
    # 例外が起きても確実に後始末
    picam2.stop()
    cv2.destroyAllWindows()
