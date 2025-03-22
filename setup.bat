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
@REM SOFA: Singing-Oriented Forced Aligner
IF NOT EXIST "SOFA" (
    git clone https://github.com/qiuqiao/SOFA.git
)
@REM pydomino
IF NOT EXIST "pydomino" (
    call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    IF %ERRORLEVEL% neq 0 CALL ERROR_VS_BUILD_TOOLS_NOT_INSTALLED
    IF %ERRORLEVEL% neq 0 EXIT /b %ERRORLEVEL%

    git clone --recursive https://github.com/DwangoMediaVillage/pydomino.git
    PUSHD pydomino
    uv pip install .
    IF %ERRORLEVEL% neq 0 CALL ERROR_PYDOMINO_INSTALL_FAILED
    POPD
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
IF EXIST "%CONTENT_DIR%\_skip_install_requirements" GOTO DL_REQUIREMENTS
ECHO.
ECHO Info: Check install requirements...
uv pip install "numpy<2" cython
@REM uv pip install https://github.com/liyaodev/fairseq/releases/download/v0.12.3.1/fairseq-0.12.3.1-cp311-cp311-win_amd64.whl
uv pip install -r %CONTENT_DIR%/DiffSinger/requirements.txt
uv pip install -r %CONTENT_DIR%/SOME/requirements.txt
uv pip install -r %CONTENT_DIR%/SOFA/requirements.txt
uv pip install mido einops tensorboard onnxruntime pydub
uv pip install onnxscript

@REM === For transcription ===
uv pip install transformers
uv pip install pyopenjtalk-plus
@REM uv pip install stable-ts punctuators

ECHO. > %CONTENT_DIR%\_skip_install_requirements

:DL_REQUIREMENTS
@REM download prerequisites
CALL dl-prerequisites.bat

ECHO.
ECHO Info: Ready
ECHO.

EXIT /b 0


:ERROR_VS_BUILD_TOOLS_NOT_INSTALLED
ECHO.
ECHO Info: Visual Studio Build Tools 2022 is not installed.
ECHO       Please install Visual Studio Build Tools 2022 and try again if you want to use pydomino.
ECHO       https://visualstudio.microsoft.com/downloads/
ECHO       (You can find it under "Tools for Visual Studio" in this page.)
ECHO       Also, check "C++ build tools" in "Individual components" in the installer.
ECHO Note: If you have an another build environment in your path (e.g. MSYS2),
ECHO       you should remove it from your path or workaround it e.g.:
ECHO           SET PATH=[VSPATH]\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%%PATH%%
ECHO           SET PATH=[VSPATH]\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%%PATH%%
ECHO       This is a workaround for the issue that cmake cannot find the MSVC compiler.
ECHO       and then:
ECHO           PUSHD content\pydomino
ECHO           pip install .
ECHO       in this console.
ECHO.
EXIT /b 1


:ERROR_PYDOMINO_INSTALL_FAILED
ECHO.
ECHO Error: Install process of pydomino perhaps failed.
ECHO        Please check the error message above and try again.
ECHO.
ECHO Note: If you have an another build environment in your path (e.g. MSYS2),
ECHO       you should remove it from your path or workaround it e.g.
ECHO           SET PATH=[VSPATH]\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%%PATH%%
ECHO           SET PATH=[VSPATH]\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%%PATH%%
ECHO       This is a workaround for the issue that cmake cannot find the MSVC compiler.
ECHO       and then:
ECHO           PUSHD content\pydomino
ECHO           RMDIR /S /Q build
ECHO           uv pip install .
ECHO       in this console.
ECHO.
ECHO  Your current CMake path:
WHERE cmake
ECHO  Your current Ninja path:
WHERE ninja
ECHO.
EXIT /b 1