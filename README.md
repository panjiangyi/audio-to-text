# Audio-to-Text

Transcribe audio/video to plain text using faster-whisper.

## Install

```bash
git clone https://github.com/panjiangyi/audio-to-text.git
cd audio-to-text
./install.sh
```

The installer will:

- install `ffmpeg` if needed
- install `uv` if needed
- install the project dependencies
- create a global `att` command in `~/.local/bin`
- add `~/.local/bin` to your shell `PATH`

If the command is not available in the current shell immediately after install, reload your shell config or open a new terminal.

## Usage

```bash
# Basic transcription (Chinese)
att stt /path/to/audio.mp3

# English with larger model
att stt /path/to/podcast.mp3 --language en --model medium

# Use GPU (requires CUDA + cuDNN)
att stt /path/to/audio.wav --device cuda --model large-v3

# Save to file
att stt /path/to/audio.mp3 > transcript.txt
```

You can still run the local project entrypoint directly:

```bash
uv run att stt /path/to/audio.mp3
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

## Notes

- Supported audio inputs include `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`, and `.opus`.
- Video files are also supported. The CLI will extract temporary audio with `ffmpeg` before transcription.
- In root or container environments without `sudo`, `install.sh` will run package manager commands directly.
