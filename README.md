# Audio-to-Text

Transcribe audio/video to plain text or timestamped SRT subtitles using faster-whisper.

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

# Generate timestamped SRT subtitles next to the input
att stt /path/to/video.mp4 --output srt

# Custom output path
att stt /path/to/audio.mp3 --output srt --output-path /tmp/out.srt

# Bias recognition with a short terminology hint (faster-whisper initial_prompt)
att stt /path/to/video.mp4 --output srt --context "Kubernetes, etcd, CRD"
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
| `--output` | `txt` | Output format (`txt` or `srt`) |
| `--output-path` | — | Write to a custom file path |
| `--context` | — | Terminology hint passed to faster-whisper (`initial_prompt`) |

## Proofreading & Burning

`att` also has an `srt` subcommand for safe caption proofreading, and subtitle
burn-in is done with ffmpeg. See `SKILL.md` for the full workflow; quick form:

```bash
# Print current caption texts (one per line) for proofreading
att srt /path/to/video.zh.srt
# Rebuild with corrected texts (one per line), keeping original timestamps
att srt /path/to/video.zh.srt --apply /tmp/corpus.txt \
    --output-path /path/to/video.proofed.srt
```

Burn subtitles into a video (Chinese: Noto Sans CJK SC):

```bash
ffmpeg -y -i video.mp4 \
  -vf "subtitles='/abs/video.zh.srt':force_style='FontName=Noto Sans CJK SC,FontSize=22,Outline=2,MarginV=28'" \
  -c:v libx264 -crf 23 -preset medium -c:a copy video.subbed.mp4
```

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
