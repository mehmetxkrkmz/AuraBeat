import os
import subprocess
import sys
import platform

def build_app():
    print(f"Building AuraBeat for {platform.system()}...")
    
    separator = ";" if os.name == "nt" else ":"
    
    command = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AuraBeat",
        "--windowed",          # Hide console window
        "--noconfirm",         # Overwrite existing build
        "--add-data", f"src{separator}src",  # Include all source files (icons, UI, etc)
        "main.py"
    ]
    
    try:
        subprocess.run(command, check=True)
        print("\n" + "="*50)
        print("✅ Build Completed Successfully!")
        print(f"Executable is located in the 'dist/AuraBeat' folder.")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print("\n❌ Build failed!")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    build_app()
