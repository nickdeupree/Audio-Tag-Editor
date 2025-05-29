import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
main_script = os.path.join(current_dir, "main.py")

# Run PyInstaller with proper arguments
PyInstaller.__main__.run([
    '--onefile',                    # Create a single executable file
    '--windowed',                   # Hide console window (for GUI apps)
    '--name=AudioTagEditor',        # Name of the executable
    '--icon=icon.ico',             # Add icon if you have one (optional)
    '--distpath=dist',             # Output directory
    '--workpath=build',            # Temporary build directory
    '--clean',                     # Clean cache and remove temporary files
    main_script
])