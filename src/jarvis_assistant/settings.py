"""Configuration for the Jarvis assistant."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path


@dataclass
class JarvisSettings:
    """Runtime options for Jarvis.

    Voice and speech recognition are optional so the assistant can run in a
    plain terminal or in environments where microphone/audio packages are not
    installed.
    """

    note_file: Path = Path("jarvis_notes.txt")
    memory_file: Path = Path("jarvis_memory.txt")
    enable_voice: bool = True
    enable_speech_recognition: bool = True
    voice_rate: int = 170
    listen_timeout: int = 5
    phrase_time_limit: int = 5

    def normalized(self) -> "JarvisSettings":
        return replace(
            self,
            note_file=Path(self.note_file).expanduser(),
            memory_file=Path(self.memory_file).expanduser(),
        )
