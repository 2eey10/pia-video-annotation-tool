from cx_Freeze import setup, Executable
import os

# Set the path to the VLC installation directory
VLC_DIR = r'C:\Program Files\VideoLAN\VLC'

# List of binaries to include
binaries = [
    (os.path.join(VLC_DIR, 'libvlc.dll'), '.'),
    (os.path.join(VLC_DIR, 'libvlccore.dll'), '.'),
    (os.path.join(VLC_DIR, 'axvlc.dll'), '.'),
    (os.path.join(VLC_DIR, 'npvlc.dll'), '.'),
]

# Define the build options
build_exe_options = {
    'packages': [],  # Add any additional packages here if needed
    'excludes': [],  # Add any modules to exclude if needed
    'include_files': binaries,
}

# Define the setup
setup(
    name='PIA_Video_Annotation_Tool',
    version='0.1',
    description='A tool for video annotation.',
    options={'build_exe': build_exe_options},
    executables=[Executable('main.py', base=None)],  # Use 'base="Win32GUI"' for GUI applications
)
