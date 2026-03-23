#!/usr/bin/env python3
"""
Voice Assistant for Windows - Simple Working Audio Visualization
Simplified version with basic but functional audio visualization.
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
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pyaudio
from collections import deque

class SimpleAudioVisualizer:
    """Simplified audio visualization that actually works"""
    
    def __init__(self, parent):
        self.parent = parent
        self.is_recording = False
        self.audio_data = deque(maxlen=1000)
        self.volume_history = deque(maxlen=100)
        
        # Audio settings - more conservative
        self.CHUNK = 512
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # Lower sample rate for stability
        
        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = None
            print(f"Audio initialized: {self.audio.get_default_input_device_info()}")
        except Exception as e:
            print(f"Audio init error: {e}")
            self.create_error_display(parent)
            return
        
        self.setup_simple_plots()
        
    def create_error_display(self, parent):
        """Create error display when audio fails"""
        error_frame = tk.Frame(parent, bg='#1e1e1e')
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(error_frame, text="Audio Visualization Error", 
                font=("Arial", 16, "bold"),
                bg='#1e1e1e', fg='#ff0000').pack(pady=20)
        
        tk.Label(error_frame, text="Voice commands will still work", 
                font=("Arial", 12),
                bg='#1e1e1e', fg='#00ff00').pack(pady=10)
        
    def setup_simple_plots(self):
        """Setup simple, reliable plots"""
        try:
            # Create figure
            self.fig = Figure(figsize=(10, 4), facecolor='#1e1e1e')
            
            # Simple waveform plot
            self.ax_waveform = self.fig.add_subplot(111, facecolor='#000000')
            self.ax_waveform.set_title('Live Audio Input', color='#00ff00', fontsize=14)
            self.ax_waveform.set_xlabel('Time', color='#00ff00')
            self.ax_waveform.set_ylabel('Amplitude', color='#00ff00')
            self.ax_waveform.tick_params(colors='#00ff00')
            self.ax_waveform.set_ylim(-32768, 32767)
            self.ax_waveform.grid(True, alpha=0.3, color='#00ff00')
            
            # Initialize empty line
            self.waveform_line, = self.ax_waveform.plot([], [], 'g-', linewidth=1)
            
            self.fig.tight_layout()
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            print("Plots setup successfully")
            
        except Exception as e:
            print(f"Plot setup error: {e}")
            self.create_error_display(self.parent)
        
    def start_recording(self):
        """Start audio recording"""
        if not self.is_recording:
            try:
                print("Starting audio recording...")
                self.stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK,
                    stream_callback=self.audio_callback
                )
                self.stream.start_stream()
                self.is_recording = True
                print("Audio recording started")
                
                # Start update loop
                self.update_display()
                
            except Exception as e:
                print(f"Error starting recording: {e}")
                self.is_recording = False
                
    def stop_recording(self):
        """Stop audio recording"""
        if self.is_recording:
            try:
                self.is_recording = False
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                print("Audio recording stopped")
            except Exception as e:
                print(f"Error stopping recording: {e}")
                
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Simple audio callback"""
        if self.is_recording:
            try:
                # Convert to numpy array
                audio_array = np.frombuffer(in_data, dtype=np.int16)
                
                # Only add valid data
                if len(audio_array) > 0 and not np.all(audio_array == 0):
                    self.audio_data.extend(audio_array)
                    
                    # Calculate simple volume
                    if np.any(audio_array != 0):
                        volume = np.abs(audio_array).mean()
                        self.volume_history.append(volume)
                
            except Exception as e:
                print(f"Audio callback error: {e}")
                
        return (in_data, pyaudio.paContinue)
    
    def update_display(self):
        """Update the display"""
        if self.is_recording:
            try:
                # Update waveform if we have data
                if len(self.audio_data) > 0:
                    # Get recent data
                    data_array = np.array(list(self.audio_data))
                    
                    # Create time axis
                    time_axis = np.arange(len(data_array))
                    
                    # Update plot
                    self.waveform_line.set_data(time_axis, data_array)
                    
                    # Adjust x-axis limits
                    if len(data_array) > 0:
                        self.ax_waveform.set_xlim(0, max(len(data_array), 1000))
                    
                    # Redraw
                    self.canvas.draw_idle()
                
                # Schedule next update
                self.parent.after(100, self.update_display)  # Update every 100ms
                
            except Exception as e:
                print(f"Display update error: {e}")
                # Try again in a moment
                self.parent.after(500, self.update_display)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_recording()
            if hasattr(self, 'audio'):
                self.audio.terminate()
        except Exception as e:
            print(f"Cleanup error: {e}")

class VoiceAssistantSimpleViz:
    """Voice Assistant with Simple Working Audio Visualization"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant - Simple Audio Visualization")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize voice components
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.engine = pyttsx3.init()

            # Adjust microphone sensitivity
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)

            print("Voice components initialized successfully")
        except Exception as e:
            print(f"Voice init error: {e}")
            messagebox.showerror("Error", f"Failed to initialize voice components: {e}")
            sys.exit(1)

        # GUI state
        self.is_listening = False
        self.listening_thread = None

        self.setup_gui()

        self.commands = VoiceCommandEngine(
            speak=self.speak,
            log=self.add_log,
            confirm_dangerous=lambda name: messagebox.askyesno(
                "Confirm", f"Run {name}? This will affect the whole system."
            ),
        )
        self.add_log("Voice Assistant ready. Click 'Start Listening' to begin.")

    def setup_gui(self):
        """Setup GUI"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Voice Assistant - Simple Audio Visualization", 
                              font=("Arial", 18, "bold"), 
                              bg='#1e1e1e', fg='#00ff00')
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 12), 
                                    bg='#1e1e1e', fg='#ffff00')
        self.status_label.pack(pady=5)
        
        # Control frame
        control_frame = tk.Frame(main_frame, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, pady=10)
        
        # Listen button
        self.listen_button = tk.Button(control_frame, text="Start Listening", 
                                      font=("Arial", 14, "bold"),
                                      bg='#00ff00', fg='#000000',
                                      width=15, height=2,
                                      command=self.toggle_listening)
        self.listen_button.pack(side=tk.LEFT, padx=10)
        
        # Quick buttons frame
        quick_frame = tk.Frame(control_frame, bg='#1e1e1e')
        quick_frame.pack(side=tk.LEFT, padx=20)
        
        # Quick access buttons
        quick_apps = [
            ("Notepad", "notepad"),
            ("Calculator", "calculator"),
            ("Chrome", "chrome"),
            ("Settings", "settings")
        ]
        
        for text, cmd in quick_apps:
            btn = tk.Button(quick_frame, text=text, 
                           font=("Arial", 10),
                           bg='#404040', fg='#ffffff',
                           command=lambda c=cmd: self.quick_command(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Audio visualization
        viz_frame = tk.LabelFrame(main_frame, text="Audio Visualization", 
                                font=("Arial", 12, "bold"),
                                bg='#1e1e1e', fg='#00ff00', padx=5, pady=5)
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.audio_viz = SimpleAudioVisualizer(viz_frame)
        
        # Activity log
        log_frame = tk.LabelFrame(main_frame, text="Activity Log",
                                font=("Arial", 12, "bold"),
                                bg='#1e1e1e', fg='#00ff00', padx=5, pady=5)
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 width=80, height=8,
                                                 bg='#000000', fg='#00ff00',
                                                 font=("Consolas", 9))
        self.log_text.pack(fill=tk.X)
        
        # Text input
        input_frame = tk.Frame(main_frame, bg='#1e1e1e')
        input_frame.pack(fill=tk.X, pady=5)
        
        self.text_input = tk.Entry(input_frame, font=("Arial", 12),
                                  bg='#2d2d2d', fg='#ffffff',
                                  insertbackground='#00ff00',
                                  relief=tk.FLAT, bd=2)
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.text_input.bind('<Return>', self.process_text_command)
        
        tk.Button(input_frame, text="Send", 
                 font=("Arial", 10),
                 bg='#404040', fg='#ffffff',
                 command=self.process_text_command).pack(side=tk.RIGHT, padx=5)

    def speak(self, text):
        """Text to speech"""
        self.add_log(f"Assistant: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")

    def add_log(self, message):
        """Add to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status):
        """Update status"""
        self.status_label.config(text=f"Status: {status}")
        self.root.update_idletasks()

    def toggle_listening(self):
        """Toggle listening"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        """Start listening"""
        self.is_listening = True
        self.listen_button.config(text="Stop Listening", bg='#ff0000')
        self.update_status("Listening...")
        self.add_log("Started listening...")
        
        # Start audio visualization
        self.audio_viz.start_recording()
        
        # Start voice recognition thread
        self.listening_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.listening_thread.start()

    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.listen_button.config(text="Start Listening", bg='#00ff00')
        self.update_status("Ready")
        self.add_log("Stopped listening.")
        
        # Stop audio visualization
        self.audio_viz.stop_recording()

    def listen_loop(self):
        """Voice recognition loop"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    self.update_status("Listening...")
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=5)
                    
                    self.update_status("Recognizing...")
                    command = self.recognizer.recognize_google(audio).lower()
                    
                    self.add_log(f"You said: {command}")
                    self.process_command(command)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                self.add_log(f"Speech recognition error: {e}")
                continue
            except Exception as e:
                self.add_log(f"Error: {e}")
                break

    def process_text_command(self, event=None):
        """Process text command"""
        command = self.text_input.get().strip().lower()
        if command:
            self.add_log(f"Text command: {command}")
            self.text_input.delete(0, tk.END)
            self.process_command(command)

    def process_command(self, command):
        """Process voice command"""
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

    def quick_command(self, command):
        """Quick command from button"""
        if command in ["notepad", "calculator", "chrome"]:
            self.commands.launch_application(command)
        elif command == "settings":
            self.commands.open_windows_feature("settings")

    def show_help(self):
        """Show help"""
        self.speak("Here are available commands")
        self.add_log(self.commands.get_help_text())

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.audio_viz.cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def run(self):
        """Run application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app = VoiceAssistantSimpleViz()
        app.run()
    except Exception as e:
        print(f"Failed to start: {e}")
        sys.exit(1)
