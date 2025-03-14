@ECHO OFF
CD /d %~dp0

CALL setup.bat

CD content\DiffSinger

@REM parser = argparse.ArgumentParser(description='Train DiffSinger model')
@REM parser.add_argument('--save_interval', type=int, default=2000, help='Step interval for validation and saving')
@REM parser.add_argument('--batch_size', type=int, default=9, help='Batch size for training')
@REM parser.add_argument('--max_updates', type=int, default=160000, help='Maximum training steps')
@REM parser.add_argument('--resume_training', action='store_true', help='Resume training from checkpoint')
@REM parser.add_argument('--local_data', action='store_true', help='Use locally binarized data')
@REM parser.add_argument('--re_config_path', type=str, default='', help='Path to existing config for resume training')
@REM parser.add_argument('--training_config', type=str, default='content/DiffSinger/configs/acoustic.yaml', help='Path to training config file')
@REM parser.add_argument('--save_dir', type=str, default='', help="Path to model save path")

@REM SET TRAINING_CONFIG=../configs/acoustic.yaml
@REM SET TRAINING_CONFIG=../configs/acoustic_vocoder.yaml
SET TRAINING_CONFIG=../configs/variance.yaml

SET SAVE_DIR=../trained_models/diffsinger_variance

python ..\..\train.py --save_interval 1000 --batch_size 8 --max_updates 160000 --training_config "%TRAINING_CONFIG%" --save_dir "%SAVE_DIR%"

pause