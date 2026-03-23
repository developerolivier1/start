#!/usr/bin/env python3
"""
Audio Diagnostic Tool
Test audio input and visualization components
"""

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from collections import deque
import threading
import time

class AudioDiagnostic:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Diagnostic Tool")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.is_recording = False
        
        # Data storage
        self.audio_data = deque(maxlen=1024)
        self.volume_history = deque(maxlen=50)
        
        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
            print(f"PyAudio initialized successfully")
            print(f"Default input device: {self.audio.get_default_input_device_info()}")
            print(f"Available input devices: {self.get_input_devices()}")
        except Exception as e:
            print(f"Error initializing PyAudio: {e}")
            return
        
        self.setup_gui()
        
    def get_input_devices(self):
        """Get list of available input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append(f"Device {i}: {info['name']}")
        return devices
    
    def setup_gui(self):
        """Setup diagnostic GUI"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(main_frame, text="Audio Diagnostic Tool", 
                        font=("Arial", 16, "bold"), 
                        bg='#1e1e1e', fg='#00ff00')
        title.pack(pady=10)
        
        # Device info
        device_frame = tk.Frame(main_frame, bg='#1e1e1e')
        device_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(device_frame, text="Audio Devices:", 
                font=("Arial", 12), bg='#1e1e1e', fg='#ffff00').pack(anchor=tk.W)
        
        devices_text = tk.Text(device_frame, height=4, width=80,
                               bg='#000000', fg='#00ff00',
                               font=("Consolas", 9))
        devices_text.pack(fill=tk.X, pady=5)
        
        devices = self.get_input_devices()
        for device in devices:
            devices_text.insert(tk.END, device + "\n")
        devices_text.config(state=tk.DISABLED)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#1e1e1e')
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = tk.Button(button_frame, text="Start Audio Test", 
                                     font=("Arial", 12),
                                     bg='#00ff00', fg='#000000',
                                     command=self.start_test)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop Test", 
                                    font=("Arial", 12),
                                    bg='#ff0000', fg='#ffffff',
                                    command=self.stop_test, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 12), 
                                    bg='#1e1e1e', fg='#ffff00')
        self.status_label.pack(pady=5)
        
        # Visualization
        self.setup_visualization(main_frame)
        
    def setup_visualization(self, parent):
        """Setup matplotlib visualization"""
        # Create figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 4), 
                                                      facecolor='#1e1e1e')
        
        # Waveform plot
        self.ax1.set_facecolor('#000000')
        self.ax1.set_title('Audio Waveform', color='#00ff00')
        self.ax1.set_xlabel('Samples', color='#00ff00')
        self.ax1.set_ylabel('Amplitude', color='#00ff00')
        self.ax1.tick_params(colors='#00ff00')
        self.ax1.set_xlim(0, self.CHUNK)
        self.ax1.set_ylim(-32768, 32767)
        self.waveform_line, = self.ax1.plot([], [], 'g-', linewidth=1)
        
        # Volume plot
        self.ax2.set_facecolor('#000000')
        self.ax2.set_title('Volume Level', color='#00ff00')
        self.ax2.set_xlabel('Time', color='#00ff00')
        self.ax2.set_ylabel('Volume', color='#00ff00')
        self.ax2.tick_params(colors='#00ff00')
        self.ax2.set_xlim(0, 50)
        self.ax2.set_ylim(0, 100)
        self.volume_line, = self.ax2.plot([], [], 'b-', linewidth=2)
        
        self.fig.tight_layout()
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback function"""
        if self.is_recording:
            try:
                # Convert to numpy array
                audio_array = np.frombuffer(in_data, dtype=np.int16)
                self.audio_data.extend(audio_array)
                
                # Calculate volume
                volume = np.sqrt(np.mean(audio_array**2))
                volume_normalized = min(100, volume / 100)  # Normalize to 0-100
                self.volume_history.append(volume_normalized)
                
            except Exception as e:
                print(f"Audio callback error: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def update_plots(self):
        """Update matplotlib plots"""
        if self.is_recording:
            try:
                # Update waveform
                if len(self.audio_data) > 0:
                    waveform_data = list(self.audio_data)
                    self.waveform_line.set_data(range(len(waveform_data)), waveform_data)
                
                # Update volume
                if len(self.volume_history) > 0:
                    volume_data = list(self.volume_history)
                    self.volume_line.set_data(range(len(volume_data)), volume_data)
                
                self.canvas.draw()
                
            except Exception as e:
                print(f"Plot update error: {e}")
        
        # Schedule next update
        if self.is_recording:
            self.root.after(50, self.update_plots)
    
    def start_test(self):
        """Start audio test"""
        try:
            self.status_label.config(text="Status: Starting audio test...")
            self.root.update()
            
            # Open audio stream
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
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Recording... Speak into your microphone")
            
            # Start plot updates
            self.update_plots()
            
            print("Audio test started successfully")
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {e}")
            print(f"Error starting audio test: {e}")
    
    def stop_test(self):
        """Stop audio test"""
        try:
            self.is_recording = False
            
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Test stopped")
            
            print("Audio test stopped")
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error stopping - {e}")
            print(f"Error stopping audio test: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_test()
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    def run(self):
        """Run the diagnostic tool"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            print(f"Error running diagnostic: {e}")
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle window closing"""
        self.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    print("Starting Audio Diagnostic Tool...")
    diagnostic = AudioDiagnostic()
    diagnostic.run()
