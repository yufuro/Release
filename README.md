## 🤖 ロボティクス体験キット / Robotics Experience Kit

<img src="https://github.com/user-attachments/assets/491546c5-e0e8-42da-94b3-e083f5ea7232" width="500">
-----

### 🚀 動作環境 (Platform & OS)

| 項目 | 詳細 |
| :--- | :--- |
| **プラットフォーム** | Raspberry Pi 4/4GB |
| **OS** | Bookworm (64bit) Normalインストールにて実証済み |
| **使用実績** | 2025年11月14日 ロボティクス体験講座にて使用 |

-----

### 🛠️ セットアップ手順 (Setup Instructions)

以下の手順に従って、リポジトリの展開とシステム設定を行ってください。

#### 1\. リポジトリのクローン

`/home/<ユーザー名>`上に **Release** リポジトリをクローンします。

```bash
$ cd
$ git clone https://github.com/yufuro/Release.git
```

#### 2\. システムファイルの初期設定

Raspberry Piのシステムファイルを初期設定します。

```bash
$ sh ./Release/setup/setup_raspi.sh
```

#### 3\. インストールと自動再起動

上記のコマンド実行後、システムが自動で再起動します。再起動後に以下のインストール作業を実行してください。

```bash
$ sh ./Release/setup/setup.sh
```

-----
# ロボティクス体験キット (Powered By fuRo) サンプルコード集

Raspberry Pi、カメラモジュール、サーボモーター、照度センサを使用したロボティクス学習用のPythonサンプルコード集です。
基礎的なカメラ表示から、画像処理による追尾、AIを用いた物体認識まで、段階的に学習することができます。

## 📂 ファイル構成

### 1. カメラ・画像処理（基本編）
PiCamera2とOpenCVを使用した、基本的な映像取得と処理のサンプルです。

| ファイル名 | 概要 | 特徴 |
| :--- | :--- | :--- |
| **`camera_test/cv-camera.py`** | カメラ映像の表示 | 最もシンプルな構成。カメラの上下反転設定などの確認に。 |
| **`face_detect/face_detect.py`** | 顔検出 | Haar Cascadeを使用し、カメラ映像から顔を検出して枠表示します。 |
| **`tracking_test/red_color_tracking.py`** | 色検出（赤色） | 色空間(HSV)変換を利用し、赤色の物体を認識して重心と面積を表示します（モーター制御なし）。 |

### 2. ハードウェア制御・センサーテスト
接続されたハードウェア単体の動作確認用コードです。

| ファイル名 | 概要 | 特徴 |
| :--- | :--- | :--- |
| **`servo_test/servo_test.py`** | サーボ動作テスト | 2軸のサーボモーターをゆっくり往復（スイープ）させます。 |
| **`light_test/lightsensor_cli.py`** | 照度センサテスト | TSL2591センサの値をコンソール（文字）で表示します。 |

### 3. 統合・インタラクティブ（応用編）
画像処理やセンサー値を使って、実際にロボット（サーボ）を制御します。

| ファイル名 | 概要 | 特徴 |
| :--- | :--- | :--- |
| **`servo_tracking/red_color_servo_tracking.py`** | 赤色追尾（簡易版） | 赤い物体が中心に来るようにサーボを制御します。理解しやすいステップ制御版。 |
| **`servo_tracking/pid_red_color_servo_tracking.py`** | 赤色追尾（PID制御） | **PID制御**を用いて、ターゲットになめらかに追従する高性能な追尾プログラムです。 |
| **`light_test/lightsensor_gui.py`** | 照度モニター | 照度センサの値をグラフで可視化します。自動レンジ調整機能付き。 |
| **`Voicevox/lux_interactive.py`** | 照度リアクション | 明るさに応じてサーボが動き、効果音（WAV）を再生するデモです。 |

### 4. AI・物体検出（発展編）
Google MediaPipeを使用した高度な認識サンプルです。

| ファイル名 | 概要 | 特徴 |
| :--- | :--- | :--- |
| **`object_detect/detect_picam.py`** | 物体検出 | 学習済みモデルを使用し、人やコップなど一般的な物体をリアルタイムで検出・識別します。 |

### 5. 音声・発話（Audio & Speech）
VOICEVOX Coreを利用した音声合成と、スピーカー再生に関するコードです。

| ファイル名 | 概要 | 特徴 |
| :--- | :--- | :--- |
| **`Voicevox/checkdev.py`** | デバイス確認 | 使用可能なマイク・スピーカーの一覧を表示します。デバイス番号の特定に使用します。 |
| **`Voicevox/create_voice.py`** | 音声合成 | VOICEVOX Coreを使用し、テキストから音声ファイル(WAV)を生成します。 |
| **`Voicevox/play_voice.py`** | 音声再生 | 生成したWAVファイルを再生します。再生時のノイズ対策（無音挿入）が含まれています。 |

---

## 🛠 動作環境・要件

### ハードウェア
 <img src="https://github.com/user-attachments/assets/910b0de4-1e54-4c81-b76c-4a0fc24df4d1" width="400">

* Raspberry Pi (Pi 4/ Pi 5 推奨)
* Camera Module 3 (PiCamera2 対応)
* PCA9685 PWM Driver (I2C接続)
* TSL2591 Light Sensor (I2C接続)
* Servo Motors x2 (Pan/Tilt)
* Speaker / Headphones (3.5mm jack or USB/HDMI)

## 🚀 実行方法

ターミナルで各ファイルを指定して実行してください。
（終了するには、カメラウィンドウがアクティブな状態で `Esc` キーを押すか、ターミナルで `Ctrl+C` を押します）

```bash
source ~/venv/bin/activate

# 例: 顔検出を実行する場合
python3 face_detect.py

# 例: PID制御で赤色追尾をする場合
python3 pid_red_color_servo_tracking.py
