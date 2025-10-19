#!/bin/bash
# macOS-optimized launcher for Quran Translator

echo "🎤 Starting Quran Recitation Translator..."

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Optimizing for macOS..."
    
    # Try to use pythonw for better GUI support
    if command -v pythonw &> /dev/null; then
        PYTHON_CMD="pythonw"
    else
        PYTHON_CMD="python3"
    fi
    
    # Launch the app in the background and get its PID
    cd "$DIR"
    $PYTHON_CMD run_app.py &
    APP_PID=$!
    
    # Wait a moment for the app to start
    sleep 2
    
    # Try to bring the app to the foreground using osascript
    osascript -e "tell application \"System Events\" to set frontmost of first process whose unix id is $APP_PID to true" 2>/dev/null || true
    
    # Wait for the app to finish
    wait $APP_PID
    
else
    # Standard launch for other platforms
    echo "🖥️ Launching on $OSTYPE..."
    cd "$DIR"
    python3 run_app.py
fi

echo "✅ Quran Translator closed."