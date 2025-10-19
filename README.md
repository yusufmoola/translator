# Quran Recitation Translator

A real-time speech recognition application that listens to Quran recitation and displays the corresponding English translation.

## Features

- **Real-time Speech Recognition**: Captures Arabic speech using your microphone
- **Verse Matching**: Intelligently matches recognized Arabic text to Quran verses
- **Live Translation Display**: Shows Arabic text and English translation side-by-side
- **Confidence Scoring**: Displays matching confidence for recognized verses
- **Recognition Log**: Tracks all recognition attempts and results

## Requirements

- macOS (with plans for iOS support)
- Python 3.8+
- Microphone access
- Internet connection (for Google Speech Recognition)

## Installation

1. **Clone or download the project**
   ```bash
   cd quran_translator
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies (macOS)**
   ```bash
   # Install portaudio for pyaudio
   brew install portaudio
   
   # If you encounter issues with pyaudio, try:
   pip install --global-option='build_ext' --global-option='-I/opt/homebrew/include' --global-option='-L/opt/homebrew/lib' pyaudio
   ```

4. **Download Complete Quran Data**
   ```bash
   # Option 1: Use the standalone downloader
   python download_quran.py
   
   # Option 2: Use the app's download button
   # Run the app and click "Download Quran"
   ```

## Usage

### Running the Application

**Easy Start (Recommended):**
```bash
python run_app.py
```

**Manual Start:**
```bash
python app_integrated.py
```

### Using the Interface

1. **Start Listening**: Click "Start Listening" to begin speech recognition
2. **Recite Quran**: Speak Arabic verses clearly into your microphone
3. **View Results**: The app will display:
   - Recognized Arabic text
   - Matching verse information (Surah and Ayah number)
   - English translation
   - Confidence score

4. **Test Mode**: Use "Test Recognition" to try with sample verses

### Tips for Best Results

- **Clear Audio**: Speak clearly and minimize background noise
- **Proper Pronunciation**: Traditional Arabic pronunciation works best
- **Good Microphone**: Use a quality microphone for better recognition
- **Internet Connection**: Required for Google Speech Recognition API

## Project Structure

```
quran_translator/
├── run_app.py            # Easy startup script (RECOMMENDED)
├── app_integrated.py     # Main application with GUI
├── arabic_speech.py      # Speech recognition module
├── quran_matcher.py      # Verse matching algorithms
├── quran_api_simple.py   # Simple Quran API integration
├── quran_api.py          # Advanced API (fallback)
├── download_quran.py     # Standalone data downloader
├── test_app.py           # Component testing script
├── main.py               # Basic application framework
├── setup.py              # Installation script
├── requirements.txt      # Python dependencies
├── data/
│   ├── sample_quran.json    # Sample Quran data (fallback)
│   ├── quran_complete.json  # Complete Quran (downloaded)
│   └── translations.json    # Available translations
└── README.md            # This file
```

## Technical Details

### Speech Recognition
- Uses Google Speech Recognition API
- Configured for Arabic language (ar-SA)
- Continuous listening with background processing
- Automatic noise calibration

### Verse Matching
- Text normalization (removes diacritics, normalizes characters)
- Fuzzy matching algorithm with confidence scoring
- Word-level and sequence-level similarity comparison
- Supports partial verse recognition

### Quran Foundation API Integration
The app uses the [Quran Foundation API](https://api-docs.quran.foundation/) to fetch:
- Complete Quran text in Arabic (Uthmani script)
- English translations (default: Dr. Mustafa Khattab, the Clear Quran)
- Verse metadata (Juz, Hizb, page numbers)
- Multiple translation options

### Data Format
The Quran data is stored in JSON format with this structure:
```json
{
  "source": "Quran Foundation API",
  "translation_id": 131,
  "surahs": [
    {
      "number": 1,
      "name": "Al-Fatihah",
      "name_arabic": "الفاتحة",
      "revelation_place": "makkah",
      "verses_count": 7,
      "verses": [
        {
          "number": 1,
          "verse_key": "1:1",
          "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
          "translation": "In the name of Allah...",
          "juz": 1,
          "page": 1
        }
      ]
    }
  ]
}
```

## Extending the Application

### Adding More Quran Data
1. Expand `data/sample_quran.json` with complete Quran text
2. Include multiple translation options
3. Add transliteration support

### Improving Recognition
1. Train custom Arabic speech models
2. Add offline recognition capabilities
3. Implement voice activity detection

### iOS Development
The current Python/Tkinter implementation can be ported to iOS using:
- **Kivy**: Cross-platform Python framework
- **BeeWare**: Native iOS apps from Python
- **Native iOS**: Swift with Speech Framework

## Troubleshooting

### Common Issues

1. **Microphone Permission**
   - Grant microphone access when prompted
   - Check System Preferences > Security & Privacy > Microphone

2. **PyAudio Installation**
   ```bash
   # On macOS with Apple Silicon
   brew install portaudio
   pip install pyaudio
   ```

3. **Speech Recognition Errors**
   - Check internet connection
   - Verify microphone is working
   - Try speaking more clearly

4. **No Verse Matches**
   - Current sample data is limited
   - Recognition may not be perfect
   - Try with Al-Fatihah verses for testing

## Future Enhancements

- [ ] Complete Quran database integration
- [ ] Multiple translation languages
- [ ] Offline speech recognition
- [ ] iOS app development
- [ ] Audio recording and playback
- [ ] Verse bookmarking and history
- [ ] Custom reciter voice training
- [ ] Tajweed analysis and feedback

## License

This project is for educational and religious purposes. Please ensure proper attribution when using Quran text and translations.

## Contributing

Contributions are welcome! Please focus on:
- Improving Arabic speech recognition accuracy
- Adding more comprehensive Quran data
- Enhancing the user interface
- iOS development support