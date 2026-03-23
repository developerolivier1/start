#!/usr/bin/env python3
"""
Voice Assistant for Windows - Fixed Audio Visualization Version
Fixed version with better error handling and compatibility.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
import pyttsx3
import sys
from datetime import datetime
import threading

from voice_assistant_core import CommandDispatch, VoiceCommandEngine
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Ensure TkAgg backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque

# Try to import pyaudio with error handling
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. Audio visualization will be disabled.")

class AudioVisualizerFixed:
    """Fixed audio visualization component with better error handling"""
    
    def __init__(self, parent):
        self.parent = parent
        self.is_recording = False
        self.audio_data = deque(maxlen=1024)
        self.volume_history = deque(maxlen=50)
        self.speech_detected = False
        self.visualization_enabled = PYAUDIO_AVAILABLE
        
        if not self.visualization_enabled:
            self.create_fallback_display(parent)
            return
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Initialize PyAudio with error handling
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = None
            self.setup_plots()
        except Exception as e:
            print(f"Error initializing audio: {e}")
            self.visualization_enabled = False
            self.create_fallback_display(parent)
        
    def create_fallback_display(self, parent):
        """Create fallback display when audio visualization is not available"""
        fallback_frame = tk.Frame(parent, bg='#1e1e1e', height=200)
        fallback_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(fallback_frame, 
                text="Audio Visualization Unavailable", 
                font=("Arial", 16, "bold"),
                bg='#1e1e1e', fg='#ff0000').pack(pady=20)
        
        tk.Label(fallback_frame, 
                text="Please install PyAudio: pip install pyaudio", 
                font=("Arial", 12),
                bg='#1e1e1e', fg='#ffff00').pack(pady=10)
        
        tk.Label(fallback_frame, 
                text="Voice commands will still work without visualization.", 
                font=("Arial", 10),
                bg='#1e1e1e', fg='#00ff00').pack(pady=10)
        
    def setup_plots(self):
        """Setup matplotlib plots with error handling"""
        try:
            # Create figure with subplots
            self.fig = Figure(figsize=(10, 6), facecolor='#1e1e1e')
            
            # Waveform plot
            self.ax_waveform = self.fig.add_subplot(311, facecolor='#000000')
            self.ax_waveform.set_title('Audio Waveform', color='#00ff00')
            self.ax_waveform.set_xlabel('Samples', color='#00ff00')
            self.ax_waveform.set_ylabel('Amplitude', color='#00ff00')
            self.ax_waveform.tick_params(colors='#00ff00')
            self.waveform_line, = self.ax_waveform.plot([], [], 'g-', linewidth=1)
            self.ax_waveform.set_xlim(0, self.CHUNK)
            self.ax_waveform.set_ylim(-32768, 32767)
            
            # Volume meter plot
            self.ax_volume = self.fig.add_subplot(312, facecolor='#000000')
            self.ax_volume.set_title('Volume Level', color='#00ff00')
            self.ax_volume.set_xlabel('Time', color='#00ff00')
            self.ax_volume.set_ylabel('Volume (dB)', color='#00ff00')
            self.ax_volume.tick_params(colors='#00ff00')
            self.volume_line, = self.ax_volume.plot([], [], 'b-', linewidth=2)
            self.threshold_line = self.ax_volume.axhline(y=30, color='r', linestyle='--', label='Speech Threshold')
            self.ax_volume.set_xlim(0, 50)
            self.ax_volume.set_ylim(0, 100)
            self.ax_volume.legend(loc='upper right', facecolor='#000000', edgecolor='#00ff00', labelcolor='#00ff00')
            
            # Frequency spectrum plot
            self.ax_spectrum = self.fig.add_subplot(313, facecolor='#000000')
            self.ax_spectrum.set_title('Frequency Spectrum', color='#00ff00')
            self.ax_spectrum.set_xlabel('Frequency (Hz)', color='#00ff00')
            self.ax_spectrum.set_ylabel('Magnitude', color='#00ff00')
            self.ax_spectrum.tick_params(colors='#00ff00')
            self.spectrum_line, = self.ax_spectrum.plot([], [], 'r-', linewidth=1)
            self.ax_spectrum.set_xlim(0, 5000)
            self.ax_spectrum.set_ylim(0, 1000)
            
            self.fig.tight_layout()
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error setting up plots: {e}")
            self.visualization_enabled = False
            self.create_fallback_display(self.parent)
        
    def start_recording(self):
        """Start audio recording for visualization"""
        if not self.visualization_enabled:
            return
            
        try:
            if not self.is_recording:
                self.is_recording = True
                self.stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK,
                    stream_callback=self.audio_callback
                )
                self.stream.start_stream()
                
                # Start animation
                self.ani = FigureCanvasTkAgg._tkcanvas.after(50, self.update_plots)
                
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
                
    def stop_recording(self):
        """Stop audio recording"""
        if not self.visualization_enabled:
            return
            
        try:
            if self.is_recording:
                self.is_recording = False
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    
        except Exception as e:
            print(f"Error stopping recording: {e}")
                
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback with error handling"""
        if self.is_recording and self.visualization_enabled:
            try:
                # Convert audio data to numpy array
                audio_array = np.frombuffer(in_data, dtype=np.int16)
                self.audio_data.extend(audio_array)
                
                # Calculate volume
                volume = np.sqrt(np.mean(audio_array**2))
                volume_db = 20 * np.log10(volume + 1e-10)  # Add small value to avoid log(0)
                volume_db = max(0, volume_db + 50)  # Normalize to 0-100 range
                self.volume_history.append(volume_db)
                
                # Speech detection
                self.speech_detected = volume_db > 30
                
            except Exception as e:
                print(f"Audio callback error: {e}")
                
        return (in_data, pyaudio.paContinue)
    
    def update_plots(self):
        """Update matplotlib plots with error handling"""
        if not self.visualization_enabled or not self.is_recording:
            return
            
        try:
            # Update waveform
            if len(self.audio_data) > 0:
                waveform_data = list(self.audio_data)
                self.waveform_line.set_data(range(len(waveform_data)), waveform_data)
                
                # Change background color based on speech detection
                if self.speech_detected:
                    self.ax_waveform.set_facecolor('#003300')
                else:
                    self.ax_waveform.set_facecolor('#000000')
            
            # Update volume meter
            if len(self.volume_history) > 0:
                volume_data = list(self.volume_history)
                self.volume_line.set_data(range(len(volume_data)), volume_data)
            
            # Update frequency spectrum
            if len(self.audio_data) >= self.CHUNK:
                # Get last chunk of audio data
                audio_chunk = np.array(list(self.audio_data)[-self.CHUNK:])
                
                # Apply FFT
                fft_data = np.fft.fft(audio_chunk)
                fft_magnitude = np.abs(fft_data[:len(fft_data)//2])
                
                # Frequency bins
                freq_bins = np.fft.fftfreq(len(audio_chunk), 1/self.RATE)[:len(fft_data)//2]
                
                # Limit to 5kHz
                freq_limit = 5000
                freq_mask = freq_bins < freq_limit
                freq_bins = freq_bins[freq_mask]
                fft_magnitude = fft_magnitude[freq_mask]
                
                self.spectrum_line.set_data(freq_bins, fft_magnitude)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating plots: {e}")
        
        # Schedule next update
        if self.is_recording:
            self.parent.after(50, self.update_plots)
    
    def cleanup(self):
        """Cleanup audio resources"""
        try:
            self.stop_recording()
            if hasattr(self, 'audio'):
                self.audio.terminate()
        except Exception as e:
            print(f"Error during cleanup: {e}")

class VoiceAssistantAudioVizFixed:
    """Voice Assistant with Fixed Audio Visualization"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant for Windows - Fixed Audio Visualization")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize voice components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()

        # GUI state
        self.is_listening = False
        self.listening_thread = None

        # Adjust microphone sensitivity
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self.setup_gui()

        self.commands = VoiceCommandEngine(
            speak=self.speak,
            log=self.add_log,
            confirm_dangerous=lambda name: messagebox.askyesno(
                "Confirm", f"Run {name}? This will affect the whole system."
            ),
        )
        self.add_log("Voice Assistant with Fixed Audio Visualization initialized. Click 'Start Listening'.")

    def setup_gui(self):
        """Setup the graphical user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="Voice Assistant - Fixed Audio Visualization", 
                              font=("Arial", 20, "bold"), 
                              bg='#1e1e1e', fg='#00ff00')
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status indicator
        self.status_label = tk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 12), 
                                    bg='#1e1e1e', fg='#ffff00')
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Listen button
        self.listen_button = tk.Button(left_panel, text="Start Listening", 
                                      font=("Arial", 14, "bold"),
                                      bg='#00ff00', fg='#000000',
                                      width=15, height=2,
                                      command=self.toggle_listening)
        self.listen_button.pack(pady=10)
        
        # Quick access buttons
        quick_access_frame = ttk.LabelFrame(left_panel, text="Quick Access", padding="5")
        quick_access_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Application buttons
        apps_frame = ttk.LabelFrame(quick_access_frame, text="Applications", padding="5")
        apps_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        apps = [
            ("Notepad", "notepad"),
            ("Calculator", "calculator"),
            ("Chrome", "chrome"),
            ("VS Code", "visual studio code"),
            ("Spotify", "spotify")
        ]
        
        for i, (display_name, command) in enumerate(apps):
            btn = tk.Button(apps_frame, text=display_name, 
                          font=("Arial", 10),
                          bg='#404040', fg='#ffffff',
                          command=lambda c=command: self.quick_launch_app(c))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.W+tk.E)
        
        apps_frame.columnconfigure(0, weight=1)
        apps_frame.columnconfigure(1, weight=1)
        
        # Windows features buttons
        windows_frame = ttk.LabelFrame(quick_access_frame, text="Windows Features", padding="5")
        windows_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        windows = [
            ("Control Panel", "control panel"),
            ("Settings", "settings"),
            ("Task Manager", "task manager"),
            ("Device Manager", "device manager")
        ]
        
        for i, (display_name, command) in enumerate(windows):
            btn = tk.Button(windows_frame, text=display_name, 
                          font=("Arial", 10),
                          bg='#404040', fg='#ffffff',
                          command=lambda c=command: self.quick_open_feature(c))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky=tk.W+tk.E)
        
        windows_frame.columnconfigure(0, weight=1)
        windows_frame.columnconfigure(1, weight=1)
        
        # Web buttons
        web_frame = ttk.LabelFrame(quick_access_frame, text="Web", padding="5")
        web_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        websites = [
            ("Google", "google"),
            ("YouTube", "youtube"),
            ("Gmail", "gmail")
        ]
        
        for i, (display_name, command) in enumerate(websites):
            btn = tk.Button(web_frame, text=display_name, 
                          font=("Arial", 10),
                          bg='#404040', fg='#ffffff',
                          command=lambda c=command: self.quick_open_website(c))
            btn.grid(row=0, column=i, padx=2, pady=2, sticky=tk.W+tk.E)
        
        web_frame.columnconfigure(0, weight=1)
        web_frame.columnconfigure(1, weight=1)
        web_frame.columnconfigure(2, weight=1)
        
        # Right panel - Audio visualization and log
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        right_panel.rowconfigure(0, weight=3)
        right_panel.rowconfigure(1, weight=1)
        
        # Audio visualization
        viz_frame = ttk.LabelFrame(right_panel, text="Audio Visualization", padding="5")
        viz_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.audio_viz = AudioVisualizerFixed(viz_frame)
        
        # Activity log
        log_frame = ttk.LabelFrame(right_panel, text="Activity Log", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 width=60, height=10,
                                                 bg='#000000', fg='#00ff00',
                                                 font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Text input frame
        text_input_frame = ttk.Frame(main_frame)
        text_input_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        text_input_frame.columnconfigure(0, weight=1)
        
        self.text_input = tk.Entry(text_input_frame, font=("Arial", 12))
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.text_input.bind('<Return>', self.process_text_command)
        
        text_button = tk.Button(text_input_frame, text="Send Command", 
                               font=("Arial", 10),
                               bg='#404040', fg='#ffffff',
                               command=self.process_text_command)
        text_button.grid(row=0, column=1, padx=5)

    def speak(self, text):
        """Convert text to speech"""
        self.add_log(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def add_log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=f"Status: {status}")
        self.root.update_idletasks()

    def toggle_listening(self):
        """Toggle listening state"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        """Start listening for voice commands"""
        self.is_listening = True
        self.listen_button.config(text="Stop Listening", bg='#ff0000')
        self.update_status("Listening...")
        self.add_log("Started listening...")
        
        # Start audio visualization
        self.audio_viz.start_recording()
        
        # Start listening in a separate thread
        self.listening_thread = threading.Thread(target=self.listen_loop)
        self.listening_thread.daemon = True
        self.listening_thread.start()

    def stop_listening(self):
        """Stop listening for voice commands"""
        self.is_listening = False
        self.listen_button.config(text="Start Listening", bg='#00ff00')
        self.update_status("Ready")
        self.add_log("Stopped listening.")
        
        # Stop audio visualization
        self.audio_viz.stop_recording()

    def listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    self.update_status("Listening...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    self.update_status("Recognizing...")
                    command = self.recognizer.recognize_google(audio).lower()
                    
                    self.add_log(f"You said: {command}")
                    self.process_command(command)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self.add_log("Could not understand audio")
                continue
            except sr.RequestError as e:
                self.add_log(f"Speech recognition error: {e}")
                continue
            except Exception as e:
                self.add_log(f"Error: {e}")
                break

    def process_text_command(self, event=None):
        """Process text command from entry field"""
        command = self.text_input.get().strip().lower()
        if command:
            self.add_log(f"Text command: {command}")
            self.text_input.delete(0, tk.END)
            self.process_command(command)

    def process_command(self, command):
        """Process and execute commands"""
        if not command:
            return

        result = self.commands.process(command)
        if result == CommandDispatch.EXIT:
            self.speak("Goodbye!")
            self.cleanup()
            self.root.quit()
            return
        if result == CommandDispatch.HELP:
            self.show_help()

    def show_help(self):
        """Display available commands"""
        help_text = self.commands.get_help_text()
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Available Commands")
        help_window.geometry("500x400")
        help_window.configure(bg='#1e1e1e')
        
        help_text_widget = scrolledtext.ScrolledText(help_window, 
                                                     width=60, height=20,
                                                     bg='#000000', fg='#00ff00',
                                                     font=("Consolas", 10))
        help_text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        
        self.speak("Here are the available commands. Check the help window for the full list.")

    def quick_launch_app(self, app_name):
        """Quick launch application from button"""
        self.commands.launch_application(app_name)

    def quick_open_feature(self, feature):
        """Quick open Windows feature from button"""
        self.commands.open_windows_feature(feature)

    def quick_open_website(self, site):
        """Quick open website from button"""
        self.commands.open_website(site)

    def cleanup(self):
        """Cleanup resources"""
        self.audio_viz.cleanup()

    def run(self):
        """Start the GUI application"""
        self.speak("Voice Assistant with Fixed Audio Visualization ready. Click Start Listening.")
        try:
            self.root.mainloop()
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app = VoiceAssistantAudioVizFixed()
        app.run()
    except Exception as e:
        print(f"Failed to initialize voice assistant with fixed audio visualization: {e}")
        sys.exit(1)
