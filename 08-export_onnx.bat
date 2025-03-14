@ECHO OFF
CD /d %~dp0

CALL setup.bat

CD content\DiffSinger

@REM parser = argparse.ArgumentParser(description='Export DiffSinger models to ONNX format')
@REM parser.add_argument('--acoustic', type=str, help='Path to acoustic checkpoint', default='')
@REM parser.add_argument('--variance', type=str, help='Path to variance checkpoint', default='')
@REM parser.add_argument('--fir_acoustic_vocoder', type=str, help='Path to FirSinger acoustic/vocoder checkpoint', default='')
@REM parser.add_argument('--output', type=str, required=True, help='Output folder path')
@REM parser.add_argument('--quiet', action='store_true', help='Hide ONNX converter output')
@REM parser.add_argument('--conda', type=str, help='Path to conda executable', default='conda')
@REM args = parser.parse_args()

@REM SET ACOUSTIC_CKPT=../trained_models/diffsinger
@REM SET VARIANCE_CKPT=../trained_models/diffsinger
SET ACOUSTIC_CKPT="../trained_models/diffsinger/model_ckpt_steps_160000.ckpt"
SET VARIANCE_CKPT="../trained_models/diffsinger_variance/model_ckpt_steps_160000.ckpt"
SET ONNX_OUTPUT_DIR=../output_models/diffsinger

SET CONDAEXE=micromamba

python ..\..\export_onnx.py --acoustic %ACOUSTIC_CKPT% --variance %VARIANCE_CKPT% --fir_acoustic_vocoder %FIR_ACOUSTIC_VOCODER_CKPT% --output %ONNX_OUTPUT_DIR% --conda %CONDAEXE%

pause