#!/usr/bin/env python3
"""
Setup script for Quran Translator
Handles installation and dependency management
"""

import subprocess
import sys
import os
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_system_dependencies():
    """Install system-level dependencies"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("Installing macOS dependencies...")
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            print("✓ Homebrew detected")
            
            # Install portaudio for pyaudio
            print("Installing portaudio...")
            subprocess.run(["brew", "install", "portaudio"], check=True)
            print("✓ portaudio installed")
            
        except subprocess.CalledProcessError:
            print("Warning: Homebrew not found. Please install portaudio manually:")
            print("1. Install Homebrew: https://brew.sh/")
            print("2. Run: brew install portaudio")
            
    elif system == "Linux":
        print("For Linux, please install these packages:")
        print("Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio")
        print("CentOS/RHEL: sudo yum install portaudio-devel")
        
    else:
        print(f"Unsupported system: {system}")

def install_python_dependencies():
    """Install Python packages"""
    print("Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✓ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}")
        
        # Try alternative pyaudio installation for macOS
        if platform.system() == "Darwin":
            print("Trying alternative pyaudio installation...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--global-option=build_ext",
                    "--global-option=-I/opt/homebrew/include",
                    "--global-option=-L/opt/homebrew/lib",
                    "pyaudio"
                ], check=True)
                print("✓ pyaudio installed with custom flags")
            except subprocess.CalledProcessError:
                print("Failed to install pyaudio. Please install manually.")

def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs", "recordings"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def test_installation():
    """Test if installation was successful"""
    print("\nTesting installation...")
    
    try:
        import speech_recognition
        print("✓ SpeechRecognition imported successfully")
    except ImportError:
        print("✗ SpeechRecognition import failed")
        return False
    
    try:
        import pyaudio
        print("✓ PyAudio imported successfully")
    except ImportError:
        print("✗ PyAudio import failed")
        return False
    
    try:
        import tkinter
        print("✓ Tkinter imported successfully")
    except ImportError:
        print("✗ Tkinter import failed")
        return False
    
    return True

def main():
    """Main setup function"""
    print("Quran Translator Setup")
    print("=" * 30)
    
    # Check Python version
    check_python_version()
    
    # Install system dependencies
    install_system_dependencies()
    
    # Create directories
    create_directories()
    
    # Install Python dependencies
    install_python_dependencies()
    
    # Test installation
    if test_installation():
        print("\n✓ Setup completed successfully!")
        print("\nTo run the application:")
        print("python app_integrated.py")
    else:
        print("\n✗ Setup completed with errors")
        print("Please check the error messages above and resolve any issues")

if __name__ == "__main__":
    main()