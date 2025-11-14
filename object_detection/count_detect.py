# Copyright 2023 The MediaPipe Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import sys
import time
import cv2
import mediapipe as mp
from picamera2 import Picamera2
from libcamera import controls
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils import visualize

# 任意の物体名を指定する変数（ここで変更可能）
target_object = "person"  # ここを好きな物体名に変更できる

# カメラの初期設定
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

# FPS計算用のグローバル変数
COUNTER, FPS = 0, 0
START_TIME = time.time()
is_inference_in_flight = False
latest_detection_result = None
fps_avg_frame_count = 10

def save_result(result: vision.ObjectDetectorResult,
                unused_output_image: mp.Image,
                timestamp_ms: int):
    """検出が完了したときに呼び出されるコールバック関数"""
    global is_inference_in_flight, latest_detection_result, COUNTER, START_TIME, FPS

    # 推論が終了したことをマークし、新しいフレームを送信できるようにする
    is_inference_in_flight = False

    # 検出結果から指定した物体の数をカウントする
    object_count = sum(1 for detection in result.detections if detection.categories[0].category_name == target_object)
    
    # 検出された物体の数をコンソールに出力
    print(f"検出された {target_object} の数: {object_count}")

    # FPSを更新
    if COUNTER % fps_avg_frame_count == 0:
        current_time = time.time()
        FPS = fps_avg_frame_count / (current_time - START_TIME)
        START_TIME = current_time

    latest_detection_result = result
    COUNTER += 1

    # 画像上に検出された物体の数を描画
    object_text = f'{target_object.capitalize()}: {object_count}'
    image_copy = unused_output_image.numpy_view().copy()  # 書き込み可能なコピーを作成
    cv2.putText(image_copy, object_text, (24, 100),
                cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)

def run(model: str, max_results: int, score_threshold: float,
        width: int, height: int) -> None:
    global is_inference_in_flight

    # オブジェクト検出モデルを初期化
    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ObjectDetectorOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        max_results=max_results,
        score_threshold=score_threshold,
        result_callback=save_result
    )
    detector = vision.ObjectDetector.create_from_options(options)

    # 表示に関するパラメータ
    row_size = 50  # ピクセル
    left_margin = 24  # ピクセル
    text_color = (0, 0, 0)  # 黒
    font_size = 1
    font_thickness = 1

    # 検出結果を表示するウィンドウを作成
    cv2.namedWindow('object_detection', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('object_detection', 800, 600)

    while True:
        frame = picam2.capture_array()
        frame = cv2.flip(frame,-1)
        if frame is None:
            break

        # フレームをリサイズし、推論用に変換
        image = cv2.resize(frame, (width, height))
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # 前回の推論が終了していれば、新しい推論を開始
        if not is_inference_in_flight:
            detector.detect_async(mp_image, time.time_ns() // 1_000_000)
            is_inference_in_flight = True

        # FPSを画像上に描画
        fps_text = 'FPS = {:.1f}'.format(FPS)
        text_location = (left_margin, row_size)
        cv2.putText(image, fps_text, text_location, cv2.FONT_HERSHEY_DUPLEX,
                    font_size, text_color, font_thickness, cv2.LINE_AA)

        # 最新の検出結果が存在する場合は画像に描画
        if latest_detection_result is not None:
            image = visualize(image, latest_detection_result)

            # 画像上に検出された物体の数を描画
            object_count = sum(1 for detection in latest_detection_result.detections if detection.categories[0].category_name == target_object)
            object_text = f'{target_object.capitalize()}: {object_count}'
            cv2.putText(image, object_text, (24, 100), cv2.FONT_HERSHEY_DUPLEX,
                        font_size, text_color, font_thickness, cv2.LINE_AA)

        cv2.imshow('object_detection', image)

        # ESCキーが押されたら終了
        if cv2.waitKey(1) == 27:
            break

    detector.close()
    picam2.stop()
    cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', help='オブジェクト検出モデルのパス',
                        required=False, default='efficientdet.tflite')
    parser.add_argument('--maxResults', help='検出結果の最大数',
                        required=False, default=5)
    parser.add_argument('--scoreThreshold',
                        help='検出結果のスコア閾値',
                        required=False, type=float, default=0.25)
    parser.add_argument('--cameraId', help='カメラID',
                        required=False, type=int, default=0)
    parser.add_argument('--frameWidth',
                        help='カメラからキャプチャするフレームの幅',
                        required=False, type=int, default=1280)
    parser.add_argument('--frameHeight',
                        help='カメラからキャプチャするフレームの高さ',
                        required=False, type=int, default=720)
    args = parser.parse_args()

    run(args.model, int(args.maxResults), args.scoreThreshold,
        args.frameWidth, args.frameHeight)

if __name__ == '__main__':
    main()

