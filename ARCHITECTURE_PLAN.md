# Multi-Platform Architecture Plan

## Goal

Refactor into a shared core library with thin platform-specific UI layers, enabling Mac app, web app, and future mobile apps from one codebase.

## Proposed Structure

```
translator/
├── core/                      # Shared logic — no UI, no platform deps
│   ├── __init__.py
│   ├── matcher.py             # QuranMatcher (extracted as-is)
│   ├── normalizer.py          # Arabic text normalization
│   ├── data_manager.py        # Load/download Quran JSON
│   ├── user_data.py           # Bookmarks, history, collections (local storage)
│   ├── oauth_client.py        # OAuth2 + token management
│   ├── content_api.py         # Quran.Foundation Content API
│   ├── user_api.py            # Quran.Foundation User API
│   └── config.py              # Config loader
├── clients/
│   ├── mac/                   # Tkinter desktop app
│   │   ├── app.py             # Thin UI importing from core/
│   │   └── speech.py          # pyaudio + SpeechRecognition (mac-specific)
│   ├── web/
│   │   ├── backend/           # FastAPI server wrapping core/
│   │   │   ├── server.py      # REST + WebSocket endpoints
│   │   │   └── requirements.txt
│   │   └── frontend/          # Static JS app
│   │       ├── index.html
│   │       ├── app.js         # Web Speech API + UI
│   │       └── matcher.js     # (optional) client-side matching for zero-latency
│   └── mobile/                # Future — React Native or Flutter calling backend
├── data/                      # Quran JSON (shared across clients)
└── infra/                     # CDK/Terraform for AWS deployment
```

## How It Works Per Platform

| Platform | Speech input | Matching | User features |
|----------|-------------|----------|---------------|
| Mac | `pyaudio` → Google Speech API (existing) | Direct Python import from `core/` | Direct import from `core/` |
| Web | Browser Web Speech API (free, client-side) | Call backend via WebSocket, *or* use `matcher.js` client-side | Backend proxies OAuth + calls `core/` |
| Mobile (future) | Platform speech APIs | Call backend REST endpoint | Same backend |

## Key Design Decisions

1. **Speech stays platform-specific** — each client handles audio capture natively (pyaudio on Mac, Web Speech API in browser, platform APIs on mobile). The core only receives recognized Arabic text as a string.

2. **Backend is optional for Mac** — the Mac app imports `core/` directly with zero network overhead. The web/mobile clients hit the FastAPI backend which wraps the same `core/`.

3. **Matching can run in two modes** — server-side (Python, consistent across all clients) or client-side in the browser (port the normalizer + matcher to JS for offline/low-latency). Ship both and let the frontend fall back to client-side if the server is unreachable.

4. **One Quran data file** — `data/quran_complete.json` is shared. The backend serves it to web/mobile clients (cached at CDN edge). Mac reads it from disk.

## Refactoring Steps

### Phase 1: Extract Core Library
- Move `quran_matcher.py`, `config.py`, `oauth2_client.py`, `content_api.py`, `user_api.py`, `unified_quran_api.py` into `core/`
- Split `quran_matcher.py` into `matcher.py` (matching logic) and `normalizer.py` (Arabic text normalization)
- Strip the Tkinter UI out of `app_integrated.py` → becomes `clients/mac/app.py` importing from `core/`
- `arabic_speech.py` → `clients/mac/speech.py` (already mac-specific with pyobjc deps)
- Verify Mac app still works against the new `core/` package

### Phase 2: Web Backend
- FastAPI server exposing:
  - `POST /match` — accepts Arabic text, returns matched verse + translation
  - `WS /listen` — WebSocket for streaming recognition results
  - `GET /quran-data` — serve Quran JSON (or let CDN handle it)
  - OAuth proxy endpoints (token exchange — client_secret can't live in browser)
  - User data CRUD (bookmarks, history, collections)

### Phase 3: Web Frontend
- Static HTML/JS app (or React if complexity warrants it)
- Web Speech API for in-browser Arabic speech recognition (`lang: 'ar-SA'`)
- Dark theme UI matching the Mac app aesthetic
- Service Worker for offline support (cache Quran JSON + app shell)

### Phase 4: AWS Deployment
- **Minimal (static, no user features):**
  - S3 (static site) → CloudFront (CDN) — cost: ~$1-5/month
- **Full (with user features):**
  - S3 + CloudFront (frontend)
  - API Gateway + Lambda or Fargate (backend)
  - DynamoDB (bookmarks, history, collections)
  - Cognito or Quran.Foundation OAuth
  - Cost: ~$5-20/month

### Phase 5 (Future): Mobile
- React Native or Flutter app calling the same backend
- Platform-native speech APIs feeding recognized text to the shared matching endpoint

## Effort Estimates

| Task | Effort |
|------|--------|
| Phase 1: Extract core, verify Mac app | 1-2 days |
| Phase 2: FastAPI backend | 1 day |
| Phase 3: Web frontend + Web Speech API | 2-3 days |
| Phase 4: AWS infra (CDK) | 0.5-1 day |
| Total MVP (web + Mac working) | ~5-7 days |

## Notes

- The existing code is already fairly modular — the refactor is mostly moving files and adjusting imports.
- Web Speech API works in Chrome, Safari, and Edge. Firefox has partial support. For unsupported browsers, could fall back to a "paste Arabic text" mode.
- The Quran JSON is ~6MB — acceptable for browser caching via Service Worker / CDN.
- If Quran.Foundation OAuth is too complex for the web version, can use a simpler auth system (Cognito, or even just local browser storage for bookmarks) and add sync later.
