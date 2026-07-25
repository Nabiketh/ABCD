from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from jarvis_assistant import JarvisAssistant, JarvisSettings


class JarvisAssistantTests(unittest.TestCase):
    def make_assistant(self, temp_dir: Path, inputs=None, now=None):
        outputs = []
        opened_urls = []
        launched_apps = []
        pending_inputs = list(inputs or [])
        settings = JarvisSettings(
            note_file=temp_dir / "notes.txt",
            memory_file=temp_dir / "memory.txt",
            enable_voice=False,
            enable_speech_recognition=False,
        )

        def input_provider(prompt: str) -> str:
            return pending_inputs.pop(0) if pending_inputs else ""

        assistant = JarvisAssistant(
            settings=settings,
            output=outputs.append,
            input_provider=input_provider,
            now_provider=now or (lambda: dt.datetime(2026, 7, 25, 22, 30)),
            open_url=opened_urls.append,
            launch_app=lambda app_name: launched_apps.append(app_name) or True,
        )
        return assistant, outputs, opened_urls, launched_apps

    def test_time_command_uses_current_time_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, outputs, _, _ = self.make_assistant(Path(directory))

            should_continue = assistant.handle_command("what time is it")

            self.assertTrue(should_continue)
            self.assertEqual(outputs[-1], "The time is 10:30 PM")

    def test_note_command_writes_user_note(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            assistant, outputs, _, _ = self.make_assistant(temp_dir, inputs=["Ship the project"])

            assistant.handle_command("take a note")

            self.assertEqual((temp_dir / "notes.txt").read_text(encoding="utf-8"), "Ship the project")
            self.assertEqual(outputs[-1], "Your note has been saved.")

    def test_memory_command_preserves_original_case(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            assistant, outputs, _, _ = self.make_assistant(temp_dir)

            assistant.handle_command("Remember that My project name is ABCD")

            self.assertEqual((temp_dir / "memory.txt").read_text(encoding="utf-8"), "My project name is ABCD")
            self.assertEqual(outputs[-1], "I have saved that memory.")

    def test_open_google_uses_url_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, outputs, opened_urls, _ = self.make_assistant(Path(directory))

            assistant.handle_command("open google")

            self.assertEqual(opened_urls, ["https://www.google.com"])
            self.assertEqual(outputs[-1], "Opening https://www.google.com")

    def test_open_whatsapp_uses_whatsapp_web(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, outputs, opened_urls, _ = self.make_assistant(Path(directory))

            assistant.handle_command("open whatsapp")

            self.assertEqual(opened_urls, ["https://web.whatsapp.com"])
            self.assertEqual(outputs[-1], "Opening https://web.whatsapp.com")

    def test_weather_command_asks_for_city_then_searches(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, outputs, opened_urls, _ = self.make_assistant(Path(directory), inputs=["Mumbai"])

            assistant.handle_command("how is weather")

            self.assertEqual(outputs[0], "Which city should I check?")
            self.assertEqual(opened_urls, ["https://www.google.com/search?q=weather+in+Mumbai"])

    def test_weather_command_can_include_city(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, _, opened_urls, _ = self.make_assistant(Path(directory))

            assistant.handle_command("weather in Delhi")

            self.assertEqual(opened_urls, ["https://www.google.com/search?q=weather+in+Delhi"])

    def test_exit_command_stops_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            assistant, outputs, _, _ = self.make_assistant(Path(directory))

            should_continue = assistant.handle_command("goodbye")

            self.assertFalse(should_continue)
            self.assertEqual(outputs[-1], "Goodbye, sir.")


if __name__ == "__main__":
    unittest.main()
