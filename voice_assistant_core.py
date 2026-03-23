#!/usr/bin/env python3
"""
Shared command routing and execution for all voice assistant entry points.
Handles apps, Windows features, web, system utilities, media keys, desktop shortcuts,
and a whitelist of custom shell phrases from commands_config.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import webbrowser
from enum import Enum
from typing import Callable, Optional

import win32api
import win32con


class CommandDispatch(Enum):
    EXIT = "exit"
    HELP = "help"
    HANDLED = "handled"
    UNKNOWN = "unknown"


_WIN = 0x5B
_ALT = 0x12
_CTRL = 0x11
_SHIFT = 0x10


def _tap_vk(vk: int) -> None:
    win32api.keybd_event(vk, 0, 0, 0)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)


def _hold_combo(hold: list[int], key: int) -> None:
    for vk in hold:
        win32api.keybd_event(vk, 0, 0, 0)
    win32api.keybd_event(key, 0, 0, 0)
    win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
    for vk in reversed(hold):
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)


def _screenshot_snip() -> None:
    win32api.keybd_event(_WIN, 0, 0, 0)
    win32api.keybd_event(_SHIFT, 0, 0, 0)
    win32api.keybd_event(ord("S"), 0, 0, 0)
    win32api.keybd_event(ord("S"), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(_WIN, 0, win32con.KEYEVENTF_KEYUP, 0)


_MEDIA_ACTIONS = {
    "volume_up": lambda: _tap_vk(0xAF),
    "volume_down": lambda: _tap_vk(0xAE),
    "mute": lambda: _tap_vk(0xAD),
    "play_pause": lambda: _tap_vk(0xB3),
    "next_track": lambda: _tap_vk(0xB0),
    "prev_track": lambda: _tap_vk(0xB1),
    "stop_media": lambda: _tap_vk(0xB2),
}

_DESKTOP_ACTIONS = {
    "win_d": lambda: _hold_combo([_WIN], ord("D")),
    "win_m": lambda: _hold_combo([_WIN], ord("M")),
    "win_e": lambda: _hold_combo([_WIN], ord("E")),
    "alt_tab": lambda: _hold_combo([_ALT], 0x09),
    "win_left": lambda: _hold_combo([_WIN], 0x25),
    "win_right": lambda: _hold_combo([_WIN], 0x27),
    "win_up": lambda: _hold_combo([_WIN], 0x26),
    "win_down": lambda: _hold_combo([_WIN], 0x28),
    "win_tab": lambda: _hold_combo([_WIN], 0x09),
    "win_s": lambda: _hold_combo([_WIN], ord("S")),
    "alt_f4": lambda: _hold_combo([_ALT], 0x73),
    "ctrl_c": lambda: _hold_combo([_CTRL], ord("C")),
    "ctrl_v": lambda: _hold_combo([_CTRL], ord("V")),
    "ctrl_x": lambda: _hold_combo([_CTRL], ord("X")),
    "ctrl_a": lambda: _hold_combo([_CTRL], ord("A")),
    "ctrl_z": lambda: _hold_combo([_CTRL], ord("Z")),
    "ctrl_y": lambda: _hold_combo([_CTRL], ord("Y")),
    "screenshot": _screenshot_snip,
    "clipboard_history": lambda: _hold_combo([_WIN], ord("V")),
}

_BUILTIN_MEDIA_PHRASES = {
    "volume up": "volume_up",
    "turn up the volume": "volume_up",
    "louder": "volume_up",
    "volume down": "volume_down",
    "turn down the volume": "volume_down",
    "quieter": "volume_down",
    "mute": "mute",
    "unmute": "mute",
    "mute sound": "mute",
    "pause music": "play_pause",
    "play music": "play_pause",
    "pause": "play_pause",
    "next track": "next_track",
    "next song": "next_track",
    "skip song": "next_track",
    "previous track": "prev_track",
    "last track": "prev_track",
}

_BUILTIN_DESKTOP_PHRASES = {
    "show desktop": "win_d",
    "minimize all windows": "win_m",
    "minimize windows": "win_m",
    "open file explorer": "win_e",
    "open explorer": "win_e",
    "switch window": "alt_tab",
    "next window": "alt_tab",
    "snap window left": "win_left",
    "snap left": "win_left",
    "snap window right": "win_right",
    "snap right": "win_right",
    "maximize window": "win_up",
    "restore window": "win_down",
    "task view": "win_tab",
    "open search": "win_s",
    "close window": "alt_f4",
    "take screenshot": "screenshot",
    "snip screen": "screenshot",
    "copy": "ctrl_c",
    "paste": "ctrl_v",
    "cut": "ctrl_x",
    "select all": "ctrl_a",
    "undo": "ctrl_z",
    "redo": "ctrl_y",
    "open clipboard history": "clipboard_history",
}

_BUILTIN_SYSTEM_PHRASES = {
    "shutdown computer": "shutdown",
    "turn off computer": "shutdown",
    "power off": "shutdown",
    "restart computer": "restart",
    "reboot computer": "restart",
    "restart system": "restart",
    "lock screen": "lock",
    "lock computer": "lock",
    "go to sleep": "sleep",
    "sleep computer": "sleep",
    "put computer to sleep": "sleep",
    "sign out": "log off",
    "log off": "log off",
    "log out": "log off",
    "hibernate computer": "hibernate",
}

_DANGEROUS_SYSTEM = frozenset({"shutdown", "restart"})


def _config_path(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "commands_config.json")


class VoiceCommandEngine:
    def __init__(
        self,
        config_path: Optional[str] = None,
        speak: Callable[[str], None] = print,
        log: Optional[Callable[[str], None]] = None,
        confirm_dangerous: Optional[Callable[[str], bool]] = None,
    ):
        self.speak = speak
        self.log = log or (lambda _m: None)
        self.confirm_dangerous = confirm_dangerous
        self.config_path = _config_path(config_path)
        self.config: dict = {}
        self.reload_config()

    def reload_config(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

        for key in (
            "applications",
            "windows_features",
            "system_utilities",
            "web_commands",
            "media_commands",
            "desktop_commands",
            "system_phrases",
            "custom_shell_commands",
        ):
            if key not in self.config:
                self.config[key] = {}

        self.config["media_commands"] = {
            **_BUILTIN_MEDIA_PHRASES,
            **self.config["media_commands"],
        }
        self.config["desktop_commands"] = {
            **_BUILTIN_DESKTOP_PHRASES,
            **self.config["desktop_commands"],
        }
        self.config["system_phrases"] = {
            **_BUILTIN_SYSTEM_PHRASES,
            **self.config["system_phrases"],
        }

    def get_help_text(self) -> str:
        def sample_lines(title: str, d: dict, n: int = 8) -> list[str]:
            lines = [f"{title}:"]
            keys = list(d.keys())[:n]
            for k in keys:
                lines.append(f"  — {k}")
            if len(d) > n:
                lines.append(f"  … and {len(d) - n} more in commands_config.json")
            return lines

        parts = [
            "Voice Assistant — say natural phrases or use open / launch / start / show.",
            "",
            "Examples:",
            "  open notepad | launch youtube | show settings | lock screen | volume up",
            "  show desktop | switch window | take screenshot | close window | close notepad",
            "",
            *sample_lines("Applications (open …)", self.config.get("applications", {})),
            "",
            *sample_lines("Websites (open … / launch …)", self.config.get("web_commands", {})),
            "",
            *sample_lines("Windows features (open … / show …)", self.config.get("windows_features", {})),
            "",
            *sample_lines("Media & volume", self.config.get("media_commands", {})),
            "",
            *sample_lines("Desktop & keyboard shortcuts", self.config.get("desktop_commands", {})),
            "",
            "System: say shutdown computer, restart computer, lock screen, go to sleep, etc.",
            "Custom shell phrases: edit custom_shell_commands in commands_config.json (whitelist only).",
            "",
            "help — this list   |   exit / quit / stop — close assistant",
        ]
        return "\n".join(parts)

    def _run_media(self, action_id: str) -> bool:
        fn = _MEDIA_ACTIONS.get(action_id)
        if not fn:
            return False
        try:
            fn()
            self.speak("Done")
            self.log(f"Media action: {action_id}")
            return True
        except Exception as e:
            self.log(f"Media action error: {e}")
            self.speak("Could not run that media action")
            return True

    def _run_desktop(self, action_id: str) -> bool:
        fn = _DESKTOP_ACTIONS.get(action_id)
        if not fn:
            return False
        try:
            fn()
            self.speak("Done")
            self.log(f"Desktop action: {action_id}")
            return True
        except Exception as e:
            self.log(f"Desktop action error: {e}")
            self.speak("Could not run that shortcut")
            return True

    def launch_application(self, app_name: str) -> bool:
        app_name = app_name.lower().strip()
        if app_name in self.config["applications"]:
            executable = self.config["applications"][app_name]
            try:
                subprocess.Popen(executable)
                self.speak(f"Launching {app_name}")
                self.log(f"Launched app: {app_name}")
                return True
            except Exception as e:
                self.log(f"Error launching {app_name}: {e}")
                self.speak(f"Could not launch {app_name}")
                return True

        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Windows\System32",
        ]
        for path in common_paths:
            for root, _dirs, files in os.walk(path):
                for file in files:
                    if app_name.replace(" ", "") in file.lower() and file.endswith(".exe"):
                        try:
                            subprocess.Popen(os.path.join(root, file))
                            self.speak(f"Found and launching {app_name}")
                            self.log(f"Launched (search): {app_name}")
                            return True
                        except Exception:
                            continue
        self.speak(f"Could not find {app_name}")
        self.log(f"Application not found: {app_name}")
        return True

    def open_windows_feature(self, feature: str) -> bool:
        feature = feature.lower().strip()
        if feature not in self.config["windows_features"]:
            self.speak(f"Windows feature {feature} not found")
            self.log(f"Windows feature not found: {feature}")
            return True
        command = self.config["windows_features"][feature]
        try:
            if command.startswith("ms-settings:"):
                os.startfile(command)
            else:
                subprocess.Popen(command, shell=True)
            self.speak(f"Opening {feature}")
            self.log(f"Opened feature: {feature}")
            return True
        except Exception as e:
            self.log(f"Error opening {feature}: {e}")
            self.speak(f"Could not open {feature}")
            return True

    def open_website(self, site: str) -> bool:
        site = site.lower().strip()
        if site not in self.config["web_commands"]:
            self.speak(f"Website {site} not found")
            self.log(f"Website not found: {site}")
            return True
        url = self.config["web_commands"][site]
        try:
            webbrowser.open(url)
            self.speak(f"Opening {site}")
            self.log(f"Opened website: {site}")
            return True
        except Exception as e:
            self.log(f"Error opening {site}: {e}")
            self.speak(f"Could not open {site}")
            return True

    def execute_system_command(self, utility_key: str) -> bool:
        utility_key = utility_key.lower().strip()
        if utility_key not in self.config["system_utilities"]:
            self.speak(f"System command {utility_key} not found")
            self.log(f"System command not found: {utility_key}")
            return True

        if utility_key in _DANGEROUS_SYSTEM:
            ok = True
            if self.confirm_dangerous:
                ok = self.confirm_dangerous(utility_key)
            if not ok:
                self.speak("Command cancelled")
                self.log("Dangerous system command cancelled")
                return True
            try:
                subprocess.Popen(self.config["system_utilities"][utility_key], shell=True)
                self.speak(f"System will {utility_key} now")
                self.log(f"System utility: {utility_key}")
            except Exception as e:
                self.log(f"Error executing {utility_key}: {e}")
                self.speak(f"Could not {utility_key}")
            return True

        try:
            subprocess.Popen(self.config["system_utilities"][utility_key], shell=True)
            self.speak(f"Executing {utility_key}")
            self.log(f"System utility: {utility_key}")
        except Exception as e:
            self.log(f"Error executing {utility_key}: {e}")
            self.speak(f"Could not {utility_key}")
        return True

    def close_target(self, name: str) -> bool:
        """End tasks for a configured application (by friendly name)."""
        name = name.lower().strip()
        if not name:
            self.speak("Say close followed by an app name")
            return True
        exe = None
        if name in self.config["applications"]:
            exe = self.config["applications"][name]
        if not exe:
            self.speak(f"I don't know how to close {name}")
            self.log(f"Close unknown target: {name}")
            return True
        base = os.path.basename(exe)
        try:
            subprocess.Popen(f"taskkill /im {base} /f", shell=True)
            self.speak(f"Closing {name}")
            self.log(f"Close: {name} ({base})")
            return True
        except Exception as e:
            self.log(f"Close error: {e}")
            self.speak(f"Could not close {name}")
            return True

    def run_custom_shell(self, phrase: str) -> bool:
        phrase = phrase.lower().strip()
        if phrase not in self.config["custom_shell_commands"]:
            return False
        cmd = self.config["custom_shell_commands"][phrase]
        try:
            subprocess.Popen(cmd, shell=True)
            self.speak(f"Running {phrase}")
            self.log(f"Custom shell: {phrase}")
            return True
        except Exception as e:
            self.log(f"Custom shell error: {e}")
            self.speak("Could not run that command")
            return True

    def _try_prefixed_target(self, target: str) -> bool:
        target = target.strip().lower()
        if not target:
            return False
        if target in self.config["applications"]:
            return self.launch_application(target)
        if target in self.config["windows_features"]:
            return self.open_windows_feature(target)
        if target in self.config["web_commands"]:
            return self.open_website(target)
        if self.run_custom_shell(target):
            return True
        self.launch_application(target)
        return True

    def process(self, command: Optional[str]) -> CommandDispatch:
        if not command:
            return CommandDispatch.HANDLED

        cmd = command.lower().strip()

        if cmd in ("exit", "quit", "stop"):
            return CommandDispatch.EXIT

        if cmd in ("help", "show help", "what can you do", "list commands"):
            return CommandDispatch.HELP

        if cmd in self.config["system_phrases"]:
            self.execute_system_command(self.config["system_phrases"][cmd])
            return CommandDispatch.HANDLED

        if cmd in self.config["system_utilities"]:
            self.execute_system_command(cmd)
            return CommandDispatch.HANDLED

        if cmd in self.config["media_commands"]:
            action = self.config["media_commands"][cmd]
            self._run_media(action)
            return CommandDispatch.HANDLED

        if cmd in self.config["desktop_commands"]:
            action = self.config["desktop_commands"][cmd]
            self._run_desktop(action)
            return CommandDispatch.HANDLED

        if cmd.startswith("close "):
            self.close_target(cmd[6:].strip())
            return CommandDispatch.HANDLED

        if cmd in self.config["custom_shell_commands"]:
            self.run_custom_shell(cmd)
            return CommandDispatch.HANDLED

        for prefix in ("open ", "launch ", "start "):
            if cmd.startswith(prefix):
                target = cmd[len(prefix) :].strip()
                self._try_prefixed_target(target)
                return CommandDispatch.HANDLED

        if cmd.startswith("show "):
            target = cmd[5:].strip()
            if target in self.config["windows_features"]:
                self.open_windows_feature(target)
            elif target in self.config["applications"]:
                self.launch_application(target)
            elif target in self.config["web_commands"]:
                self.open_website(target)
            elif self.run_custom_shell(target):
                pass
            else:
                self.open_windows_feature(target)
            return CommandDispatch.HANDLED

        self.speak("Sorry, I didn't understand that command. Say help for available commands.")
        self.log(f"Unknown command: {cmd}")
        return CommandDispatch.UNKNOWN
