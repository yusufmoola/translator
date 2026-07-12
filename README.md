# Quran Recitation Translator

A real-time speech recognition app that listens to Quran recitation and displays the Arabic text with its English translation. Built with the Quran.Foundation API for the 2026 Hackathon.

## Features

- **Real-time Speech Recognition** — captures Arabic recitation via microphone (Google Speech API)
- **Intelligent Verse Matching** — fuzzy matching with diacritic normalization and partial recognition
- **Quran.Foundation Content API** — fetches verses, chapters, and translations from the official API
- **OAuth2 Login** — Quran.Foundation user authentication with PKCE
- **Bookmarks** — save verses locally or sync to the cloud when logged in
- **Reading History** — auto-tracks recited verses
- **Collections** — organize saved verses into groups
- **Offline Fallback** — works without internet using cached data (feature-flagged)

## Requirements

- macOS
- Python 3.13+ (Homebrew) with Tk 9.0
- Microphone access
- Internet connection

## Quick Start

```bash
# 1. Install system deps
brew install python@3.13 python-tk@3.13 portaudio

# 2. Create venv
python3.13 -m venv .venv
source .venv/bin/activate

# 3. Install Python deps
pip install requests SpeechRecognition pyaudio

# 4. Configure API credentials
cp .env.example .env
# Edit .env with your Quran.Foundation client_id and client_secret

# 5. Run
python app_integrated.py
```

## Configuration

Copy `.env.example` to `.env` and add your credentials from [Quran.Foundation Request Access](https://api-docs.quran.foundation/request-access/):

```env
QURAN_CLIENT_ID=your_client_id
QURAN_CLIENT_SECRET=your_client_secret
QURAN_ENVIRONMENT=prelive
OAUTH_REDIRECT_PORT=8765

# Feature flags
USE_FOUNDATION_CONTENT_API=true
USE_OFFLINE_FALLBACK=true
```

Register `http://localhost:8765/callback` as your redirect URI.

## Hackathon Technical Checklist

| Requirement | Implementation |
|---|---|
| Content API | `content_api.py` — `/content/api/v4/chapters`, `/verses/by_chapter`, `/verses/by_key` |
| User-Related API | `user_api.py` — bookmarks, collections, reading sessions via `/auth/v1/` |
| OAuth integration | `oauth2_client.py` — authorization_code + PKCE flow with browser redirect |

## Architecture

```
├── app_integrated.py      # Main GUI application (Tkinter)
├── oauth2_client.py       # OAuth2 client (client_credentials + auth_code/PKCE)
├── content_api.py         # Quran.Foundation Content API v4 client
├── user_api.py            # User API (bookmarks, collections, reading sessions)
├── arabic_speech.py       # Microphone capture + Google Speech Recognition
├── quran_matcher.py       # Arabic text normalization + fuzzy verse matching
├── config.py              # Configuration and feature flags
├── unified_quran_api.py   # Offline fallback (Al-Quran Cloud API)
├── data/
│   ├── quran_official.json   # Downloaded from Foundation API
│   └── quran_complete.json   # Offline fallback data
├── .env                   # API credentials (not committed)
└── .env.example           # Template
```

## How It Works

1. **Speech** — microphone audio → Google Speech API (Arabic `ar-SA`) → recognized text
2. **Matching** — normalized text → fuzzy match against verse index (exact → sequence → substring → word overlap)
3. **Display** — matched verse shown with Arabic, English translation, surah/ayah info
4. **Sync** — bookmarks and history sync to Quran.Foundation when logged in, or stored locally

## Feature Flags

Set `USE_FOUNDATION_CONTENT_API=false` in `.env` to use the offline Al-Quran Cloud data instead of the Foundation API. The old code path is preserved and toggleable.

## Roadmap: Multi-Platform

The app is being refactored into a shared core library with thin platform-specific UI layers. See [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md) for full details.

- **Phase 1** — Extract core library (matcher, normalizer, APIs, config), verify Mac app still works
- **Phase 2** — Web backend (FastAPI with REST + WebSocket endpoints, OAuth proxy)
- **Phase 3** — Web frontend (Web Speech API for in-browser Arabic recognition, static JS app)
- **Phase 4** — AWS deployment (S3 + CloudFront for static assets, API Gateway + Lambda for backend)
- **Phase 5** — Mobile apps (React Native or Flutter, calling the same backend)

## License

For educational and religious purposes. Quran text sourced from Quran.Foundation under their developer terms.
