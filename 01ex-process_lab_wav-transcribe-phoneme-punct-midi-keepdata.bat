@ECHO OFF
CD /d %~dp0

CALL setup.bat

@REM data_type: lab_wav, csv_wav, ds
SET DATA_TYPE=lab_wav

SET TRANSCRIBE_PHONEME_MODEL=TylorShine/wavlm-base-plus-hiragana-ctc
SET TRANSCRIBE_LANGUAGE=ja
SET TRANSCRIBE_BATCH_SIZE=8

@REM "openjtalk+domino" or "openjtalk+SOFA"
SET ALIGNMENT_TYPE="openjtalk+domino"

@REM SET ADDITIONAL_ARGS=
SET ADDITIONAL_ARGS=--keep_punctuations


CD content
python ..\extract_data.py --data_type %DATA_TYPE% --data_zip_path "" --no_cleanup --estimate_midi SOME --transcription_phoneme_model "%TRANSCRIBE_PHONEME_MODEL%" --transcription_language %TRANSCRIBE_LANGUAGE% --transcription_batch_size %TRANSCRIBE_BATCH_SIZE% --g2p_alignment_type %ALIGNMENT_TYPE% %ADDITIONAL_ARGS%

pause