#!/usr/bin/env python3
"""
Voice Assistant for Windows - Basic GUI Version
A Python-based voice assistant with a user-friendly graphical interface.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
import pyttsx3
import sys
from datetime import datetime
import threading

from voice_assistant_core import CommandDispatch, VoiceCommandEngine

class VoiceAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant for Windows")
        self.root.geometry("800x600")
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
        self.add_log("Voice Assistant initialized. Click 'Start Listening' or use quick access buttons.")

    def setup_gui(self):
        """Setup the graphical user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="Voice Assistant", 
                              font=("Arial", 24, "bold"), 
                              bg='#1e1e1e', fg='#00ff00')
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status indicator
        self.status_label = tk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 12), 
                                    bg='#1e1e1e', fg='#ffff00')
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Listen button
        self.listen_button = tk.Button(control_frame, text="Start Listening", 
                                      font=("Arial", 14, "bold"),
                                      bg='#00ff00', fg='#000000',
                                      width=15, height=2,
                                      command=self.toggle_listening)
        self.listen_button.pack(pady=10)
        
        # Quick access buttons
        quick_access_frame = ttk.LabelFrame(control_frame, text="Quick Access", padding="5")
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
        
        # Activity log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 width=50, height=20,
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

    def run(self):
        """Start the GUI application"""
        self.speak("Voice Assistant GUI ready. Click Start Listening or use quick access buttons.")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = VoiceAssistantGUI()
        app.run()
    except Exception as e:
        print(f"Failed to initialize voice assistant GUI: {e}")
        sys.exit(1)
