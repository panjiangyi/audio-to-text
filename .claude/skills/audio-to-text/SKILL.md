---
name: audio-to-text
description: Transcribe audio/video files to SRT subtitles using faster-whisper
---

# Audio-to-Text: Speech-to-Text Skill

This skill transcribes audio or video files into SRT subtitle files using faster-whisper.

## When to Use

- User asks to transcribe audio/video to text
- User mentions generating subtitles or captions
- User has a media file that needs speech-to-text conversion

## How to Invoke

Use the `att stt` command:

```bash
att stt /absolute/path/to/video.mp4
```

### Common Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `small` | Whisper model size (tiny/small/medium/large-v3) |
| `--language` | `zh` | Language code (zh/en/ja/...) |
| `--device` | `cpu` | Device (cpu/cuda) |
| `--suffix` | `zh` | Output suffix (produces `<stem>.<suffix>.srt`) |
| `--on-exists` | `rename` | What if SRT exists (rename/overwrite/skip) |
| `--vad-filter` | `True` | Enable voice activity detection |

### Examples

```bash
# Basic transcription (Chinese)
att stt /path/to/video.mp4

# English transcription with larger model
att stt /path/to/podcast.mp3 --language en --model medium

# Overwrite existing subtitle
att stt /path/to/video.mp4 --on-exists overwrite

# Use GPU (requires CUDA + cuDNN)
att stt /path/to/video.mp4 --device cuda --model large-v3
```

## Output

- Creates `<video_stem>.<suffix>.srt` next to the input file
- Default: `video.zh.srt` for Chinese transcription

## Prerequisites

1. **audio-to-text installed**:
   ```bash
   cd /mnt/data/james/Documents/sidework/audio-to-text
   uv sync
   uv pip install -e .
   ```

2. **ffmpeg** installed and in PATH:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y ffmpeg
   ```

3. **att command available** in shell

## Workflow

1. Accept audio/video path from user
2. Run `att stt <path>` with appropriate options
3. Report the output SRT file location
4. Optionally preview first few subtitle entries

## Notes

- First run downloads the Whisper model (can be slow)
- GPU acceleration requires CUDA + cuDNN setup
- Supports: .mp4, .mkv, .avi, .mp3, .wav, .m4a, .ogg, .opus, .flac
