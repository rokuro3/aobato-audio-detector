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

BirdNET+ V3.0 developer previewのモデルおよび利用条件は、リポジトリの `TERMS_OF_USE.md` と公式配布元を確認してください。再配布時はモデルの利用条件とZenodoの配布条件を必ず守ってください。