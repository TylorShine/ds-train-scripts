@ECHO OFF
CD /d %~dp0

CALL setup.bat

@REM data_type: lab_wav, csv_wav, ds
SET DATA_TYPE=lab_wav

CD content
python ..\extract_data.py --data_type %DATA_TYPE% --data_zip_path "%1"

pause