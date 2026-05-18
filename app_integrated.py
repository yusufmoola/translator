#!/usr/bin/env python3
"""
Integrated Quran Recitation Translator
Quran.Foundation API integration with bookmarks, history, collections.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
from typing import Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from arabic_speech import ArabicSpeechRecognizer
    HAS_SPEECH = True
except ImportError as _e:
    print(f"Speech recognition unavailable: {_e}")
    HAS_SPEECH = False
    ArabicSpeechRecognizer = None

from quran_matcher import QuranMatcher
from config import config
from oauth2_client import OAuth2Client
from content_api import QuranContentAPI
from user_api import QuranUserAPI


def get_resource_path(relative_path):
    """Get path to resource, works for dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


class QuranTranslatorApp:
    """Main application using tk.Text widgets for all display (macOS dark mode safe)."""

    BG = "#1e1e1e"
    FG = "#e0e0e0"
    ACCENT = "#4caf50"
    DIM = "#888888"
    ARABIC_FG = "#ffffff"
    ENGLISH_FG = "#cccccc"
    BTN_BG = "#4caf50"
    BTN_FG = "#000000"
    NAV_BG = "#2a2a2a"
    NAV_FG = "#cccccc"
    NAV_BORDER = "#4caf50"
    PANEL_BG = "#000000"
    ORANGE = "#e8a838"
    RED = "#e85555"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quran Recitation Translator")
        self.root.geometry("1000x780")
        self.root.configure(bg=self.BG)

        self.bring_to_foreground()

        # State
        self.speech_recognizer = None
        self.quran_matcher = None
        self.is_listening = False
        self.current_verse = None
        self.current_page = "translator"

        # API
        self.oauth_client = None
        self.content_api = None
        self.user_api = None
        self._init_api_clients()

        # Build UI
        self._build_ui()
        self.initialize_quran_data()
        # Speech recognition is initialized lazily on first "Start Listening" click

    def _init_api_clients(self):
        if config.has_official_api():
            self.oauth_client = OAuth2Client(
                config.client_id, config.client_secret, config.environment)
            self.content_api = QuranContentAPI(self.oauth_client)
            self.user_api = QuranUserAPI(self.oauth_client)

    def bring_to_foreground(self):
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(self.root.attributes, '-topmost', False)
            self.root.focus_force()
            import platform
            if platform.system() == "Darwin":
                try:
                    import subprocess
                    subprocess.run([
                        'osascript', '-e',
                        'tell application "System Events" to set frontmost of '
                        'first process whose unix id is {} to true'.format(os.getpid())
                    ], check=False, capture_output=True)
                except Exception:
                    pass
        except Exception:
            pass

    def _build_ui(self):
        """Build entire UI using only Text and Button widgets (Tk 8.5 dark mode safe)."""

        # Navigation bar (using buttons)
        nav = tk.Frame(self.root, bg=self.BG)
        nav.pack(fill=tk.X, padx=8, pady=(8, 0))

        pages = [("Translator", "translator"), ("Bookmarks", "bookmarks"),
                 ("History", "history"), ("Collections", "collections")]
        self.nav_buttons = {}
        for label, page in pages:
            b = tk.Button(nav, text=label, command=lambda p=page: self._show_page(p),
                          bg=self.NAV_BG, fg=self.NAV_FG, relief=tk.RIDGE,
                          font=("Arial", 11), padx=14, pady=5,
                          activebackground=self.NAV_BG, activeforeground=self.NAV_FG,
                          highlightthickness=0, borderwidth=1)
            b.pack(side=tk.LEFT, padx=(0, 2))
            self.nav_buttons[page] = b

        # Login button
        self.login_btn = tk.Button(nav, text="Login", command=self.login,
                                   bg=self.ACCENT, fg="#000000", relief=tk.FLAT,
                                   font=("Arial", 10, "bold"), padx=12, pady=4,
                                   activebackground="#4a4", activeforeground="#000",
                                   highlightthickness=0, borderwidth=0)
        self.login_btn.pack(side=tk.RIGHT)

        # Status bar at bottom (pack first so it gets reserved space)
        self.statusbar = tk.Text(self.root, height=1, font=("Courier", 10),
                                 bg="#111111", fg="#00ff00", relief=tk.FLAT,
                                 borderwidth=4, highlightthickness=0, wrap=tk.NONE)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4))
        self.statusbar.insert("1.0", "Ready")
        self.statusbar.configure(state=tk.DISABLED)

        # Page container
        self.page_frame = tk.Frame(self.root, bg=self.BG)
        self.page_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

        # Build all pages
        self.pages = {}
        self._build_translator_page()
        self._build_bookmarks_page()
        self._build_history_page()
        self._build_collections_page()

        self._show_page("translator")

    def _show_page(self, name):
        """Show a page, hide others."""
        for p, frame in self.pages.items():
            frame.pack_forget()
        self.pages[name].pack(fill=tk.BOTH, expand=True)

        for p, btn in self.nav_buttons.items():
            if p == name:
                btn.configure(bg=self.ACCENT, fg="#000000", font=("Arial", 11, "bold"),
                              relief=tk.FLAT)
            else:
                btn.configure(bg=self.NAV_BG, fg=self.NAV_FG, font=("Arial", 11),
                              relief=tk.RIDGE)
        self.current_page = name

        # Auto-refresh tab content
        if name == "bookmarks":
            self.refresh_bookmarks()
        elif name == "history":
            self.refresh_history()
        elif name == "collections":
            self.refresh_collections()

    # --- Translator Page ---

    def _build_translator_page(self):
        page = tk.Frame(self.page_frame, bg=self.BG)
        self.pages["translator"] = page

        # Action buttons row
        btn_row = tk.Frame(page, bg=self.BG)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        for text, cmd in [("Start Listening", self.toggle_listening),
                          ("Test Recognition", self.test_recognition),
                          ("Download Quran", self.download_quran_data),
                          ("Bookmark Verse", self.bookmark_current_verse)]:
            b = tk.Button(btn_row, text=text, command=cmd,
                          bg=self.BTN_BG, fg=self.BTN_FG, relief=tk.FLAT,
                          font=("Arial", 10, "bold"), padx=10, pady=3,
                          activebackground=self.BTN_BG, activeforeground=self.BTN_FG,
                          highlightthickness=0, borderwidth=0)
            b.pack(side=tk.LEFT, padx=(0, 6))

        # Store listen button reference for text updates
        self.listen_btn = btn_row.winfo_children()[0]

        # Status text (using a small Text widget - always visible)
        self.status_text = tk.Text(page, height=2, font=("Arial", 11),
                                   bg=self.PANEL_BG, fg=self.ORANGE,
                                   relief=tk.FLAT, borderwidth=6, wrap=tk.WORD,
                                   highlightthickness=0)
        self.status_text.pack(fill=tk.X, pady=(0, 6))
        self.status_text.insert("1.0", "Status: Ready\nNo verse detected")
        self.status_text.configure(state=tk.DISABLED)

        # Combined verse display - one widget guarantees both are visible
        self.verse_display = tk.Text(page, font=("Arial", 16),
                                     bg=self.PANEL_BG, fg="#ffffff",
                                     relief=tk.FLAT, borderwidth=8, wrap=tk.WORD,
                                     highlightthickness=0, spacing1=6, spacing3=6,
                                     cursor="arrow")
        self.verse_display.tag_configure("arabic", font=("Arial", 20),
                                         foreground="#ffffff", justify=tk.RIGHT,
                                         spacing3=12)
        self.verse_display.tag_configure("english", font=("Arial", 16),
                                         foreground="#ffff00")
        self.verse_display.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
        self.verse_display.insert(tk.END, "Recite or click 'Test Recognition' to begin...\n\n", "english")
        # Prevent mouse/keyboard from altering text
        self.verse_display.bind("<Key>", lambda e: "break")
        self.verse_display.bind("<Button-1>", lambda e: "break")
        self.verse_display.bind("<B1-Motion>", lambda e: "break")

        # Log area
        self._make_section_label(page, "LOG")
        self.log_text = tk.Text(page, height=2, font=("Courier", 9),
                                bg="#1a1a1a", fg=self.DIM,
                                relief=tk.FLAT, borderwidth=6, wrap=tk.WORD,
                                highlightthickness=0)
        self.log_text.pack(fill=tk.X, pady=(0, 4))
        self.log_text.configure(state=tk.DISABLED)

    def _make_section_label(self, parent, text):
        """Create a section label using a tiny Text widget (visible in dark mode)."""
        lbl = tk.Text(parent, height=1, font=("Arial", 9, "bold"),
                      bg=self.BG, fg=self.ACCENT, relief=tk.FLAT,
                      borderwidth=0, highlightthickness=0)
        lbl.pack(fill=tk.X, pady=(4, 1), anchor=tk.W)
        lbl.insert("1.0", text)
        lbl.configure(state=tk.DISABLED)

    # --- Bookmarks Page ---

    def _build_bookmarks_page(self):
        page = tk.Frame(self.page_frame, bg=self.BG)
        self.pages["bookmarks"] = page

        btn_row = tk.Frame(page, bg=self.BG)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        tk.Button(btn_row, text="Refresh", command=self.refresh_bookmarks,
                  bg=self.BTN_BG, fg=self.BTN_FG, relief=tk.FLAT,
                  font=("Arial", 10), padx=10, pady=3,
                  highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=(0, 6))
        if config.has_official_api():
            tk.Button(btn_row, text="Sync to Cloud", command=self.sync_bookmarks,
                      bg=self.ACCENT, fg="#000", relief=tk.FLAT,
                      font=("Arial", 10), padx=10, pady=3,
                      highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        self.bookmarks_display = tk.Text(page, font=("Arial", 12),
                                         bg=self.PANEL_BG, fg=self.FG,
                                         relief=tk.FLAT, borderwidth=6, wrap=tk.WORD,
                                         highlightthickness=0, spacing1=2, spacing3=2)
        self.bookmarks_display.pack(fill=tk.BOTH, expand=True)
        self.bookmarks_display.insert("1.0", "No bookmarks yet.\n\nUse 'Bookmark Verse' on the Translator page.")
        self.bookmarks_display.configure(state=tk.DISABLED)

    # --- History Page ---

    def _build_history_page(self):
        page = tk.Frame(self.page_frame, bg=self.BG)
        self.pages["history"] = page

        btn_row = tk.Frame(page, bg=self.BG)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        tk.Button(btn_row, text="Refresh", command=self.refresh_history,
                  bg=self.BTN_BG, fg=self.BTN_FG, relief=tk.FLAT,
                  font=("Arial", 10), padx=10, pady=3,
                  highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        self.history_display = tk.Text(page, font=("Arial", 12),
                                       bg=self.PANEL_BG, fg=self.FG,
                                       relief=tk.FLAT, borderwidth=6, wrap=tk.WORD,
                                       highlightthickness=0, spacing1=2, spacing3=2)
        self.history_display.pack(fill=tk.BOTH, expand=True)
        self.history_display.insert("1.0", "No reading history yet.\n\nVerses are tracked automatically as you recite.")
        self.history_display.configure(state=tk.DISABLED)

    # --- Collections Page ---

    def _build_collections_page(self):
        page = tk.Frame(self.page_frame, bg=self.BG)
        self.pages["collections"] = page

        btn_row = tk.Frame(page, bg=self.BG)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        tk.Button(btn_row, text="Refresh", command=self.refresh_collections,
                  bg=self.BTN_BG, fg=self.BTN_FG, relief=tk.FLAT,
                  font=("Arial", 10), padx=10, pady=3,
                  highlightthickness=0, borderwidth=0).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_row, text="New Collection", command=self.create_collection,
                  bg=self.ACCENT, fg="#000", relief=tk.FLAT,
                  font=("Arial", 10), padx=10, pady=3,
                  highlightthickness=0, borderwidth=0).pack(side=tk.LEFT)

        self.collections_display = tk.Text(page, font=("Arial", 12),
                                           bg=self.PANEL_BG, fg=self.FG,
                                           relief=tk.FLAT, borderwidth=6, wrap=tk.WORD,
                                           highlightthickness=0, spacing1=2, spacing3=2)
        self.collections_display.pack(fill=tk.BOTH, expand=True)
        self.collections_display.insert("1.0", "No collections yet.\n\nClick 'New Collection' to create one.")
        self.collections_display.configure(state=tk.DISABLED)

    # --- Auth ---

    def _update_login_button(self):
        if self.oauth_client and self.oauth_client.is_user_authenticated():
            self.login_btn.configure(text="Logout", command=self.logout,
                                     bg="#666666", fg="#ffffff")
        else:
            self.login_btn.configure(text="Login", command=self.login,
                                     bg=self.ACCENT, fg="#000000")

    def login(self):
        if not self.oauth_client:
            messagebox.showerror("Error", "API credentials not configured")
            return
        self.set_status("Connecting to Quran.Foundation OAuth...")
        self.log_message("Opening browser for login...")

        def on_done(success):
            self.root.after(0, self._handle_login_result, success)

        self.oauth_client.start_login_flow(
            redirect_port=config.redirect_port, callback=on_done)

    def _handle_login_result(self, success):
        if success:
            self.set_status("Authenticated - syncing user data...")
            self.log_message("Login successful!")
            self._update_login_button()
            if self.user_api:
                self.sync_bookmarks()
            self.set_status("Logged in")
        else:
            self.set_status("Login failed")
            self.log_message("Login failed")
            messagebox.showerror("Login Failed", "Could not complete login.")

    def logout(self):
        if self.oauth_client:
            self.oauth_client.logout()
            self._update_login_button()
            self.log_message("Logged out")

    # --- Data ---

    def initialize_quran_data(self):
        try:
            data_file = None

            # Prefer quran_complete.json (has full 114 surahs with translations)
            complete_file = get_resource_path(os.path.join("data", "quran_complete.json"))
            if os.path.exists(complete_file):
                data_file = complete_file
                self.log_message("Using complete Quran data (114 surahs)")

            # Fall back to official file (prelive - may lack translations)
            if not data_file:
                official_file = get_resource_path(os.path.join("data", "quran_official.json"))
                if os.path.exists(official_file):
                    data_file = official_file
                    self.log_message("Using Foundation data (limited)")

            if data_file:
                self.quran_matcher = QuranMatcher(data_file)
                self.set_status("Verse index ready")
            else:
                self.quran_matcher = QuranMatcher(get_resource_path("data/sample_quran.json"))
                self.log_message("Sample data only - click 'Download Quran'")
        except Exception as e:
            self.log_message(f"Data init error: {e}")

    def setup_speech_recognition(self):
        """Initialize speech recognition lazily (only when user starts listening)."""
        if self.speech_recognizer:
            return True
        if not HAS_SPEECH:
            self.log_message("Speech unavailable (install pyaudio)")
            return False
        try:
            self.speech_recognizer = ArabicSpeechRecognizer(self.on_speech_recognized)
            self.log_message("Speech recognition ready")
            return True
        except Exception as e:
            self.log_message(f"Speech init error: {e}")
            return False

    def download_quran_data(self):
        def download():
            try:
                self.set_status("Downloading complete Quran (114 surahs)...")
                self.log_message("Downloading Quran data...")

                from unified_quran_api import UnifiedQuranAPI
                api = UnifiedQuranAPI()
                self.set_status("Fetching from Al-Quran Cloud API (with translations)...")
                success = api.download_from_fallback_api(force_refresh=True)

                if success:
                    self.set_status("Building verse index...")
                    self.initialize_quran_data()
                    self.set_status("Download complete - 114 surahs loaded")
                    self.log_message("Download complete!")
                    self.root.after(0, lambda: messagebox.showinfo("Done", "Complete Quran downloaded (114 surahs with translations)!"))
                else:
                    self.set_status("Download failed")
                    self.log_message("Download failed")
            except Exception as e:
                self.set_status(f"Error: {e}")
                self.log_message(f"Download error: {e}")
        threading.Thread(target=download, daemon=True).start()

    # --- Speech ---

    def toggle_listening(self):
        if not self.speech_recognizer:
            self.set_status("Initializing microphone...")
            if not self.setup_speech_recognition():
                messagebox.showerror("Error", "Speech recognition not available.\nInstall: pip install pyaudio")
                self.set_status("Speech recognition unavailable")
                return
        if not self.is_listening:
            self.is_listening = True
            self.listen_btn.config(text="Stop Listening", bg=self.RED)
            self._set_status("Listening...", self.RED)
            self.set_status("Listening for Arabic recitation...")
            self.speech_recognizer.start_listening()
            self.log_message("Listening...")
        else:
            self.is_listening = False
            self.listen_btn.config(text="Start Listening", bg=self.BTN_BG)
            self._set_status("Ready", self.ACCENT)
            self.speech_recognizer.stop_listening()
            self.log_message("Stopped")

    def test_recognition(self):
        samples = ["بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                   "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                   "الرَّحْمَٰنِ الرَّحِيمِ"]
        self._run_test_sequence(samples, 0)

    def _run_test_sequence(self, samples, index):
        """Run test samples one at a time without blocking the UI."""
        if index >= len(samples):
            return
        self.on_speech_recognized(samples[index])
        self.root.after(800, self._run_test_sequence, samples, index + 1)

    def on_speech_recognized(self, arabic_text: str):
        self.set_status("Matching verse...")
        self.log_message(f"Heard: {arabic_text[:40]}")
        if not self.quran_matcher:
            return
        verse_info = self.quran_matcher.find_matching_verse(arabic_text)
        if verse_info:
            self.current_verse = verse_info
            self.display_verse(verse_info)
            self._track_reading(verse_info)
            self.set_status(f"Matched: {verse_info.get('surah_name', '')} v{verse_info.get('verse', '')}")
        else:
            self.log_message("No match found")
            self.set_status("No verse match found")
            self._display_verse_text(arabic_text, "(no match)")

    # --- Display ---

    def display_verse(self, verse_info: dict):
        surah_name = verse_info.get('surah_name', f"Surah {verse_info.get('surah', '')}")
        verse_num = verse_info.get('verse', '')
        confidence = verse_info.get('confidence', 0)

        status = f"{surah_name}, Verse {verse_num}"
        if confidence > 0:
            status += f"  ({confidence:.0%} match)"
        self._set_status(status, self.ACCENT)

        self._display_verse_text(verse_info.get('arabic', ''),
                                verse_info.get('translation', ''))

    def _set_status(self, text, color=None):
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", text)
        if color:
            self.status_text.configure(fg=color)
        self.status_text.configure(state=tk.DISABLED)

    def _set_text(self, widget, text):
        """Update any Text widget content."""
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state=tk.DISABLED)

    def _display_verse_text(self, arabic: str, english: str):
        """Update the combined verse display with arabic and english."""
        w = self.verse_display
        w.configure(state=tk.NORMAL)
        w.delete("1.0", tk.END)
        w.insert(tk.END, arabic, "arabic")
        w.insert(tk.END, "\n\n")
        w.insert(tk.END, english)
        w.see("1.0")
        w.configure(state=tk.DISABLED)
        # Also show translation in status bar
        self.set_status(f"Translation: {english}")

    # --- Bookmarks ---

    def bookmark_current_verse(self):
        if not self.current_verse:
            messagebox.showinfo("No Verse", "No verse displayed to bookmark.")
            return
        verse_key = f"{self.current_verse.get('surah', '')}:{self.current_verse.get('verse', '')}"
        surah_name = self.current_verse.get('surah_name', '')
        arabic = self.current_verse.get('arabic', '')
        translation = self.current_verse.get('translation', '')

        if self.user_api:
            added = self.user_api.add_local_bookmark(verse_key, surah_name, arabic, translation)
            if added:
                self.log_message(f"Bookmarked {verse_key}")
            else:
                self.log_message(f"{verse_key} already bookmarked")

    def refresh_bookmarks(self):
        bookmarks = []
        if self.user_api and self.oauth_client and self.oauth_client.is_user_authenticated():
            result = self.user_api.get_bookmarks()
            if result:
                bookmarks = result.get("data", result.get("bookmarks", []))
        if not bookmarks and self.user_api:
            bookmarks = self.user_api.get_local_bookmarks()

        lines = []
        if not bookmarks:
            lines.append("No bookmarks yet.\n\nUse 'Bookmark Verse' on the Translator page.")
        else:
            for i, bm in enumerate(bookmarks, 1):
                vk = bm.get("verse_key", bm.get("verseKey", "?"))
                sn = bm.get("surah_name", "")
                ar = bm.get("arabic", "")
                tr = bm.get("translation", "")
                synced = bm.get("synced", True)
                header = f"{i}. {vk}"
                if sn:
                    header += f" - {sn}"
                if not synced:
                    header += " [local]"
                lines.append(header)
                if ar:
                    lines.append(f"   {ar}")
                if tr:
                    lines.append(f"   {tr}")
                lines.append("")

        self._set_text(self.bookmarks_display, "\n".join(lines))

    def sync_bookmarks(self):
        if not self.user_api or not self.oauth_client:
            return
        if not self.oauth_client.is_user_authenticated():
            return

        def do_sync():
            self.set_status("Syncing bookmarks to Quran.Foundation...")
            result = self.user_api.sync_local_data()
            count = result.get("bookmarks", 0) + result.get("sessions", 0)
            if count > 0:
                self.log_message(f"Synced {count} items")
            self.set_status(f"Sync complete ({count} items)")
            self.root.after(0, self.refresh_bookmarks)

        threading.Thread(target=do_sync, daemon=True).start()

    # --- History ---

    def _track_reading(self, verse_info: dict):
        if not self.user_api:
            return
        ch = verse_info.get('surah', 0)
        v = verse_info.get('verse', 0)
        sn = verse_info.get('surah_name', '')
        if not ch or not v:
            return
        # Always store locally (API sync is best-effort)
        self.user_api.add_local_reading_session(ch, v, v, sn)

    def refresh_history(self):
        sessions = []
        if self.user_api and self.oauth_client and self.oauth_client.is_user_authenticated():
            result = self.user_api.get_reading_sessions()
            if result:
                sessions = result.get("data", result.get("reading_sessions", []))
        if not sessions and self.user_api:
            sessions = self.user_api.get_local_reading_sessions()

        lines = []
        if not sessions:
            lines.append("No reading history yet.\n\nVerses are tracked automatically.")
        else:
            for s in reversed(sessions[-50:]):
                ch = s.get("chapter_number", s.get("chapterNumber", "?"))
                vf = s.get("verse_from", s.get("verseFrom", "?"))
                vt = s.get("verse_to", s.get("verseTo", "?"))
                sn = s.get("surah_name", "")
                ts = s.get("timestamp", s.get("created_at", ""))
                line = sn if sn else f"Surah {ch}"
                line += f", Verse {vf}" if vf == vt else f", Verses {vf}-{vt}"
                if ts:
                    line += f"  |  {ts}"
                if not s.get("synced", True):
                    line += "  [local]"
                lines.append(line)

        self._set_text(self.history_display, "\n".join(lines))

    # --- Collections ---

    def create_collection(self):
        name = simpledialog.askstring("New Collection", "Collection name:")
        if not name:
            return
        desc = simpledialog.askstring("New Collection", "Description (optional):", initialvalue="")

        if self.user_api and self.oauth_client and self.oauth_client.is_user_authenticated():
            result = self.user_api.create_collection(name, desc or "")
            if result:
                self.log_message(f"Created: {name}")
                self.refresh_collections()
                return

        if self.user_api:
            self.user_api._local_data.setdefault("collections", []).append({
                "name": name, "description": desc or "",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "items": [], "synced": False})
            self.user_api._save_local_data()
        self.log_message(f"Created: {name} (local)")
        self.refresh_collections()

    def refresh_collections(self):
        collections = []
        if self.user_api and self.oauth_client and self.oauth_client.is_user_authenticated():
            result = self.user_api.get_collections()
            if result:
                collections = result.get("data", result.get("collections", []))
        if not collections and self.user_api:
            collections = self.user_api.get_local_collections()

        lines = []
        if not collections:
            lines.append("No collections yet.\n\nClick 'New Collection' to create one.")
        else:
            for i, col in enumerate(collections, 1):
                name = col.get("name", "Untitled")
                desc = col.get("description", "")
                synced = col.get("synced", True)
                header = f"{i}. {name}"
                if not synced:
                    header += " [local]"
                lines.append(header)
                if desc:
                    lines.append(f"   {desc}")
                lines.append("")

        self._set_text(self.collections_display, "\n".join(lines))

    # --- Logging ---

    def set_status(self, text: str):
        """Update the bottom status bar."""
        try:
            self.statusbar.configure(state=tk.NORMAL)
            self.statusbar.delete("1.0", tk.END)
            self.statusbar.insert("1.0", text)
            self.statusbar.configure(state=tk.DISABLED)
            self.root.update_idletasks()
        except (tk.TclError, AttributeError):
            pass

    def log_message(self, message: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {message}\n"
        print(entry.strip())
        self.set_status(message)
        if hasattr(self, 'log_text') and self.log_text:
            try:
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, entry)
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
            except tk.TclError:
                pass

    # --- Lifecycle ---

    def on_closing(self):
        if self.is_listening:
            self.stop_listening()
        self.root.destroy()

    def stop_listening(self):
        self.is_listening = False
        if self.speech_recognizer:
            self.speech_recognizer.stop_listening()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log_message("Quran Translator started")
        self.root.after(100, self.bring_to_foreground)
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = QuranTranslatorApp()
        app.run()
    except Exception as e:
        print(f"Failed to start: {e}")
        import traceback
        traceback.print_exc()
