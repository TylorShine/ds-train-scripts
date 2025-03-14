@ECHO OFF
CD /d %~dp0

CALL setup.bat

@REM Type the ID of speakers you'd like to KEEP separated by commas. Ex: "0,3,4"
@REM Note: You can find the ID of speakers in the model by opening the spk_map.json file in the model folder.
@REM If you see {"natural": 0, "power": 1, "silly": 2} but only want to keep "natural" and "power", type 0,1 below.
SET RETAIN_SPEAKERS=0

@REM If you don't know what this means, don't change it.
@REM ['zeros', 'random', 'mean', 'cyclic']
SET FILL_EMBED=zeros

SET DROP_OUT_PATH = "%~dpn0_spk-dropped%~x0"

python content\DiffSinger\scripts\drop_spk.py "%1" "%DROP_OUT_PATH%" --retain %RETAIN_SPEAKERS% --fill %FILL_EMBED%

pause