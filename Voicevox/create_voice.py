from pathlib import Path
from voicevox_core import VoicevoxCore
import sys
import os


def synthesize_voice(
    text: str,
    filename: str = "output1",
    speaker_id: int = 1,
    dict_dir: str = "./open_jtalk_dic_utf_8-1.11"
):
    """VOICEVOX Core を使って音声を合成し、WAVファイルとして保存する。

    Args:
        text (str): 読み上げるテキスト
        filename (str): 出力するファイル名（拡張子は自動で .wav）
        speaker_id (int): 話者 ID（例: 1=ずんだもん、2=四国めたん）
        dict_dir (str): OpenJTalk 辞書ディレクトリ
    """

    dict_path = Path(dict_dir)
    if not dict_path.exists():
        raise FileNotFoundError(f"OpenJTalk 辞書が見つかりません: {dict_path}")

    core = VoicevoxCore(open_jtalk_dict_dir=dict_path)

    # モデル未ロードならロード
    if not core.is_model_loaded(speaker_id):
        core.load_model(speaker_id)

    # 音声合成
    wave_bytes = core.tts(text, speaker_id)

    # 保存
    out_path = f"./{filename}.wav"
    with open(out_path, "wb") as f:
        f.write(wave_bytes)

    print(f"合成完了: {out_path}")


if __name__ == "__main__":
    synthesize_voice(
        text="まぶしいのだ",
        filename="output1",
        speaker_id=1,
    )
