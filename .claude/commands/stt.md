---
allowed-tools:
  - Bash
---

Transcribe an audio or video file to SRT subtitles.

Usage: `/stt <path> [options]`

## Examples

- `/stt /path/to/video.mp4` - Transcribe Chinese speech
- `/stt /path/to/podcast.mp3 --language en` - Transcribe English
- `/stt /path/to/video.mp4 --model medium --device cuda` - Use larger model with GPU

## Instructions

1. Parse the user's file path and any options from the command arguments
2. Run the transcription command:
   ```bash
   att stt <path> [options]
   ```
3. Report the output SRT file location

If no path is provided, ask the user for the media file path.
