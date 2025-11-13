# Copyright 2023 The MediaPipe Authors.
# Licensed under the Apache License, Version 2.0

import argparse
import sys
import time
import cv2
import mediapipe as mp
from picamera2 import Picamera2
from libcamera import controls
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils import visualize  # MediaPipe サンプル付属の可視化関数

# ===== カメラ初期化（プレビュー用途の軽量設定） =====
# XRGB8888 は 4ch（BGRA相当：使わないAが先頭/末尾に乗る）で返る点に注意
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "XRGB8888", "size": (640, 480)}
    )
)
picam2.start()
# レンズ付きモジュールなら AF を連続モードに
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# ===== FPS 計測用のグローバル（可視化のため） =====
COUNTER, FPS = 0, 0.0
START_TIME = time.time()


def run(model: str, max_results: int, score_threshold: float,
        width: int, height: int) -> None:
    """
    MediaPipe ObjectDetector を LIVE_STREAM（非同期）で動かし、
    Picamera2 からの映像に検出結果をオーバレイ表示する。
    """
    # ---- 非同期推論制御用のフラグ／最新結果 ----
    #   is_inference_in_flight=True の間は新規フレームを投げない（詰まり防止）
    global is_inference_in_flight
    global latest_detection_result
    is_inference_in_flight = False
    latest_detection_result = None

    # ---- FPS の移動平均間隔（何フレーム毎に平均を取り直すか）----
    fps_avg_frame_count = 10

    def save_result(result: vision.ObjectDetectorResult,
                    unused_output_image: mp.Image,
                    timestamp_ms: int):
        """
        非同期推論のコールバック：
        - 推論完了を通知
        - FPS を更新
        - 最新の検出結果を保持
        """
        nonlocal fps_avg_frame_count
        global is_inference_in_flight, latest_detection_result, COUNTER, START_TIME, FPS

        # 次のフレームを投げられるようにする
        is_inference_in_flight = False

        # FPS更新（fps_avg_frame_count フレームごとに再計算）
        if COUNTER % fps_avg_frame_count == 0:
            now = time.time()
            elapsed = max(now - START_TIME, 1e-6)
            FPS = fps_avg_frame_count / elapsed
            START_TIME = now

        latest_detection_result = result
        COUNTER += 1

    # ---- ObjectDetector の作成（LIVE_STREAM + コールバック）----
    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ObjectDetectorOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        max_results=max_results,
        score_threshold=score_threshold,
        result_callback=save_result,
    )
    detector = vision.ObjectDetector.create_from_options(options)

    # ---- 表示用ウィンドウ（大きめに可変）----
    cv2.namedWindow("object_detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("object_detection", 800, 600)

    # 画面表示のための描画パラメータ
    row_size = 50        # FPSテキストのY位置（ピクセル）
    left_margin = 24     # FPSテキストのX位置（ピクセル）
    text_color = (0, 0, 0)  # 黒（BGR）
    font_size = 1
    font_thickness = 1

    try:
        while True:
            # ====== フレーム取得 ======
            # XRGB8888（4ch）で来る点に注意（BGRA相当）
            frame = picam2.capture_array()
            frame = cv2.flip(frame, 0)  # 取り付け向きに応じて上下反転

            if frame is None:
                break

            # ====== MediaPipe 用の入力画像を作る ======
            # 1) 表示サイズとは別に、推論用に width×height へリサイズ
            # 2) 4ch(BGRA) → RGB へ変換（XRGB8888 はアルファ(未使用)付き）
            image = cv2.resize(frame, (width, height))
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

            # ====== 非同期推論の投入制御 ======
            if not is_inference_in_flight:
                # MediaPipe はタイムスタンプ(ms)の単調増加を要求
                detector.detect_async(mp_image, time.time_ns() // 1_000_000)
                is_inference_in_flight = True
            # else: 推論中は何もしない（バックログの肥大化を防止）

            # ====== FPS表示（OpenCV の BGR 上に描画するので元の image を使用）======
            # ※ここでの image は BGRA→RGB に変換する前の OpenCV 用画像
            #   ただし text_color は BGR 前提。RGB配列に描いても色の意味が入れ替わる点に注意。
            #   見た目の色を厳密に合わせたい場合は BGR 画像に描く/最後に変換する流れに統一してください。
            fps_text = f"FPS = {FPS:.1f}"
            cv2.putText(image, fps_text, (left_margin, row_size),
                        cv2.FONT_HERSHEY_DUPLEX, font_size, text_color,
                        font_thickness, cv2.LINE_AA)

            # ====== 検出結果の可視化 ======
            # MediaPipe の visualize は RGB/BGR どちらでも動くが、
            # その後の imshow での色を気にするなら配列の色順を統一しておくと混乱しない。
            if latest_detection_result is not None:
                image = visualize(image, latest_detection_result)

            # ====== 画面に表示 ======
            cv2.imshow("object_detection", image)

            # ====== ESCで終了 ======
            if cv2.waitKey(1) == 27:
                break

    finally:
        # 必ずリソースを解放
        detector.close()
        picam2.stop()
        cv2.destroyAllWindows()


def main():
    # コマンドライン引数（デフォルトは軽量モデル＆中程度信頼度）
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--model", help="Path of the object detection model.",
                        required=False, default="efficientdet.tflite")
    parser.add_argument("--maxResults", help="Max number of detection results.",
                        required=False, type=int, default=5)
    parser.add_argument("--scoreThreshold",
                        help="The score threshold of detection results.",
                        required=False, type=float, default=0.25)
    parser.add_argument("--cameraId", help="Id of camera.",
                        required=False, type=int, default=0)
    parser.add_argument("--frameWidth",
                        help="Width of frame to capture from camera.",
                        required=False, type=int, default=1280)
    parser.add_argument("--frameHeight",
                        help="Height of frame to capture from camera.",
                        required=False, type=int, default=720)
    args = parser.parse_args()

    run(args.model, args.maxResults, args.scoreThreshold,
        args.frameWidth, args.frameHeight)


if __name__ == "__main__":
    main()
