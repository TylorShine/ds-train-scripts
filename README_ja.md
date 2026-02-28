# DiffSinger トレーニングスクリプト
[[English](README.md) | *日本語*]

DiffSinger音声合成モデルのトレーニングプロセスを効率化するスクリプト集です。

## 概要

このリポジトリには、DiffSinger（歌声合成モデル）のセットアップとトレーニングワークフローを自動化するユーティリティスクリプトが含まれています。スクリプトはリポジトリのクローン、環境設定、データ準備、トレーニングプロセスを処理します。

## 必要条件

- Git（リポジトリのクローン用、オプション）
- CUDA対応GPU（トレーニング用）
- Windows OS（セットアップにバッチスクリプトを使用）
- Visual Studio Build Tools（`pydomino`のビルド時に使用）
  - [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)からダウンロードしてインストールします。ページ下部の「すべてのダウンロード」以下->「Tools for Visual Studio」->「Build Tools for Visual Studio 2022」からダウンロードします。

## 始め方

1. このリポジトリをクローンします：
   ```bat
   git clone https://github.com/TylorShine/ds-train-scripts.git
   cd ds-train-scripts
   ```

   - もしくは、[ここ](https://github.com/TylorShine/ds-train-scripts/archive/refs/heads/main.zip)からダウンロードして解凍します。


2. 環境をセットアップするために起動スクリプトを*2回*実行します：
   ```bat
   00-launch.bat
   ... 初期セットアップ完了後、もう一度実行
   00-launch.bat
   ```

   これにより以下が実行されます：
   - 必要なディレクトリの作成
   - Python仮想環境の作成  (MicroMamba)
   - 必要なリポジトリのクローン：
     - nnsvs-db-converter（データセット変換用）
     - DiffSinger（メインモデルリポジトリ）
     - MakeDiffSinger（ユーティリティ）
     - ghin_shenanigans（データセットの音声分割用）
     - その他...（`00-launch.bat`を参照）
   - 必要なモデルファイルなどのダウンロード

3. データセットを作成します（NNSVSの構造と同じ）：
   ```
   - my_voice_name
        - song1
            - song1.wav（音声ファイル）
            - song1.lab（アラインメントファイル）
        - song2
            - song2.wav
            - song2.lab
        - ...
   - ...
   ```
   そしてzip（または7-zip）で圧縮します。


   もしラベルがない場合は、データ構造は以下のようになります：

   ```
   - my_voice_name
        - song1
            - song1.wav（音声ファイル）
            - song1.txt（書き起こしファイル、オプション）
        - song2
            - song2.wav
            - song2.txt
        - ...
   - ...
   ```
   そしてzipで圧縮します。

4. `01-extract_data-lab_wav-midi.bat`にzipファイルをドラッグ＆ドロップします。

    - ラベルのないデータセットを使用する場合は、`01-extract_data-lab_wav-midi-transcribe-midi.bat`にzipファイルをドラッグ＆ドロップします。
      - さらに、約物記号("！"、"？"または"…")を維持したい場合は、`01-extract_data-lab_wav-midi-transcribe-punct-midi.bat`にzipファイルをドラッグ＆ドロップします。

5. （オプション）`02-edit_config_acoustic.bat`を編集して学習データの出力ディレクトリのパスやモデルの歌唱言語を設定します。

6. `02-edit_config_acoustic.bat`を実行して設定ファイルを生成します。

7. `03-preprocess_acoustic.bat`を実行してデータの前処理を行います。

8. `04-train_acoustic.bat`を実行して音響モデルのトレーニングを開始します。

    - トレーニング中は、 [localhost:6006](http://localhost:6006/) からトレーニングの進行状況を確認できます。
    - もし、トレーニングプロセスを中断したい場合は、`Ctrl+C`を押してください。

9. （オプション）`05-edit_config_variance.bat`を編集して学習データの出力ディレクトリのパスやモデルの歌唱言語を設定します。

10. `05-edit_config_variance.bat`を実行して設定ファイルを生成します。

11. `06-preprocess_variance.bat`を実行してデータの前処理を行います。

12. `07-train_variance.bat`を実行してバリアンスモデルのトレーニングを開始します。
    
    - トレーニング中は、 [localhost:6006](http://localhost:6006/) からトレーニングの進行状況を確認できます。
    - もし、トレーニングプロセスを中断したい場合は、`Ctrl+C`を押してください。

13. `08-export_onnx.bat`を編集して出力ディレクトリのパスとボイスバンク名を設定します。

14. 出力ディレクトリの設定ファイルを編集します。（OpenUTAU用）

    - 基本的には、`character.txt`のみ編集が必要です。
    - 詳細は[xunmengshe/OpenUtauのwiki](https://github.com/xunmengshe/OpenUtau/wiki/Voicebank-Development)を参照してください。

## 謝辞

このプロジェクトは以下のリポジトリを基に構築されています。作者/メンテナ/貢献者の皆様に感謝いたします！：
- [MLo7GhinsanのDiffSinger_colab_notebook](https://github.com/MLo7Ghinsan/DiffSinger_colab_notebook_MLo7)
  - 多くのプロセスはこのリポジトリを基にしています。
- [DiffSinger](https://github.com/openvpi/DiffSinger)
- [MakeDiffSinger](https://github.com/openvpi/MakeDiffSinger)
- [nnsvs-db-converter](https://github.com/UtaUtaUtau/nnsvs-db-converter)

## ライセンス

MIT License
