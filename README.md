# アオバト音声検出AI

アップロードした音声をBirdNET+ V3.0で3秒チャンクごとに推論し、`Treron sieboldii`（アオバト）の検出確率を表示・CSV出力します。モデルとラベルCSVはセットアップ時にZenodoから自動取得します。モデルファイルは配布物に同梱しません。

## Windowsで配布する場合

1. このフォルダーを配布先へコピーします。
2. `setup.bat` をダブルクリックして、一度セットアップします。

3. `run_app.bat` をダブルクリックします。
4. 表示された `http://localhost:8501` をブラウザーで開きます。

セットアップスクリプトはPython 3.12のWindows x64 embedded版、必要なライブラリ、BirdNET V3.0モデル（約68MB）、ラベルCSVを順に取得します。処理中は全体の進捗率が表示されます。セットアップにはインターネット接続が必要です。

`setup.bat` が内部で必要なPowerShell処理を呼び出すため、利用者が `.ps1` を直接実行したり、実行ポリシーを変更したりする必要はありません。

すでに一度セットアップしていて `No module named streamlit` が表示される場合も、`setup.bat` をもう一度実行してください。セットアップの最後にStreamlitのimport確認が表示されます。

## 開発環境での起動

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## クレジット

Powered by BirdNET+ V3.0 Developer Preview 3.1。BirdNET+ V3.0

- ライセンス: [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)
- 引用: Lasseck, M., Eibl, M., Klinck, H., & Kahl, S. (2026). *BirdNET+ V3.0 model developer preview (Preview 3.1).* Zenodo. [https://doi.org/10.5281/zenodo.20703646](https://doi.org/10.5281/zenodo.20703646)
- 利用条件: [BirdNET+ V3.0 Developer Preview Terms of Use](https://github.com/birdnet-team/birdnet-V3.0-dev/blob/main/TERMS_OF_USE.md)

BirdNET+ V3.0 developer previewのモデルおよび利用条件は、リポジトリの `TERMS_OF_USE.md` と公式配布元を確認してください。再配布時はモデルの利用条件とZenodoの配布条件を必ず守ってください。