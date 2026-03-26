# Audio-to-Text

Transcribe audio/video to plain text using faster-whisper.

## Install

```bash
git clone https://github.com/<your-username>/audio-to-text.git
cd audio-to-text
./install.sh
```

**Requirements:** Python 3.12+, ffmpeg

## Usage

```bash
# Basic transcription (Chinese)
uv run att stt /path/to/audio.mp3

# English with larger model
uv run att stt /path/to/podcast.mp3 --language en --model medium

# Use GPU (requires CUDA + cuDNN)
uv run att stt /path/to/audio.wav --device cuda --model large-v3

# Save to file
uv run att stt /path/to/audio.mp3 > transcript.txt
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `small` | Whisper model (tiny/small/medium/large-v3) |
| `--language` | `zh` | Language code (zh/en/ja/...) |
| `--device` | `cpu` | Device (cpu/cuda) |
| `--compute-type` | `auto` | Compute type (auto/int8/float16) |
| `--vad-filter` | `True` | Enable VAD filtering |
| `--keep-temp-audio` | `False` | Keep extracted temp WAV for debugging |

## GPU Support

For CUDA acceleration:
1. Install NVIDIA drivers
2. Install CUDA Toolkit
3. Install cuDNN

If cuDNN is missing, the script will automatically fall back to CPU.

## Claude Code Integration

In Claude Code, use:
```
/stt /path/to/audio.mp3
```

Or ask naturally:
```
Transcribe this audio file: /path/to/audio.mp3
```
