---
name: audio-to-text
description: Use when the user wants to transcribe a local audio or video file into plain text from the command line with this project. Covers installation, the global `att` command, and common transcription commands.
---

# Audio to Text

Use this skill when the task is to convert a local audio or video file into plain text with the CLI in this repository.

## Install

Run:

```bash
./install.sh
```

The installer will:

- install `ffmpeg` if needed
- install `uv` if needed
- install project dependencies with `uv sync`
- create `~/.local/bin/att`
- add `~/.local/bin` to your shell `PATH`

## Quick Start

Run transcription with:

```bash
att stt /path/to/audio.mp3
```

The command writes the transcript to stdout.

Save the result into a file:

```bash
att stt /path/to/audio.mp3 > transcript.txt
```

## Common Commands

Chinese transcription:

```bash
att stt /path/to/audio.mp3
```

English transcription:

```bash
att stt /path/to/audio.mp3 --language en
```

Use a larger model:

```bash
att stt /path/to/audio.mp3 --model medium
```

Try GPU acceleration:

```bash
att stt /path/to/audio.mp3 --device cuda --model large-v3
```

If `cuda` is requested but `cuDNN` is unavailable, the CLI falls back to CPU automatically.

Local project entrypoint:

```bash
uv run att stt /path/to/audio.mp3
```

## Supported Inputs

The CLI accepts local audio files such as `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`, and `.opus`.

It also accepts local video files. For video input, the CLI extracts a temporary WAV with `ffmpeg` before transcription.

## Useful Options

- `--model`: whisper model, for example `tiny`, `small`, `medium`, `large-v3`
- `--language`: language code such as `zh`, `en`, `ja`
- `--device`: `cpu` or `cuda`
- `--compute-type`: advanced inference mode such as `auto`, `int8`, `float16`
- `--vad-filter`: enable or disable VAD filtering
- `--keep-temp-audio`: keep extracted temporary WAV files for debugging

## Workflow

1. Confirm the input file exists locally.
2. Run `att stt /absolute/path/to/file`.
3. If needed, add `--language`, `--model`, or `--device`.
4. Redirect stdout to a text file if the transcript should be saved.

## Notes

- This CLI outputs plain text, not structured subtitles.
- `ffmpeg` is required when the input is a video file or a non-WAV source that needs conversion.
- In root or container environments without `sudo`, `install.sh` runs package manager commands directly.
