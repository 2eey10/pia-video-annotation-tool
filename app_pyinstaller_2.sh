#!/bin/bash

# Run PyInstaller to convert the Python script to an executable file
pyinstaller --onefile --windowed --name=PIA_Video_Annotation_Tool \
            --add-data "icons:icons" \
            main.py

# Pause the script to see the output (optional)
read -p "Press any key to continue..."