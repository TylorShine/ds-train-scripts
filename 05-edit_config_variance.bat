@ECHO OFF
CD /d %~dp0

CALL setup.bat

CD content\DiffSinger

@REM parser = argparse.ArgumentParser(description='DiffSinger configuration editor')
@REM parser.add_argument('--model-type', choices=['acoustic', 'variance'], default='acoustic', help='Model type to train')
@REM parser.add_argument('--diffusion-type', choices=['ddpm', 'reflow'], default='reflow', help='Diffusion type')
@REM parser.add_argument('--diff-accelerator', choices=['ddim', 'pndm', 'dpm-solver', 'unipc'], default='ddim', help='Diffusion accelerator')
@REM parser.add_argument('--loss-type', choices=['l1', 'l2'], default='l2', help='Loss type')
@REM parser.add_argument('--data-dir', required=True, help='Directory containing raw data')
@REM parser.add_argument('--use-shallow-diffusion', choices=['false', 'true_aux_val', 'true_gt_val'], default='true_gt_val', help='Shallow diffusion training mode')
@REM parser.add_argument('--precision', choices=['32-true', 'bf16-mixed', '16-mixed', 'bf16', '16'], default='16-mixed', help='Training precision')
@REM parser.add_argument('--save-dir', required=True, help='Model save directory')
@REM parser.add_argument('--enable-finetuning', action='store_true', help='Enable finetuning')
@REM parser.add_argument('--base-model-path', help='Path to custom base model')
@REM parser.add_argument('--selected-param', choices=['energy_breathiness', 'tension', 'voicing', 'none'], default='tension', help='Model embeds selection')
@REM parser.add_argument('--parameter-extraction', choices=['vr', 'world'], default='vr', help='Parameter extraction method')
@REM parser.add_argument('--pitch-training', choices=['false', 'standard', 'melody_encoder'], default='false', help='Pitch training mode')
@REM parser.add_argument('--f0-extractor', choices=['parselmouth', 'rmvpe', 'harvest'], default='parselmouth', help='F0 extractor algorithm')
@REM parser.add_argument('--sampling-algorithm', choices=['euler', 'rk2', 'rk4', 'rk5'], default='euler', help='Sampling algorithm')
@REM parser.add_argument('--acoustic-hidden-size', type=int, default=256, help='Acoustic hidden size')
@REM parser.add_argument('--acoustic-num-layers', type=int, default=6, help='Acoustic number of layers')
@REM parser.add_argument('--acoustic-num-channels', type=int, default=1024, help='Acoustic number of channels')
@REM parser.add_argument('--variance-hidden-size', type=int, default=256, help='Variance hidden size')
@REM parser.add_argument('--duration-hidden-size', type=int, default=512, help='Duration hidden size')
@REM parser.add_argument('--melody-encoder-hidden-size', type=int, default=128, help='Melody encoder hidden size')
@REM parser.add_argument('--pitch-num-layers', type=int, default=6, help='Pitch number of layers')
@REM parser.add_argument('--pitch-num-channels', type=int, default=512, help='Pitch number of channels')
@REM parser.add_argument('--variance-num-layers', type=int, default=6, help='Variance number of layers')
@REM parser.add_argument('--variance-num-channels', type=int, default=384, help='Variance number of channels')

SET SAVE_DIR=../trained_models/diffsinger_variance

SET DATA_DIR=../raw_data/diffsinger_db
@REM SET MODEL_TYPE=acoustic
SET MODEL_TYPE=variance
SET LANGUAGE=ja
SET DIFFUSION_TYPE=reflow
SET DIFF_ACCELERATOR=ddim
SET LOSS_TYPE=l2
SET USE_SHALLOW_DIFFUSION=true_gt_val
@REM SET USE_SHALLOW_DIFFUSION=true_aux_val
SET PRECISION=bf16-mixed
SET SELECTED_PARAM=tension
SET PARAMETER_EXTRACTION=vr
@REM SET PITCH_TRAINING=melody_encoder
SET PITCH_TRAINING=standard
SET F0_EXTRACTOR=rmvpe
SET SAMPLING_ALGORITHM=euler
SET ACOUSTIC_HIDDEN_SIZE=256
SET ACOUSTIC_NUM_LAYERS=6
SET ACOUSTIC_NUM_CHANNELS=1024
SET VARIANCE_HIDDEN_SIZE=256
SET DURATION_HIDDEN_SIZE=512
SET MELODY_ENCODER_HIDDEN_SIZE=128
SET PITCH_NUM_LAYERS=6
SET PITCH_NUM_CHANNELS=512
SET VARIANCE_NUM_LAYERS=6
SET VARIANCE_NUM_CHANNELS=384

python ..\..\edit_config.py --data-dir "%DATA_DIR%" --save-dir "%SAVE_DIR%" --language "%LANGUAGE%" --model-type %MODEL_TYPE% --diffusion-type %DIFFUSION_TYPE% --diff-accelerator %DIFF_ACCELERATOR% --loss-type %LOSS_TYPE% --use-shallow-diffusion %USE_SHALLOW_DIFFUSION% --precision %PRECISION% --selected-param %SELECTED_PARAM% --parameter-extraction %PARAMETER_EXTRACTION% --pitch-training %PITCH_TRAINING% --f0-extractor %F0_EXTRACTOR% --sampling-algorithm %SAMPLING_ALGORITHM% --acoustic-hidden-size %ACOUSTIC_HIDDEN_SIZE% --acoustic-num-layers %ACOUSTIC_NUM_LAYERS% --acoustic-num-channels %ACOUSTIC_NUM_CHANNELS% --variance-hidden-size %VARIANCE_HIDDEN_SIZE% --duration-hidden-size %DURATION_HIDDEN_SIZE% --melody-encoder-hidden-size %MELODY_ENCODER_HIDDEN_SIZE% --pitch-num-layers %PITCH_NUM_LAYERS% --pitch-num-channels %PITCH_NUM_CHANNELS% --variance-num-layers %VARIANCE_NUM_LAYERS% --variance-num-channels %VARIANCE_NUM_CHANNELS%

pause