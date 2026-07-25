"""Core Jarvis assistant behavior."""

from __future__ import annotations

import datetime as dt
import importlib
import os
import platform
import random
import re
import subprocess
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional
from urllib.parse import quote_plus

from jarvis_assistant.settings import JarvisSettings


TextOutput = Callable[[str], None]
TextInput = Callable[[str], str]
NowProvider = Callable[[], dt.datetime]
UrlLauncher = Callable[[str], object]
AppLauncher = Callable[[str], bool]


def _optional_import(module_name: str) -> Optional[Any]:
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _extract_after(command: str, phrases: Iterable[str]) -> str:
    lowered = command.lower()
    for phrase in phrases:
        index = lowered.find(phrase)
        if index != -1:
            return command[index + len(phrase) :].strip(" .,:;-")
    return ""


def _default_launch_app(app_name: str) -> bool:
    try:
        if platform.system().lower() == "windows":
            try:
                os.startfile(app_name)  # type: ignore[attr-defined]
            except OSError:
                subprocess.Popen(["cmd", "/c", "start", "", app_name])
        else:
            subprocess.Popen([app_name])
        return True
    except Exception:
        return False


class JarvisAssistant:
    """A small terminal/voice assistant with resilient optional integrations."""

    WEBSITE_ALIASES: Dict[str, str] = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "stack overflow": "https://stackoverflow.com",
        "whatsapp": "https://web.whatsapp.com",
        "whatsapp web": "https://web.whatsapp.com",
    }

    APP_ALIASES: Dict[str, str] = {
        "notepad": "notepad",
        "chrome": "chrome",
        "calculator": "calc",
        "paint": "mspaint",
    }

    EXIT_PHRASES = ("bye", "exit", "quit", "goodbye", "go to sleep", "stop jarvis")

    def __init__(
        self,
        settings: Optional[JarvisSettings] = None,
        output: TextOutput = print,
        input_provider: TextInput = input,
        now_provider: Optional[NowProvider] = None,
        open_url: UrlLauncher = webbrowser.open,
        launch_app: AppLauncher = _default_launch_app,
    ) -> None:
        self.settings = (settings or JarvisSettings()).normalized()
        self.output = output
        self.input_provider = input_provider
        self.now_provider = now_provider or dt.datetime.now
        self.open_url = open_url
        self.launch_app = launch_app
        self.engine = None
        self.recognizer = None
        self.microphone = None

        self._setup_voice()
        self._setup_speech()

    def _setup_voice(self) -> None:
        if not self.settings.enable_voice:
            return

        pyttsx3 = _optional_import("pyttsx3")
        if pyttsx3 is None:
            return

        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")
            if voices:
                self.engine.setProperty("voice", voices[0].id)
            self.engine.setProperty("rate", self.settings.voice_rate)
        except Exception:
            self.engine = None

    def _setup_speech(self) -> None:
        if not self.settings.enable_speech_recognition:
            return

        speech_recognition = _optional_import("speech_recognition")
        if speech_recognition is None:
            return

        try:
            self.recognizer = speech_recognition.Recognizer()
            self.microphone = speech_recognition.Microphone()
        except Exception:
            self.recognizer = None
            self.microphone = None

    def speak(self, text: str) -> None:
        self.output(text)
        if self.engine is None:
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            self.engine = None

    def listen(self) -> str:
        if self.recognizer is None or self.microphone is None:
            return self._read_text_input()

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source,
                    timeout=self.settings.listen_timeout,
                    phrase_time_limit=self.settings.phrase_time_limit,
                )
            return self.recognizer.recognize_google(audio).strip()
        except Exception:
            self.speak("I could not understand that. Please type the command instead.")
            return self._read_text_input()

    def _read_text_input(self) -> str:
        try:
            return self.input_provider("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"

    def wish_me(self) -> None:
        hour = self.now_provider().hour
        if hour < 12:
            self.speak("Good morning, sir.")
        elif hour < 18:
            self.speak("Good afternoon, sir.")
        else:
            self.speak("Good evening, sir.")
        self.speak("I am Jarvis. How can I assist you today?")

    def open_website(self, site: str) -> None:
        url = site.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            self.open_url(url)
            self.speak(f"Opening {url}")
        except Exception:
            self.speak("I could not open that website.")

    def search_web(self, query: str) -> None:
        clean_query = query.strip()
        if not clean_query:
            self.speak("What should I search for?")
            clean_query = self.listen()
        if clean_query:
            self.open_website("https://www.google.com/search?q=" + quote_plus(clean_query))

    def check_weather(self, location: str) -> None:
        clean_location = location.strip()
        if not clean_location:
            self.speak("Which city should I check?")
            clean_location = self.listen().strip()

        query = "weather near me"
        if clean_location:
            query = f"weather in {clean_location}"
        self.open_website("https://www.google.com/search?q=" + quote_plus(query))

    def open_app(self, app_name: str) -> None:
        clean_name = app_name.strip()
        if not clean_name:
            self.speak("Which application should I open?")
            clean_name = self.listen()

        executable = self.APP_ALIASES.get(clean_name.lower(), clean_name)
        if executable and self.launch_app(executable):
            self.speak(f"Opening {clean_name}")
        else:
            self.speak("I could not open that application.")

    def remember(self, text: str) -> None:
        memory = text.strip()
        if not memory:
            self.speak("What should I remember?")
            memory = self.listen()

        if not memory:
            self.speak("No memory was saved.")
            return

        self._write_text(self.settings.memory_file, memory)
        self.speak("I have saved that memory.")

    def recall_memory(self) -> None:
        if self.settings.memory_file.exists():
            memory = self.settings.memory_file.read_text(encoding="utf-8").strip()
            self.speak(memory or "There is no saved memory yet.")
        else:
            self.speak("There is no saved memory yet.")

    def write_note(self, note: str) -> None:
        clean_note = note.strip()
        if not clean_note:
            self.speak("No note was saved.")
            return

        self._write_text(self.settings.note_file, clean_note)
        self.speak("Your note has been saved.")

    def append_note(self, note: str) -> None:
        clean_note = note.strip()
        if not clean_note:
            self.speak("No note was saved.")
            return

        note_file = self.settings.note_file
        note_file.parent.mkdir(parents=True, exist_ok=True)
        existing = note_file.read_text(encoding="utf-8").rstrip() if note_file.exists() else ""
        note_file.write_text((existing + "\n" + clean_note).strip() + "\n", encoding="utf-8")
        self.speak("Your note has been updated.")

    def read_note(self) -> None:
        if self.settings.note_file.exists():
            note = self.settings.note_file.read_text(encoding="utf-8").strip()
            self.speak(note or "No note has been saved yet.")
        else:
            self.speak("No note has been saved yet.")

    def search_wikipedia(self, query: str) -> None:
        clean_query = query.strip()
        if not clean_query:
            self.speak("What should I search on Wikipedia?")
            clean_query = self.listen()

        if not clean_query:
            self.speak("No Wikipedia search was requested.")
            return

        wikipedia = _optional_import("wikipedia")
        if wikipedia is None:
            self.speak("Wikipedia support is not available. Install the wikipedia package to enable it.")
            return

        try:
            result = wikipedia.summary(clean_query, sentences=2)
            self.speak(result)
        except Exception:
            self.speak("I could not find a result for that topic.")

    def tell_joke(self) -> None:
        pyjokes = _optional_import("pyjokes")
        if pyjokes is None:
            self.speak("Joke support is not available. Install the pyjokes package to enable it.")
            return

        try:
            self.speak(pyjokes.get_joke())
        except Exception:
            self.speak("I could not think of a joke right now.")

    def help_text(self) -> str:
        return (
            "You can ask me to open websites, search Google, tell the time or date, "
            "search Wikipedia, write or read notes, remember details, open simple apps, "
            "or tell a joke."
        )

    def handle_command(self, query: str) -> bool:
        original = query.strip()
        text = original.lower()
        if not text:
            return True

        if _contains_any(text, self.EXIT_PHRASES):
            self.speak("Goodbye, sir.")
            return False

        if "shutdown" in text:
            self.speak("Shutting down the system is not enabled in this version.")
        elif _contains_any(text, ("hello", "hi jarvis", "hi there", "hey jarvis")):
            self.speak(random.choice(["Hello, sir.", "Hi there, sir.", "How can I help you today?"]))
        elif re.search(r"\b(time|current time)\b", text):
            self.speak(self.now_provider().strftime("The time is %I:%M %p"))
        elif re.search(r"\b(date|today)\b", text):
            self.speak(self.now_provider().strftime("Today is %A, %B %d, %Y"))
        elif self._handle_known_website(text):
            pass
        elif self._handle_generic_open_website(original):
            pass
        elif self._handle_known_app(text):
            pass
        elif self._handle_generic_open_app(original):
            pass
        elif "weather" in text:
            self.check_weather(self._extract_weather_location(original))
        elif "wikipedia" in text:
            self.search_wikipedia(self._extract_wikipedia_query(original))
        elif text.startswith(("search for ", "google ", "search google for ")):
            search_query = _extract_after(original, ("search google for", "search for", "google"))
            self.search_web(search_query)
        elif "write a note" in text or "take a note" in text:
            self.speak("What should I write?")
            self.write_note(self.listen())
        elif "append note" in text or "add to note" in text:
            self.speak("What should I add?")
            self.append_note(self.listen())
        elif "show note" in text or "read note" in text:
            self.read_note()
        elif "remember that" in text or text.startswith("remember "):
            self.remember(_extract_after(original, ("remember that", "remember")))
        elif "do you remember" in text or "what do you remember" in text:
            self.recall_memory()
        elif "joke" in text:
            self.tell_joke()
        elif "help" in text:
            self.speak(self.help_text())
        else:
            self.speak("I did not understand that command. Say help if you want options.")
        return True

    def run(self) -> None:
        self.wish_me()
        while True:
            self.speak("Listening...")
            query = self.listen()
            if not query:
                continue
            if not self.handle_command(query):
                break

    def _handle_known_website(self, text: str) -> bool:
        for alias, url in self.WEBSITE_ALIASES.items():
            if f"open {alias}" in text:
                self.open_website(url)
                return True
        return False

    def _handle_generic_open_website(self, command: str) -> bool:
        match = re.search(r"\bopen (?:website )?([a-z0-9.-]+\.[a-z]{2,})(?:\s|$)", command, re.IGNORECASE)
        if not match:
            return False
        self.open_website(match.group(1))
        return True

    def _handle_known_app(self, text: str) -> bool:
        for alias in self.APP_ALIASES:
            if f"open {alias}" in text:
                self.open_app(alias)
                return True
        return False

    def _handle_generic_open_app(self, command: str) -> bool:
        match = re.search(r"\bopen (?:app|application) ([\w .-]+)$", command, re.IGNORECASE)
        if not match:
            return False
        self.open_app(match.group(1))
        return True

    def _extract_wikipedia_query(self, command: str) -> str:
        patterns = (
            r"^\s*search\s+wikipedia\s+for\s+(?P<query>.+)$",
            r"^\s*search\s+(?P<query>.+)\s+on\s+wikipedia\s*$",
            r"^\s*search\s+wikipedia\s+(?P<query>.+)$",
            r"^\s*wikipedia\s+(?P<query>.+)$",
        )
        for pattern in patterns:
            match = re.match(pattern, command, re.IGNORECASE)
            if match:
                return match.group("query").strip()
        return command.replace("wikipedia", "", 1).strip(" .,:;-")

    def _extract_weather_location(self, command: str) -> str:
        patterns = (
            r"\bweather\s+(?:in|at|for)\s+(?P<location>.+)$",
            r"\b(?:temperature|forecast)\s+(?:in|at|for)\s+(?P<location>.+)$",
        )
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group("location").strip(" .,:;-")
        return ""

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
