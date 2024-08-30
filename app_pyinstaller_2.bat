@echo off

REM Run PyInstaller to convert the Python script to an .exe file
pyinstaller --onefile --windowed --name=PIA_Video_Annotation_Tool ^
            --add-data "icons;icons" ^
            main.py

REM Pause the script to see the output (optional)
pause
