#!/usr/bin/env python3
"""
Integrated Quran Recitation Translator
Complete application with speech recognition and verse matching
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from typing import Optional
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from arabic_speech import ArabicSpeechRecognizer
from quran_matcher import QuranMatcher
from quran_api_simple import SimpleQuranDataManager
from unified_quran_api import UnifiedQuranAPI
from config import config

class QuranTranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quran Recitation Translator")
        self.root.geometry("900x700")
        
        # Initialize components
        self.speech_recognizer = None
        self.data_manager = UnifiedQuranAPI()  # Unified API manager
        self.quran_matcher = None
        self.is_listening = False
        self.current_verse = None
        self.log_text = None  # Initialize to None for safe logging
        
        # Setup UI first so logging works
        self.setup_ui()
        
        # Then initialize data and speech recognition
        self.initialize_quran_data()
        self.setup_speech_recognition()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Quran Recitation Translator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # Control buttons
        self.listen_btn = ttk.Button(control_frame, text="Start Listening", 
                                   command=self.toggle_listening, width=15)
        self.listen_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_btn = ttk.Button(control_frame, text="Test Recognition", 
                                 command=self.test_recognition, width=15)
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.download_btn = ttk.Button(control_frame, text="Download Quran", 
                                     command=self.download_quran_data, width=15)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Show official API button only if credentials are available
        if config.has_official_api():
            self.official_btn = ttk.Button(control_frame, text="Official API", 
                                         command=self.download_official_data, width=15)
            self.official_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status indicator
        self.status_frame = ttk.Frame(control_frame)
        self.status_frame.pack(side=tk.RIGHT)
        
        ttk.Label(self.status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(self.status_frame, text="Ready", 
                                    foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Verse information frame
        info_frame = ttk.LabelFrame(main_frame, text="Current Verse", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.verse_info = ttk.Label(info_frame, text="No verse detected", 
                                  font=("Arial", 11))
        self.verse_info.pack()
        
        # Arabic text display
        arabic_frame = ttk.LabelFrame(main_frame, text="Arabic Text", padding="10")
        arabic_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.arabic_text = scrolledtext.ScrolledText(arabic_frame, height=8, width=70,
                                                   font=("Arial Unicode MS", 16),
                                                   wrap=tk.WORD, state=tk.DISABLED,
                                                   bg="#ffffff", fg="#000000",
                                                   selectbackground="#0078d4",
                                                   selectforeground="#ffffff")
        self.arabic_text.pack(fill=tk.BOTH, expand=True)
        
        # English translation display
        english_frame = ttk.LabelFrame(main_frame, text="English Translation", padding="10")
        english_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.english_text = scrolledtext.ScrolledText(english_frame, height=8, width=70,
                                                    font=("Arial", 12),
                                                    wrap=tk.WORD, state=tk.DISABLED,
                                                    bg="#ffffff", fg="#000000",
                                                    selectbackground="#0078d4",
                                                    selectforeground="#ffffff")
        self.english_text.pack(fill=tk.BOTH, expand=True)
        
        # Recognition log
        log_frame = ttk.LabelFrame(main_frame, text="Recognition Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, width=70,
                                                font=("Courier", 9),
                                                wrap=tk.WORD, state=tk.DISABLED,
                                                bg="#f8f9fa", fg="#333333",
                                                selectbackground="#0078d4",
                                                selectforeground="#ffffff")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=2)  # Arabic text gets more space
        main_frame.rowconfigure(4, weight=2)  # English text gets more space
        
    def initialize_quran_data(self):
        """Initialize Quran data and matcher"""
        try:
            # Get the best available data file
            data_file = self.data_manager.get_best_data_file()
            
            if data_file:
                self.quran_matcher = QuranMatcher(data_file)
                stats = self.data_manager.get_data_stats()
                source = stats.get('source', 'Unknown')
                self.log_message(f"Loaded Quran data: {source}")
                
                if config.has_official_api() and not stats.get('is_official', False):
                    self.log_message("💡 Official API available - click 'Official API' for premium data")
            else:
                # Fall back to sample data
                self.quran_matcher = QuranMatcher("data/sample_quran.json")
                self.log_message("Using sample data - click 'Download Quran' for complete data")
                
        except Exception as e:
            self.log_message(f"Error initializing Quran data: {e}")
    
    def setup_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            self.speech_recognizer = ArabicSpeechRecognizer(self.on_speech_recognized)
            self.log_message("Speech recognition initialized successfully")
        except Exception as e:
            self.log_message(f"Failed to initialize speech recognition: {e}")
            messagebox.showerror("Error", f"Failed to initialize speech recognition:\n{e}")
    
    def download_quran_data(self):
        """Download complete Quran data from public API"""
        def download_in_thread():
            try:
                self.download_btn.config(text="Downloading...", state="disabled")
                self.log_message("Starting Quran data download from public API...")
                
                # Download complete Quran (prefer fallback for reliability)
                success = self.data_manager.download_complete_quran(prefer_official=False)
                
                if success:
                    # Reinitialize matcher with new data
                    data_file = self.data_manager.get_best_data_file()
                    if data_file:
                        self.quran_matcher = QuranMatcher(data_file)
                        self.log_message("✓ Complete Quran data downloaded and loaded successfully!")
                        
                        # Show statistics
                        stats = self.data_manager.get_data_stats()
                        self.log_message(f"Data: {stats['chapters']} chapters, {stats['total_verses']} verses")
                        
                        messagebox.showinfo("Success", 
                                          f"Complete Quran downloaded successfully!\n"
                                          f"Source: {stats.get('source', 'Public API')}\n"
                                          f"Chapters: {stats['chapters']}\n"
                                          f"Verses: {stats['total_verses']}")
                else:
                    self.log_message("✗ Failed to download Quran data")
                    messagebox.showerror("Error", "Failed to download Quran data. Check your internet connection.")
                    
            except Exception as e:
                self.log_message(f"Error downloading Quran data: {e}")
                messagebox.showerror("Error", f"Error downloading Quran data:\n{e}")
            finally:
                self.download_btn.config(text="Download Quran", state="normal")
        
        # Run download in separate thread to avoid blocking UI
        threading.Thread(target=download_in_thread, daemon=True).start()
    
    def download_official_data(self):
        """Download data from official Quran Foundation API"""
        if not config.has_official_api():
            messagebox.showerror("Error", 
                                "Official API credentials not found.\n"
                                "Please check your .env file with API credentials.")
            return
        
        def download_in_thread():
            try:
                self.official_btn.config(text="Downloading...", state="disabled")
                self.log_message("Starting download from Official Quran Foundation API...")
                
                # Download from official API (prefer official)
                success = self.data_manager.download_complete_quran(prefer_official=True, force_refresh=True)
                
                if success:
                    # Reinitialize matcher with new data
                    data_file = self.data_manager.get_best_data_file()
                    if data_file:
                        self.quran_matcher = QuranMatcher(data_file)
                        self.log_message("✓ Quran data downloaded and loaded successfully!")
                        
                        # Show statistics
                        stats = self.data_manager.get_data_stats()
                        source = "Official API" if stats.get('is_official') else "Fallback API"
                        self.log_message(f"{source} Data: {stats['chapters']} chapters, {stats['total_verses']} verses")
                        
                        messagebox.showinfo("Success", 
                                          f"Quran data downloaded successfully!\n"
                                          f"Source: {source}\n"
                                          f"Chapters: {stats['chapters']}\n"
                                          f"Verses: {stats['total_verses']}")
                else:
                    self.log_message("✗ Failed to download Quran data")
                    messagebox.showerror("Error", "Failed to download Quran data. Check your credentials and internet connection.")
                    
            except Exception as e:
                self.log_message(f"Error downloading Quran data: {e}")
                messagebox.showerror("Error", f"Error downloading Quran data:\n{e}")
            finally:
                if hasattr(self, 'official_btn'):
                    self.official_btn.config(text="Official API", state="normal")
        
        # Run download in separate thread to avoid blocking UI
        threading.Thread(target=download_in_thread, daemon=True).start()
    
    def toggle_listening(self):
        """Start or stop listening for speech"""
        if not self.speech_recognizer:
            messagebox.showerror("Error", "Speech recognition not available")
            return
            
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Start speech recognition"""
        try:
            self.is_listening = True
            self.listen_btn.config(text="Stop Listening", style="Accent.TButton")
            self.status_label.config(text="Listening...", foreground="red")
            
            self.speech_recognizer.start_listening()
            self.log_message("Started listening for Arabic recitation...")
            
        except Exception as e:
            self.log_message(f"Error starting speech recognition: {e}")
            self.is_listening = False
            self.listen_btn.config(text="Start Listening")
            self.status_label.config(text="Error", foreground="red")
    
    def stop_listening(self):
        """Stop speech recognition"""
        try:
            self.is_listening = False
            self.listen_btn.config(text="Start Listening")
            self.status_label.config(text="Ready", foreground="green")
            
            if self.speech_recognizer:
                self.speech_recognizer.stop_listening()
            
            self.log_message("Stopped listening")
            
        except Exception as e:
            self.log_message(f"Error stopping speech recognition: {e}")
    
    def test_recognition(self):
        """Test recognition with sample text"""
        sample_texts = [
            "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            "الرَّحْمَٰنِ الرَّحِيمِ"
        ]
        
        for text in sample_texts:
            self.log_message(f"Testing with: {text}")
            self.on_speech_recognized(text)
            time.sleep(1)
    
    def on_speech_recognized(self, arabic_text: str):
        """Handle recognized Arabic speech"""
        self.log_message(f"Recognized: {arabic_text}")
        
        if not self.quran_matcher:
            self.log_message("Quran matcher not initialized")
            return
        
        # Find matching verse
        verse_info = self.quran_matcher.find_matching_verse(arabic_text)
        
        if verse_info:
            self.display_verse(verse_info)
        else:
            self.log_message("No matching verse found")
            # Still show the recognized text
            self.display_recognized_text(arabic_text)
    
    def display_verse(self, verse_info: dict):
        """Display the matched verse and its translation"""
        try:
            # Update verse info
            surah_name = verse_info.get('surah_name', f"Surah {verse_info.get('surah', '')}")
            verse_num = verse_info.get('verse', '')
            confidence = verse_info.get('confidence', 0)
            
            info_text = f"{surah_name}, Verse {verse_num}"
            if confidence > 0:
                info_text += f" (Confidence: {confidence:.1%})"
            
            self.verse_info.config(text=info_text)
            
            # Update Arabic text
            arabic = verse_info.get('arabic', '')
            self.update_text_widget(self.arabic_text, arabic)
            
            # Update English translation
            translation = verse_info.get('translation', '')
            self.update_text_widget(self.english_text, translation)
            
            self.log_message(f"Displayed: {surah_name}, Verse {verse_num}")
            
        except Exception as e:
            self.log_message(f"Error displaying verse: {e}")
    
    def display_recognized_text(self, arabic_text: str):
        """Display recognized text when no verse match is found"""
        self.verse_info.config(text="Recognized text (no verse match)")
        self.update_text_widget(self.arabic_text, arabic_text)
        self.update_text_widget(self.english_text, "No translation available")
    
    def update_text_widget(self, widget, text: str):
        """Update a text widget with new content"""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
    
    def log_message(self, message: str):
        """Add a message to the log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Always print to console
        print(log_entry.strip())
        
        # Only update GUI if log_text widget exists
        if hasattr(self, 'log_text') and self.log_text is not None:
            try:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Widget might not be ready yet, just print to console
                pass
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_listening:
            self.stop_listening()
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log_message("Quran Translator started")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = QuranTranslatorApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()