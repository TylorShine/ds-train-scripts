@ECHO OFF
CD /d %~dp0

SET DOWNLOAD_CACHE_DIR=%~dp0cache\downloads
IF NOT EXIST "%DOWNLOAD_CACHE_DIR%" mkdir "%DOWNLOAD_CACHE_DIR%"


@REM download Micromamba
@REM SET MAMBA_DIR=https://micro.mamba.pm/api/micromamba/win-64/latest
SET MAMBA_DIR=https://github.com/mamba-org/micromamba-releases/releases/download/1.5.10-0/micromamba-win-64.tar.bz2
SET MAMBA_FILE=micromamba.tar.bz2
SET MAMBA_BIN=%DOWNLOAD_CACHE_DIR%\%MAMBA_FILE%
IF NOT EXIST "%MAMBA_BIN%" (
    ECHO Info: Start downloading the Micromamba...
    ECHO .
    curl -L -o "%MAMBA_BIN%" "%MAMBA_DIR%"
    IF %ERRORLEVEL% neq 0 (
        ECHO .
        ECHO Error: Failed to download the Micromamba
        EXIT /b
    )
)

@REM extract Micromamba
SET MAMBA_ROOT_DIR=Library\bin
IF NOT EXIST "%DOWNLOAD_CACHE_DIR%\%MAMBA_ROOT_DIR%" (
    ECHO.
    ECHO Info: Extract the Micromamba...
    tar xf "%MAMBA_BIN%" -C "%DOWNLOAD_CACHE_DIR%"
    IF %ERRORLEVEL% neq 0 (
        ECHO.
        ECHO Error: Failed to extract the Micromamba
        EXIT /b
    )
)

@REM make env
SET PYTHON_VERSION="python<3.12"
SET MAMBA_ROOT_PREFIX=%DOWNLOAD_CACHE_DIR%\%MAMBA_ROOT_DIR%
SET MICROMAMBA_BIN=%MAMBA_ROOT_PREFIX%\micromamba.exe
if exist "%MAMBA_ROOT_PREFIX%\Scripts\" (
  goto :ACTIVATE
)

"%MICROMAMBA_BIN%" shell hook -s cmd.exe -p "%MAMBA_ROOT_PREFIX%" -v

:ACTIVATE
@REM call mamba_hook.bat
@REM SET OLDPWD=%CD%
@REM CD /d "%MAMBA_ROOT_PREFIX%\Scripts"
@REM call activate.bat
@REM CD /d "%OLDPWD%"
REM "%MICROMAMBA_BIN%" shell hook -s cmd.exe -p "%MAMBA_ROOT_PREFIX%" -v
SET MAMBA_ENV_NAME=diffsinger
IF NOT EXIST "%MAMBA_ROOT_PREFIX%\envs\%MAMBA_ENV_NAME%" (
    ECHO.
    ECHO Info: Make env...
    ECHO %MICROMAMBA_BIN%
    ECHO %DOWNLOAD_CACHE_DIR%
    ECHO %MAMBA_ROOT_DIR%
    ECHO %PYTHON_VERSION%
    PUSHD "%MAMBA_ROOT_PREFIX%\Scripts"
    call activate.bat
    POPD
    micromamba --version
    micromamba create -y -n %MAMBA_ENV_NAME% %PYTHON_VERSION% uv git 7zip -c conda-forge
    IF %ERRORLEVEL% neq 0 (
        ECHO.
        ECHO Error: Failed to create venv environment
        EXIT /b
    )
    ECHO.
    ECHO =======================================================================
    ECHO Info: Successful create python environment.
    ECHO       We need restart shell, launch same script again and ready to use!
    ECHO =======================================================================
    ECHO.
    PAUSE
    EXIT
)

@REM call scripts\make_env.bat

@REM activate env
ECHO.
ECHO Info: Activate env...
@REM "%MICROMAMBA_BIN%" activate %MAMBA_ENV_NAME%
@REM micromamba.exe activate %MAMBA_ENV_NAME%
PUSHD "%MAMBA_ROOT_PREFIX%\Scripts"
call activate.bat %MAMBA_ENV_NAME%
POPD
WHERE python


@REM update pip
ECHO.
ECHO Info: Update pip...
python -m pip install -U pip

SET CONTENT_DIR=%~dp0content
IF NOT EXIST "%CONTENT_DIR%" mkdir "%CONTENT_DIR%"
PUSHD "%CONTENT_DIR%"

@REM clone repos
ECHO.
ECHO Info: Clone repos...
@REM nnsvs-db-converter
IF NOT EXIST "nnsvs-db-converter" (
    git clone https://github.com/UtaUtaUtau/nnsvs-db-converter.git
)
@REM DiffSinger
IF NOT EXIST "DiffSinger" (
    git clone https://github.com/openvpi/DiffSinger.git
)
@REM MakeDiffSinger for ds training
IF NOT EXIST "MakeDiffSinger" (
    git clone https://github.com/openvpi/MakeDiffSinger.git
)
@REM ghin_shenanigans for ds segmenting... and for setup complete wav
IF NOT EXIST "ghin_shenanigans" (
    git clone https://github.com/MLo7Ghinsan/ghin_shenanigans.git
)
@REM SOME, yass some midi estimation
IF NOT EXIST "SOME" (
    git clone https://github.com/openvpi/SOME.git
)
POPD

@REM install torch
SET TORCH_INSTALL_CMD=uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
SET TORCH_PACKAGE=torch
uv pip show torch > NUL
IF %ERRORLEVEL% neq 0 (
    ECHO.
    ECHO Info: Install torch...
    %TORCH_INSTALL_CMD%
)

@REM install requirements
ECHO.
ECHO Info: Check install requirements...
@REM uv pip install "numpy<2" cython
@REM @REM uv pip install https://github.com/liyaodev/fairseq/releases/download/v0.12.3.1/fairseq-0.12.3.1-cp311-cp311-win_amd64.whl
@REM uv pip install -r %CONTENT_DIR%/DiffSinger/requirements.txt
@REM uv pip install -r %CONTENT_DIR%/SOME/requirements.txt
@REM uv pip install mido einops tensorboard onnxruntime pydub
@REM uv pip install onnxscript

@REM download prerequisites
CALL dl-prerequisites.bat

ECHO.
ECHO Info: Ready
ECHO.
