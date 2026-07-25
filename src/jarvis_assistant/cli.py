"""Command-line entrypoint for Jarvis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from jarvis_assistant.assistant import JarvisAssistant
from jarvis_assistant.settings import JarvisSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Jarvis assistant.")
    parser.add_argument(
        "-c",
        "--command",
        help='Run one command and exit, for example: --command "what time is it".',
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Use terminal input/output only. This disables voice and microphone setup.",
    )
    parser.add_argument("--no-voice", action="store_true", help="Disable text-to-speech output.")
    parser.add_argument("--no-speech", action="store_true", help="Disable microphone speech recognition.")
    parser.add_argument("--notes-file", type=Path, default=Path("jarvis_notes.txt"), help="Path for saved notes.")
    parser.add_argument(
        "--memory-file",
        type=Path,
        default=Path("jarvis_memory.txt"),
        help="Path for saved memories.",
    )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    text_only = args.text_only
    settings = JarvisSettings(
        note_file=args.notes_file,
        memory_file=args.memory_file,
        enable_voice=not (text_only or args.no_voice),
        enable_speech_recognition=not (text_only or args.no_speech),
    )
    assistant = JarvisAssistant(settings=settings)

    try:
        if args.command:
            assistant.handle_command(args.command)
            return 0
        assistant.run()
        return 0
    except KeyboardInterrupt:
        print("Jarvis stopped.")
        return 130
