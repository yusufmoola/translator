#!/usr/bin/env python3
"""
macOS-optimized launcher for Quran Translator
This launcher ensures the GUI appears in the foreground on macOS
"""

import sys
import os
import subprocess
import platform

def launch_app():
    """Launch the Quran Translator with proper foreground handling"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "run_app.py")
    
    if platform.system() == "Darwin":  # macOS
        print("🍎 Launching on macOS with foreground optimization...")
        
        # Method 1: Use Python with special flags for GUI apps
        try:
            # Use pythonw if available (better for GUI apps on macOS)
            pythonw_path = subprocess.run(['which', 'pythonw'], 
                                        capture_output=True, text=True)
            if pythonw_path.returncode == 0:
                python_cmd = 'pythonw'
            else:
                python_cmd = sys.executable
            
            # Launch with proper environment
            env = os.environ.copy()
            env['PYTHONPATH'] = script_dir
            
            # Start the app
            process = subprocess.Popen([python_cmd, app_path], 
                                     env=env, 
                                     cwd=script_dir)
            
            # Give it a moment to start
            import time
            time.sleep(1)
            
            # Try to bring it to front using osascript
            try:
                subprocess.run([
                    'osascript', '-e',
                    f'tell application "System Events" to set frontmost of first process whose unix id is {process.pid} to true'
                ], check=False, capture_output=True, timeout=5)
            except:
                pass
            
            # Wait for the process to complete
            process.wait()
            
        except Exception as e:
            print(f"macOS launch failed: {e}")
            print("Falling back to standard launch...")
            # Fallback to standard method
            subprocess.run([sys.executable, app_path])
    
    else:
        # Standard launch for other platforms
        print(f"🖥️ Launching on {platform.system()}...")
        subprocess.run([sys.executable, app_path])

if __name__ == "__main__":
    launch_app()