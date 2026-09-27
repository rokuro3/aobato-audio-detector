#!/usr/bin/env python3
"""BirdNET+ V3.0で音声中のアオバト検出確率を推論するStreamlitアプリ。"""
import csv
import io
from pathlib import Path
from typing import Callable, Iterator

import librosa
import numpy as np
import onnxruntime as ort
import streamlit as st

TARGET_SR = 32000
CHUNK_SECONDS = 3.0
CHUNK_SAMPLES = int(TARGET_SR * CHUNK_SECONDS)
TARGET_SCIENTIFIC_NAME = "Treron sieboldii"
MODEL_FILENAME = "BirdNET+_V3.0-preview3.1_Global_11K_FP16_pruned.onnx"
LABELS_FILENAME = "BirdNET+_V3.0-preview3.1_Global_11K_Labels.csv"
APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = APP_DIR / "assets"
DEFAULT_MODEL_PATH = ASSET_DIR / MODEL_FILENAME
DEFAULT_LABELS_PATH = ASSET_DIR / LABELS_FILENAME


def find_target_index(labels_path: Path) -> tuple[int, str]:
    with labels_path.open("r", newline="", encoding="utf-8") as labels_file:
        for output_index, row in enumerate(csv.DictReader(labels_file, delimiter=";")):
            if row.get("sci_name", "").strip().casefold() == TARGET_SCIENTIFIC_NAME.casefold():
                common_name = row.get("com_name", "").strip()
                return output_index, common_name
    raise ValueError(f"ラベルCSVに{TARGET_SCIENTIFIC_NAME}がありません。")


@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> ort.InferenceSession:
    return ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])


@st.cache_data(show_spinner=False)
def load_labels_info(labels_path: str) -> tuple[int, str, int]:
    target_index, common_name = find_target_index(Path(labels_path))
    with Path(labels_path).open("r", encoding="utf-8") as labels_file:
        label_count = sum(1 for _ in csv.DictReader(labels_file, delimiter=";"))
    return target_index, common_name, label_count


def iter_chunks(audio: np.ndarray, overlap_seconds: float) -> Iterator[tuple[float, np.ndarray]]:
    step = int((CHUNK_SECONDS - overlap_seconds) * TARGET_SR)
    if step <= 0:
        raise ValueError("重なりは3秒未満にしてください。")
    if audio.size == 0:
        return
    for start in range(0, len(audio), step):
        chunk = audio[start:start + CHUNK_SAMPLES]
        actual_length = len(chunk)
        if actual_length < CHUNK_SAMPLES:
            chunk = np.pad(chunk, (0, CHUNK_SAMPLES - actual_length))
        yield start / TARGET_SR, chunk.astype(np.float32, copy=False)
        if start + CHUNK_SAMPLES >= len(audio):
            break


def predict_aobato_probability(
    session: ort.InferenceSession,
    audio: np.ndarray,
    overlap_seconds: float,
    batch_size: int,
    target_index: int,
    label_count: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, float]]:
    chunks = list(iter_chunks(audio, overlap_seconds))
    if not chunks:
        return []
    input_name = session.get_inputs()[0].name
    input_type = np.float16 if "float16" in session.get_inputs()[0].type else np.float32
    rows: list[dict[str, float]] = []
    for offset in range(0, len(chunks), batch_size):
        batch = chunks[offset:offset + batch_size]
        waveforms = np.stack([chunk for _, chunk in batch]).astype(input_type)
        output = session.run(None, {input_name: waveforms})[0]
        if output.ndim != 2 or output.shape[1] != label_count:
            raise ValueError(
                f"モデル出力({output.shape})とラベル数({label_count})が一致しません。"
            )
        for (start, chunk), probabilities in zip(batch, output):
            rows.append(
                {
                    "start_sec": start,
                    "end_sec": min(start + CHUNK_SECONDS, len(audio) / TARGET_SR),
                    "probability": float(probabilities[target_index]),
                }
            )
        if on_progress is not None:
            on_progress(min(offset + batch_size, len(chunks)), len(chunks))
    return rows


def format_hms(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{secs:06.3f}"


def make_csv(rows: list[dict[str, float]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["start_sec", "end_sec", "start_hms", "end_hms", "aobato_probability"]
    )
    for row in rows:
        writer.writerow([
            f"{row['start_sec']:.3f}",
            f"{row['end_sec']:.3f}",
            format_hms(row["start_sec"]),
            format_hms(row["end_sec"]),
            f"{row['probability']:.6f}",
        ])
    return output.getvalue()


def make_audacity_labels(rows: list[dict[str, float]]) -> str:
    """Audacityのラベルトラック用タブ区切り形式（開始\t終了\tラベル）。"""
    lines = [
        f"{row['start_sec']:.3f}\t{row['end_sec']:.3f}\taobato {row['probability']:.4f}"
        for row in rows
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> None:
    st.set_page_config(page_title="アオバト音声検出AI", layout="wide")
    st.title("アオバト音声検出AI")
    st.caption("BirdNET+ V3.0で音声を3秒ごとに推論し、アオバトの検出確率を表示します。")

    with st.sidebar:
        st.header("設定")
        threshold = st.slider("出力する下限", 0.0, 1.0, 0.15, 0.01)
        batch_size = st.number_input(
            "一度に推論する音声区間数",
            min_value=1,
            max_value=128,
            value=16,
            step=1,
            help="大きいほど処理が速くなる場合がありますが、メモリを多く使います。",
        )
        st.divider()
        st.caption(
            "使用モデル: BirdNET+ V3.0 Developer Preview 3.1\n\n"
            "ライセンス: [CC BY-SA 4.0]"
            "(https://creativecommons.org/licenses/by-sa/4.0/)"
        )

    uploaded = st.file_uploader("音声ファイル", type=["wav", "mp3", "flac", "ogg", "m4a"])
    if uploaded is None:
        st.info("音声ファイルを選択してください。")
        return

    try:
        with st.spinner("モデルとラベルを読み込んでいます..."):
            target_index, common_name, label_count = load_labels_info(str(DEFAULT_LABELS_PATH))
            session = load_model(str(DEFAULT_MODEL_PATH))
        audio, _ = librosa.load(io.BytesIO(uploaded.getvalue()), sr=TARGET_SR, mono=True)
        st.audio(uploaded.getvalue(), format=uploaded.type or "audio/wav")
        st.caption(f"対象ラベル: {TARGET_SCIENTIFIC_NAME} ({common_name}) | 長さ: {len(audio) / TARGET_SR:.1f}秒")
        progress_bar = st.progress(0.0, text="推論中... 0%")

        def update_progress(done: int, total: int) -> None:
            fraction = done / total if total else 1.0
            progress_bar.progress(fraction, text=f"推論中... {done}/{total} 区間 ({fraction:.0%})")

        rows = predict_aobato_probability(
            session, audio, 0.0, int(batch_size), target_index, label_count, update_progress
        )
        progress_bar.empty()
    except Exception as error:
        st.error(f"推論に失敗しました: {error}")
        return

    visible_rows = [row for row in rows if row["probability"] >= threshold]
    st.metric("対象チャンク数", f"{len(visible_rows)} / {len(rows)}")
    if visible_rows:
        st.dataframe(
            [
                {
                    "開始": format_hms(row["start_sec"]),
                    "終了": format_hms(row["end_sec"]),
                    "アオバト確率": f"{row['probability']:.4f}",
                }
                for row in visible_rows
            ],
            width="stretch",
        )
    else:
        st.info("下限以上のチャンクはありません。")
    st.download_button(
        "確率CSVをダウンロード",
        data=make_csv(visible_rows).encode("utf-8"),
        file_name=f"{Path(uploaded.name).stem}_aobato_probability.csv",
        mime="text/csv",
        icon=":material/download:",
        width="content",
    )
    st.download_button(
        "Audacityラベルをダウンロード",
        data=make_audacity_labels(visible_rows).encode("utf-8"),
        file_name=f"{Path(uploaded.name).stem}_aobato_labels.txt",
        mime="text/plain",
        icon=":material/download:",
        width="content",
    )

    st.divider()
    with st.expander("モデルのライセンス・出典表示"):
        st.markdown(
            "- モデル: **BirdNET+ V3.0 Developer Preview 3.1 - 11K Species**\n"
            "- 作成: Lasseck, M., Eibl, M., Klinck, H., & Kahl, S.\n"
            "- ライセンス: [Creative Commons Attribution-ShareAlike 4.0 "
            "International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)\n"
            "- 入手元: [Zenodo (DOI: 10.5281/zenodo.20703646)]"
            "(https://doi.org/10.5281/zenodo.20703646)\n"
            "- 利用規約: [TERMS_OF_USE]"
            "(https://github.com/birdnet-team/birdnet-V3.0-dev/blob/main/TERMS_OF_USE.md)"
            "をご確認ください。\n\n"
            "**引用:** Lasseck, M., Eibl, M., Klinck, H., & Kahl, S. (2026). "
            "BirdNET+ V3.0 model developer preview (Preview 3.1). Zenodo. "
            "https://doi.org/10.5281/zenodo.20703646\n\n"
            "CC BY-SA の継承条件により、本モデルの出力を利用した二次利用物も同一ライセンスでの公開が必要になります。"
        )


if __name__ == "__main__":
    main()