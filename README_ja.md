# DiffSinger トレーニングスクリプト
[[English](README.md) | *日本語*]

DiffSinger音声合成モデルのトレーニングプロセスを効率化するスクリプト集です。

## 概要

このリポジトリには、DiffSinger（歌声合成モデル）のセットアップとトレーニングワークフローを自動化するユーティリティスクリプトが含まれています。スクリプトはリポジトリのクローン、環境設定、データ準備、トレーニングプロセスを処理します。

## 必要条件

- Git（リポジトリのクローン用）
- CUDA対応GPU（トレーニング用）
- Windows OS（セットアップにバッチスクリプトを使用）

## 始め方

1. このリポジトリをクローンします：
   ```bat
   git clone https://github.com/TylorShine/ds-train-scripts.git
   cd ds-train-scripts
   ```

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
     - MakeDiffSinger（トレーニングユーティリティ）
     - ghin_shenanigans（音声セグメンテーション用）

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

4. `01-extract_data-lab_wav-midi.bat`をzipファイルにドラッグ＆ドロップします。

5. `02-edit_config_acoustic.bat`を編集して出力ディレクトリのパスを設定します。

6. `02-edit_config_acoustic.bat`を実行して設定ファイルを生成します。

7. `03-preprocess_acoustic.bat`を実行してデータの前処理を行います。

8. `04-train_acoustic.bat`を実行して音響モデルのトレーニングを開始します。

9. `05-edit_config_variance.bat`を編集して出力ディレクトリのパスを設定します。

10. `05-edit_config_variance.bat`を実行して設定ファイルを生成します。

11. `06-preprocess_variance.bat`を実行してデータの前処理を行います。

12. `07-train_variance.bat`を実行してバリアンスモデルのトレーニングを開始します。

13. `08-export_onnx.bat`を編集して出力ディレクトリのパスを設定します。

14. 出力ディレクトリとその構造の設定を編集します（OpenUTAU用）
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
