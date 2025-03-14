@ECHO OFF
CD /d %~dp0

SET CONTENT_DIR=%~dp0content
IF NOT EXIST "%CONTENT_DIR%" mkdir "%CONTENT_DIR%"

SET DOWNLOAD_MODEL_DIR=%CONTENT_DIR%\pretrain_models
IF NOT EXIST "%DOWNLOAD_MODEL_DIR%" mkdir "%DOWNLOAD_MODEL_DIR%"

PUSHD "%CONTENT_DIR%"

@REM download jpn_dict.txt for OpenUtau
SET JPN_DICT_URI=https://github.com/MLo7Ghinsan/DiffSinger_colab_notebook_MLo7/releases/download/OU_files/jpn_dict.txt
SET JPN_DICT_FILE=jpn_dict.txt
SET JPN_DICT_DEST=%CONTENT_DIR%\%JPN_DICT_FILE%
CALL :DOWNLOAD_FILES "jpn_dict.txt for the OpenUtau" "%JPN_DICT_URI%" "%JPN_DICT_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download NSF-HiFiGAN vocoder model from OpenVPI
SET NSF_HIFIGAN_URI=https://github.com/openvpi/vocoders/releases/download/nsf-hifigan-44.1k-hop512-128bin-2024.02/nsf_hifigan_44.1k_hop512_128bin_2024.02.zip
SET NSF_HIFIGAN_FILE=nsf_hifigan_44.1k_hop512_128bin_2024.02.zip
SET NSF_HIFIGAN_DEST=%CONTENT_DIR%\%NSF_HIFIGAN_FILE%
CALL :DOWNLOAD_FILES "NSF-HiFiGAN vocoder model" "%NSF_HIFIGAN_URI%" "%NSF_HIFIGAN_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download SOME MIDI estimation model
SET SOME_URI=https://github.com/openvpi/SOME/releases/download/v1.0.0-baseline/0119_continuous128_5spk.zip
SET SOME_FILE=0119_continuous128_5spk.zip
SET SOME_DEST=%CONTENT_DIR%\%SOME_FILE%
CALL :DOWNLOAD_FILES "SOME MIDI estimation model" "%SOME_URI%" "%SOME_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download hnsep Harmonic-Noise Separation model
SET HNSEP_URI=https://github.com/yxlllc/vocal-remover/releases/download/hnsep_240512/hnsep_240512.zip
SET HNSEP_FILE=hnsep_240512.zip
SET HNSEP_DEST=%CONTENT_DIR%\%HNSEP_FILE%
CALL :DOWNLOAD_FILES "hnsep Harmonic-Noise Separation model" "%HNSEP_URI%" "%HNSEP_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download RMVPE pitch estimation model
SET RMVPE_URI=https://github.com/openvpi/DiffSinger/releases/download/v2.1.0/rmvpe.zip
SET RMVPE_FILE=rmvpe.zip
SET RMVPE_DEST=%CONTENT_DIR%\%RMVPE_FILE%
CALL :DOWNLOAD_FILES "RMVPE pitch estimation model" "%RMVPE_URI%" "%RMVPE_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download DiffSinger acoustic pretrained model
SET DIFFSINGER_ACOUSTIC_PT_URI=https://github.com/haru0l/diffsinger_models/releases/download/acoustic/model_ckpt_steps_49000.ckpt
SET DIFFSINGER_ACOUSTIC_PT_FILE=acoustic_pretrain.ckpt
SET DIFFSINGER_ACOUSTIC_PT_DEST=%DOWNLOAD_MODEL_DIR%\%DIFFSINGER_ACOUSTIC_PT_FILE%
CALL :DOWNLOAD_FILES "DiffSinger acoustic pretrained model" "%DIFFSINGER_ACOUSTIC_PT_URI%" "%DIFFSINGER_ACOUSTIC_PT_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM download DiffSinger variance pretrained model
SET DIFFSINGER_VARIANCE_PT_URI=https://github.com/haru0l/diffsinger_models/releases/download/variance/model_ckpt_steps_51000.ckpt
SET DIFFSINGER_VARIANCE_PT_FILE=variance_pretrain.ckpt
SET DIFFSINGER_VARIANCE_PT_DEST=%DOWNLOAD_MODEL_DIR%\%DIFFSINGER_VARIANCE_PT_FILE%
CALL :DOWNLOAD_FILES "DiffSinger variance pretrained model" "%DIFFSINGER_VARIANCE_PT_URI%" "%DIFFSINGER_VARIANCE_PT_DEST%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)


@REM extract hnsep Harmonic-Noise Separation model
SET HNSEP_EXTRACT_DIR=%CONTENT_DIR%\DiffSinger\checkpoints
SET HNSEP_EXTRACT_CHECK_FILE=%HNSEP_EXTRACT_DIR%\vr\model.pt
CALL :EXTRACT_ARCHIVE_FILES "hnsep Harmonic-Noise Separation model" "%HNSEP_DEST%" "%HNSEP_EXTRACT_DIR%" "%HNSEP_EXTRACT_CHECK_FILE%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM extract SOME MIDI estimation model
SET SOME_EXTRACT_DIR=%CONTENT_DIR%\DiffSinger\checkpoints\SOME
SET SOME_EXTRACT_CHECK_FILE=%SOME_EXTRACT_DIR%\0119_continuous256_5spk\model_ckpt_steps_100000_simplified.ckpt
CALL :EXTRACT_ARCHIVE_FILES "SOME MIDI estimation model" "%SOME_DEST%" "%SOME_EXTRACT_DIR%" "%SOME_EXTRACT_CHECK_FILE%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM extract NSF-HiFiGAN model
SET NSF_HIFIGAN_EXTRACT_DIR=%CONTENT_DIR%\DiffSinger\checkpoints
SET NSF_HIFIGAN_EXTRACT_CHECK_FILE=%NSF_HIFIGAN_EXTRACT_DIR%\nsf_hifigan_44.1k_hop512_128bin_2024.02\model.ckpt
CALL :EXTRACT_ARCHIVE_FILES "NSF-HiFiGAN model" "%NSF_HIFIGAN_DEST%" "%NSF_HIFIGAN_EXTRACT_DIR%" "%NSF_HIFIGAN_EXTRACT_CHECK_FILE%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM extract RMVPE model
SET RMVPE_EXTRACT_DIR=%CONTENT_DIR%\DiffSinger\checkpoints
SET RMVPE_EXTRACT_CHECK_FILE=%RMVPE_EXTRACT_DIR%\rmvpe\model.pt
CALL :EXTRACT_ARCHIVE_FILES "RMVPE model" "%RMVPE_DEST%" "%RMVPE_EXTRACT_DIR%" "%RMVPE_EXTRACT_CHECK_FILE%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

@REM extract RMVPE model (for the MakeDiffSinger)
SET RMVPE_MDS_EXTRACT_DIR=%CONTENT_DIR%\MakeDiffSinger\variance-temp-solution\assets
SET RMVPE_MDS_EXTRACT_CHECK_FILE=%RMVPE_MDS_EXTRACT_DIR%\rmvpe\model.pt
CALL :EXTRACT_ARCHIVE_FILES "RMVPE model (for the MakeDiffSinger)" "%RMVPE_DEST%" "%RMVPE_MDS_EXTRACT_DIR%" "%RMVPE_MDS_EXTRACT_CHECK_FILE%"
IF %ERRORLEVEL% neq 0 (
    pause
    EXIT /b %ERRORLEVEL%
)

POPD

ECHO.
ECHO Info: All nececssary models downloaded successfully!
ECHO.

EXIT /b 0


:DOWNLOAD_FILES
:WHILE_DOWNLOAD
IF NOT EXIST "%3" (
    ECHO Info: Start downloading %1
    ECHO URI: %2
    ECHO.
    curl -L -o "%3" "%2"
    IF %ERRORLEVEL% neq 0 (
        ECHO.
        ECHO Error: Failed to download %1
        ECHO URI: %2
        EXIT /b 1
    )
)
SHIFT /2
SHIFT /2
IF NOT "%2"=="" GOTO WHILE_DOWNLOAD
EXIT /b 0

:EXTRACT_ARCHIVE_FILES
:WHILE_EXTRACT
IF NOT EXIST "%4" (
    ECHO Info: Extract %1
    ECHO File: %2
    ECHO Extract Dir: %3
    ECHO Extract Check File: %4
    ECHO.
    @REM tar xf "%2" -C "%3"
    7z x -o"%3" "%2"
    IF %ERRORLEVEL% neq 0 (
        ECHO.
        ECHO Error: Failed to download %DOWNLOAD_FILES_DESC%
        ECHO File: %2
        EXIT /b 1
    )
)
SHIFT /2
SHIFT /2
SHIFT /2
IF NOT "%2"=="" GOTO WHILE_EXTRACT
EXIT /b 0