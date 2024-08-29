@echo off

REM Set the path to the VLC installation directory
set VLC_DIR=C:\Program Files\VideoLAN\VLC

REM Run PyInstaller to convert the Python script to an .exe file
pyinstaller --onefile --windowed --name=PIA_Video_Annotation_Tool ^
            --add-binary "%VLC_DIR%\libvlc.dll;." ^
            --add-binary "%VLC_DIR%\libvlccore.dll;." ^
            --add-binary "%VLC_DIR%\axvlc.dll;." ^
            --add-binary "%VLC_DIR%\npvlc.dll;." main.py

REM Pause the script to see the output (optional)
pause