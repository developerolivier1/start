#!/usr/bin/env python3
"""
Voice Assistant for Windows - Command Line Version
A Python-based voice assistant that can open desktop applications and Windows features using voice commands.
"""

import sys
import speech_recognition as sr
import pyttsx3

from voice_assistant_core import CommandDispatch, VoiceCommandEngine


class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()

        self.commands = VoiceCommandEngine(
            speak=self.speak,
            log=print,
            confirm_dangerous=self._confirm_shutdown_or_restart,
        )

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        print("Voice Assistant initialized. Say 'help' for commands or 'exit' to quit.")
        self.speak("Voice Assistant ready. Say help for commands or exit to quit.")

    def _confirm_shutdown_or_restart(self, action: str) -> bool:
        self.speak(f"Are you sure you want to {action}? Say yes to confirm.")
        reply = self.listen()
        return bool(reply and "yes" in reply)

    def speak(self, text):
        """Convert text to speech"""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen for voice commands"""
        with self.microphone as source:
            print("\nListening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Recognizing...")
                command = self.recognizer.recognize_google(audio).lower()
                print(f"You said: {command}")
                return command
            except sr.WaitTimeoutError:
                print("Listening timeout. Please try again.")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio. Please try again.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None

    def show_help(self):
        print(self.commands.get_help_text())
        self.speak("Here are the available commands. Check the console for the full list.")

    def process_command(self, command):
        if not command:
            return True
        result = self.commands.process(command)
        if result == CommandDispatch.EXIT:
            self.speak("Goodbye!")
            return False
        if result == CommandDispatch.HELP:
            self.show_help()
        return True

    def run(self):
        print("Voice Assistant is running...")

        while True:
            try:
                command = self.listen()
                if command:
                    if not self.process_command(command):
                        break
            except KeyboardInterrupt:
                print("\nVoice Assistant stopped by user.")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                self.speak("An error occurred. Please try again.")


if __name__ == "__main__":
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        print(f"Failed to initialize voice assistant: {e}")
        sys.exit(1)
