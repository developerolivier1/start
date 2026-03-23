# Voice Assistant for Windows

A Python-based voice assistant that can open desktop applications and Windows features using voice commands, with real-time audio visualization.

## Features

- **Voice Recognition**: Google Speech API integration
- **Text-to-Speech**: Voice feedback for all actions
- **Application Launcher**: Open desktop applications by voice
- **Windows Features**: Access Control Panel, Settings, and system tools
- **System Utilities**: Shutdown, restart, lock, and other system commands
- **Audio Visualization**: Real-time waveform, volume levels, and frequency spectrum
- **GUI Interface**: User-friendly graphical interface with visual feedback
- **Configurable**: Easy to add new commands and applications

## Versions Available

1. **`voice_assistant.py`** - Command-line version
2. **`voice_assistant_gui.py`** - Basic GUI version
3. **`voice_assistant_audio_viz.py`** - Full GUI with audio visualization

## Requirements

Install the required packages:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install speechrecognition==3.14.6
pip install pyttsx3==2.99
pip install pyaudio==0.2.14
pip install pywin32==311
pip install numpy==1.24.3
pip install matplotlib==3.7.1
pip install comtypes==1.4.16
pip install pypiwin32==223
pip install typing_extensions==4.15.0
```

## Usage

### Basic Command Line Version
```bash
python voice_assistant.py
```

### GUI Version
```bash
python voice_assistant_gui.py
```

### Full Version with Audio Visualization (Recommended)
```bash
python voice_assistant_audio_viz.py
```

## Audio Visualization Features

The audio visualization version provides real-time analysis of your voice:

### Waveform Display
- Shows the raw audio signal amplitude over time
- Green background tint when speech is detected
- Real-time updates at 20 FPS

### Volume Level Meter
- Displays sound intensity in decibels
- Red threshold line indicates speech detection level
- Historical volume graph showing last 50 readings

### Frequency Spectrum
- FFT-based frequency analysis
- Shows frequency components up to 5kHz
- Helps visualize voice characteristics and pitch

### Speech Detection
- Automatic speech detection based on volume threshold
- Visual feedback with color changes
- Helps you know when the system is detecting your voice

## Voice Commands

### Applications
- "Open notepad"
- "Launch calculator"
- "Start chrome"
- "Open visual studio code"
- "Launch spotify"

### Windows Features
- "Open control panel"
- "Show settings"
- "Open device manager"
- "Launch disk management"
- "Show system settings"

### System Utilities
- "Shutdown computer" (with confirmation)
- "Restart system" (with confirmation)
- "Lock screen"
- "Go to sleep"

### Web Commands
- "Open google"
- "Launch youtube"
- "Open gmail"

### General Commands
- "Help" - Shows available commands
- "Exit" or "Quit" - Closes the assistant

## GUI Features

### Main Interface
- Dark theme with terminal-style text
- Large "Start Listening" button with visual feedback
- Real-time status indicator
- Activity log with timestamps and color coding

### Quick Access Buttons
- One-click access to common applications
- No need to remember voice commands
- Instant feedback

### Multiple Input Methods
1. **Voice**: Click "Start Listening" and speak commands
2. **Buttons**: Quick access to common apps
3. **Text**: Type commands directly and press Enter

### Audio Visualization Panel
- Three real-time graphs showing audio analysis
- Helps you understand when the system is listening
- Visual feedback for speech detection

## Configuration

Customize commands by editing `commands_config.json`:

- **applications**: Add or modify application launch commands
- **windows_features**: Configure Windows tools and settings
- **system_utilities**: Modify system command mappings
- **web_commands**: Add website shortcuts

## Adding New Applications

To add a new application:

1. Open `commands_config.json` 
2. Add to the `applications` section:
```json
"app name": "executable.exe"
```

Or the assistant will automatically search for executables in common Program Files locations.

## Microphone Requirements

- Ensure your microphone is connected and working
- Grant microphone permissions when prompted
- Speak clearly and wait for the "Listening..." prompt
- The audio visualization helps you see when your voice is being detected

## Troubleshooting

**Microphone not working:**
- Check Windows microphone settings
- Ensure no other app is using the microphone
- Try running as administrator

**Audio visualization not working:**
- Install matplotlib: `pip install matplotlib` 
- Install numpy: `pip install numpy` 
- Check if PyAudio is properly installed

**Application not found:**
- Check if the application is installed
- Verify the executable name in the config file
- Try using the full path to the executable

**Speech recognition issues:**
- Speak clearly and reduce background noise
- Ensure you have an internet connection (uses Google Speech API)
- Try shorter, clearer commands
- Watch the volume meter to ensure you're speaking loudly enough

## Safety Features

- Confirmation required for shutdown/restart commands
- Error handling for failed launches
- Safe command execution with proper error checking
- Visual feedback for all operations

## Example Session with Audio Visualization

1. Start the application: `python voice_assistant_audio_viz.py` 
2. Click "Start Listening"
3. Watch the audio visualization as you speak
4. Say: "Open notepad"
5. See the waveform spike when you speak
6. Watch the volume meter cross the threshold
7. Notepad launches automatically
8. Say: "Exit" to close

## Technical Details

### Audio Processing
- Sample rate: 44.1 kHz
- Bit depth: 16-bit
- Buffer size: 1024 samples
- Update rate: 20 FPS

### Speech Detection
- Volume threshold: 30 dB (normalized)
- Automatic gain control
- Noise reduction

### Visualization
- Real-time FFT analysis
- Rolling buffer for historical data
- Color-coded feedback

The audio visualization provides professional-level audio analysis while maintaining the simplicity of a voice assistant interface.

## File Structure

```
voice-assistant-windows/
├── voice_assistant.py              # Command-line version
├── voice_assistant_gui.py          # Basic GUI version
├── voice_assistant_audio_viz.py    # Full GUI with audio visualization
├── commands_config.json            # Configuration file
├── requirements.txt                # Python dependencies
└── README.md                      # This file
```

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests!

## Support

If you encounter any issues, please check the troubleshooting section above or create an issue in the project repository.
