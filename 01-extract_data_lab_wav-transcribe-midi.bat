@ECHO OFF
CD /d %~dp0

CALL setup.bat

@REM data_type: lab_wav, csv_wav, ds
SET DATA_TYPE=lab_wav

SET WHISPER_MODEL=openai/whisper-large-v3-turbo
SET WHISPER_LANGUAGE=ja
@REM SET WHISPER_MODEL=kotoba-tech/kotoba-whisper-v2.1

@REM "openjtalk+domino" or "openjtalk+SOFA"
SET ALIGNMENT_TYPE="openjtalk+domino"

SET ADDITIONAL_ARGS=
@REM SET ADDITIONAL_ARGS=--keep_punctuations


CD content
python ..\extract_data.py --data_type %DATA_TYPE% --data_zip_path "%1" --estimate_midi SOME --transcription_model "%WHISPER_MODEL%" --transcription_language %WHISPER_LANGUAGE% --g2p_alignment_type %ALIGNMENT_TYPE% %ADDITIONAL_ARGS%

pause