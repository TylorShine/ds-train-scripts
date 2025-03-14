@ECHO OFF
CD /d %~dp0

CALL setup.bat

CD content/DiffSinger

@REM model type: acoustic, variance, acoustic_vocoder
SET MODEL_TYPE=acoustic

SET TRAINING_CONFIG=../configs/%MODEL_TYPE%.yaml

SET PYTHONPATH="."

python scripts/binarize.py --config %TRAINING_CONFIG% --reset

pause