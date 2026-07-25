# ABCD Jarvis Assistant

A small Jarvis-style assistant that can run from the terminal, with optional
voice input/output when the required packages and microphone support are
available.

## What It Can Do

- Greet the user.
- Tell the current time and date.
- Open common websites such as Google, YouTube, Gmail, GitHub, Stack Overflow,
  and WhatsApp Web.
- Search Google from a command.
- Check weather results in the browser.
- Open simple desktop applications such as Notepad, Chrome, Calculator, and
  Paint.
- Save, append, and read notes.
- Remember and recall one saved detail.
- Search Wikipedia when the optional `wikipedia` package is installed.
- Tell a joke when the optional `pyjokes` package is installed.

## Project Structure

```text
ABCD-main/
  Jarvis source code          # Backward-compatible launcher
  jarvis.py                   # Normal Python launcher
  pyproject.toml              # Package metadata
  requirements.txt            # Optional runtime dependencies
  src/jarvis_assistant/
    assistant.py              # Core command handling
    cli.py                    # Command-line interface
    settings.py               # Runtime configuration
  tests/
    test_assistant.py         # Unit tests for the core behavior
```

## Run

Terminal-only mode works without installing any optional packages:

```bash
python jarvis.py --text-only
```

You can also run a single command and exit:

```bash
python jarvis.py --text-only --command "what time is it"
```

Example commands:

```text
open whatsapp
weather in Delhi
how is weather
search for Python tutorials
take a note
exit
```

The original launcher still works:

```bash
python "Jarvis source code" --text-only
```

## Optional Voice Features

Install the optional runtime packages if you want text-to-speech,
speech-recognition, jokes, and Wikipedia support:

```bash
python -m pip install -r requirements.txt
```

Some systems also require microphone/audio drivers or PyAudio support for
speech recognition. If voice setup is unavailable, Jarvis automatically falls
back to terminal input.

## Test

```bash
python -m unittest discover -s tests
python -m compileall .
```
