"""
Speech Recognition Module for Quran Translator
Handles real-time audio capture and Arabic speech recognition
"""

import pyaudio
import wave
import threading
import queue
import time
from typing import Optional, Callable
import speech_recognition as sr

class ArabicSpeechRecognizer:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Configure recognizer for Arabic
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Calibrate microphone
        self.calibrate_microphone()
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                print("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print("Microphone calibrated")
        except Exception as e:
            print(f"Microphone calibration failed: {e}")
    
    def start_listening(self):
        """Start continuous listening"""
        if self.is_listening:
            return
            
        self.is_listening = True
        
        # Start background listening
        self.stop_listening_func = self.recognizer.listen_in_background(
            self.microphone, 
            self.audio_callback,
            phrase_time_limit=5
        )
        
        print("Started listening for Arabic speech...")
    
    def stop_listening(self):
        """Stop listening"""
        if not self.is_listening:
            return
            
        self.is_listening = False
        
        if hasattr(self, 'stop_listening_func'):
            self.stop_listening_func(wait_for_stop=False)
        
        print("Stopped listening")
    
    def audio_callback(self, recognizer, audio):
        """Callback for when audio is captured"""
        if not self.is_listening:
            return
            
        try:
            # Try Google Speech Recognition with Arabic
            text = recognizer.recognize_google(audio, language='ar-SA')
            print(f"Recognized: {text}")
            
            # Call the callback with recognized text
            if self.callback:
                self.callback(text)
                
        except sr.UnknownValueError:
            # Could not understand audio
            pass
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
        except Exception as e:
            print(f"Unexpected error in speech recognition: {e}")
    
    def recognize_from_file(self, audio_file_path: str) -> Optional[str]:
        """Recognize speech from an audio file"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='ar-SA')
                return text
        except Exception as e:
            print(f"File recognition error: {e}")
            return None

class AudioRecorder:
    """Simple audio recorder for testing purposes"""
    
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.recording = False
        self.frames = []
    
    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.frames = []
        
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("Recording started...")
        
        # Record in separate thread
        self.record_thread = threading.Thread(target=self._record_loop)
        self.record_thread.start()
    
    def stop_recording(self, filename: str = "recording.wav"):
        """Stop recording and save to file"""
        self.recording = False
        
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        
        # Save recording
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        print(f"Recording saved as {filename}")
        return filename
    
    def _record_loop(self):
        """Internal recording loop"""
        while self.recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break