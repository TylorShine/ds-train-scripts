# DiffSinger Training Scripts
[*English* | [日本語](README_ja.md)]

A collection of scripts to streamline the DiffSinger voice synthesis model training process.

## Overview

This repository contains utility scripts that automate the setup and training workflow for DiffSinger, a singing voice synthesis model. The scripts handle repository cloning, environment setup, data preparation, and training processes.

## Prerequisites

- Git (for cloning repositories, optional)
- CUDA-compatible GPU (for training)
- Windows OS (as the setup uses batch scripts)
- Visual Studio Build Tools 2022 (using when building `pydomino`)
  - You can download it from [here](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022).

## Getting Started

1. Clone this repository:
   ```bat
   git clone https://github.com/TylorShine/ds-train-scripts.git
   cd ds-train-scripts
   ```

   - or, download and unzip from [here](https://github.com/TylorShine/ds-train-scripts/archive/refs/heads/main.zip).

2. Run the launch script *twice* to set up the environment:
   ```bat
   00-launch.bat
   ... after setup completes, run again
   00-launch.bat
   ```

   This will:
   - Create necessary directories
   - Create a Python virtual environment (MicroMamba)
   - Clone required repositories:
     - nnsvs-db-converter (for dataset conversion)
     - DiffSinger (main model repository)
     - MakeDiffSinger (utilities)
     - ghin_shenanigans (for audio dataset splitting)
     - and so on... (see `00-launch.bat`)
   - Download necessary model files etc.

3. Make datasets (same as a NNSVS's structure):
   ```
   - my_voice_name
        - song1
            - song1.wav (audio file)
            - song1.lab (alignment file, HTK's format)
        - song2
            - song2.wav
            - song2.lab
        - ...
   - ...
   ```
   and zip (or 7-zip) it.


   If you will not have labels, data structure will be:
    ```
    - my_voice_name
        - song1
            - song1.wav (audio file)
            - song1.txt (transcript file, optional)
        - song2
            - song2.wav
            - song2.txt
        - ...
    - ...
    ```
    and zip it.

4. D&D the zip to `01-extract_data-lab_wav-midi.bat`.

    - If you will not have labels, D&D `01-extract_data-wav-transcribe-midi.bat` to the zip file.
      - and, you wanna try to keep the punctuations ("!", "?" and "..."), run `01-extract_data-wav-transcribe-punct-midi.bat` instead.

5. (optional) Edit `02-edit_config_acoustic.bat` to set the paths to the output directory or language.

6. Run `02-edit_config_acoustic.bat` to generate the configuration file.

7. Run `03-preprocess_acoustic.bat` to preprocess the data.

8. Run `04-train_acoustic.bat` to start the training process for the acoustic model.

    - During the training process, you can check the training progress on [localhost:6006](http://localhost:6006/)
    - If you want to stop the training process, press `Ctrl+C` in the terminal. You can resume the training process by running `04-train_acoustic.bat` again.

9. (optional) Edit `05-edit_config_variance.bat` to set the paths to the output directory or language.

10. Run `05-edit_config_variance.bat` to generate the configuration file.

11. Run `06-preprocess_variance.bat` to preprocess the data.

12. Run `07-train_variance.bat` to start the training process for the variance model.

    - During the training process, you can check the training progress on [localhost:6006](http://localhost:6006/)
    - If you want to stop the training process, press `Ctrl+C` in the terminal. You can resume the training process by running `07-train_variance.bat` again.

13. Edit `08-export_onnx.bat` to set the paths to the output directory and your voice bank name.

14. Edit configs in output directory (for OpenUtau):

    - mainly, you only need to edit the `character.txt`.
    - Please refer to [xunmengshe/OpenUtau's wiki](https://github.com/xunmengshe/OpenUtau/wiki/Voicebank-Development) for more details.

## Acknowledgements

This project builds upon the following repositories, thanks to their creators/maintainers/contributors!:
- [MLo7Ghinsan's DiffSinger_colab_notebook](https://github.com/MLo7Ghinsan/DiffSinger_colab_notebook_MLo7)
  - many processes are based on this repository.
- [DiffSinger](https://github.com/openvpi/DiffSinger)
- [MakeDiffSinger](https://github.com/openvpi/MakeDiffSinger)
- [nnsvs-db-converter](https://github.com/UtaUtaUtau/nnsvs-db-converter)

## License

MIT License
