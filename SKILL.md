---
name: audio-to-text
description: Transcribe local audio/video to plain text or SRT subtitles with the `att` CLI (faster-whisper), proofread SRT captions against user-provided context/terminology, and burn SRT subtitles into video with ffmpeg. Use for speech-to-text, subtitles, captions, caption correction/proofreading, or hardcoding subtitles into a video.
---

# Audio to Text

Use this skill when the user wants to turn a local audio/video file into text or
subtitles, fix/proofread subtitle text, or burn subtitles into a video. The work
uses the local `att` CLI (faster-whisper) plus ffmpeg — fully offline, no API keys.

## When to use — route by what the user asks for

| The user wants... | Do this | Output |
|---|---|---|
| speech as plain text | Section 1, `att stt <file>` (default) | text to stdout |
| subtitles / captions with timestamps | Section 1, `att stt <file> --output srt` | `<name>.<lang>.srt` |
| better recognition of names / jargon | add `--context "<terms>"` (Section 2) | same output, fewer errors |
| subtitle text corrected from context they provide | Section 3 — **you** proofread | `<name>.proofed.srt` |
| subtitles burned (hardcoded) into the video | Section 4 — ffmpeg | `<name>.subbed.mp4` |

**Model choice:** `small` (default) is fast but misrecognizes proper nouns and
jargon. For accuracy either rerun with `--model medium`, **or** keep `small` and
fix mistakes via Section 3 — both work; proofreading is usually cheaper.

**Prerequisite:** `att` must be on PATH. If `att` is not found, run `./install.sh`
in this repo (see Install below), or invoke the entrypoint directly as
`uv run att ...` from the repo root. Transcription (1–2) is purely local;
proofreading (3) is done by you (Claude) — the CLI only rebuilds safely so
timestamps can never be corrupted; burning (4) is an ffmpeg command.

## Install

```bash
./install.sh
```

The installer will:

- install `ffmpeg` if needed
- install `uv` if needed
- install project dependencies with `uv sync`
- create `~/.local/bin/att`
- add `~/.local/bin` to your shell `PATH`

If `att` is not on `PATH` right after install, reload your shell config or open
a new terminal. You can also run the local entrypoint directly: `uv run att ...`.

## 1. Transcribe

Plain text to stdout (default):

```bash
att stt /path/to/audio.mp3
att stt /path/to/audio.mp3 > transcript.txt
```

SRT subtitles, written next to the input as `<name>.<lang>.srt`:

```bash
att stt /path/to/video.mp4 --output srt
```

Custom output path:

```bash
att stt /path/to/audio.mp3 --output srt --output-path /tmp/out.srt
```

Common options: `--language zh|en|ja`, `--model small|medium|large-v3`,
`--device cpu|cuda`, `--vad-filter/--no-vad-filter`. Video input is accepted;
the CLI extracts a temporary WAV with ffmpeg first. If `cuda` is requested but
cuDNN is missing, it falls back to CPU.

## 2. Terminology hint before transcribing (`--context`)

Pass a short list of names/jargon to bias recognition toward the right terms:

```bash
att stt /path/to/video.mp4 --output srt --context "Kubernetes, etcd, CRD, 控制器"
```

`--context` is forwarded to faster-whisper as `initial_prompt`. Important:

- It only biases the **first decoding window** — a hint, not a global rule.
- Keep it to a short term list (tens of characters). Long background passages
  add no benefit and may interfere with segmentation.
- It is **pre-transcription guidance**; section 3 is **post-transcription
  correction**. They compose — use both when accuracy matters.

## 3. Proofread SRT captions (LLM workflow)

When the user gives context (slides, a glossary, domain knowledge) and wants the
SRT text corrected, follow this flow. **Do not hand-edit the SRT file** — the
rebuild tool is what keeps timestamps safe.

### Step 1 — extract the current texts

```bash
att srt /abs/path/video.zh.srt
```

Prints `[N entries]` (stderr) and one current text line per entry (stdout).

### Step 2 — you produce the corrected texts

You (Claude) are the proofreader. Using the user's context (slides, glossary,
domain knowledge), correct each entry and write the results — **one corrected
line per entry** — to a temp file such as `/tmp/corpus.txt` with your Write
tool. Rules:

- Exactly `N` lines — same count and order as step 1.
- One subtitle per line. **Never merge two originals into one line, never split
  one original into multiple lines.**
- Fix only: domain terminology, proper nouns, obvious misrecognition, clearly
  wrong punctuation.
- If a line is uncertain, copy the original line verbatim — do not invent.
- Text only on each line. No index numbers, no timestamps, no commentary.

### Step 3 — rebuild

```bash
att srt /abs/path/video.zh.srt --apply /tmp/corpus.txt \
    --output-path /abs/path/video.proofed.srt
```

The CLI re-renders the SRT with the **original timestamps** and your corrected
texts. Default output is `<name>.proofed.srt`; `--output-path` overrides it
(including writing back over the input).

If your line count ≠ entry count, the CLI **refuses, prints both counts, and
writes nothing** — re-read step 1, fix your file, and retry.

### Fallback prompt template (only if `att srt` is unavailable)

If you must edit the SRT by hand, use this prompt and follow it exactly:

> You are proofreading an SRT caption file given the user's context. Output a
> COMPLETE, VALID SRT and nothing else. Change ONLY subtitle text lines. Keep
> every index line, every timestamp line (`HH:MM:SS,mmm`), and every blank line
> exactly as received — do not renumber, reformat, merge, or split entries; the
> total entry count must not change. Edit only terminology, proper nouns, obvious
> misrecognition, and clearly wrong punctuation to match the context. If a line
> is uncertain, leave it unchanged.

Prefer the `att srt --apply` flow; this template is a fallback only.

## 4. Burn SRT subtitles into a video (ffmpeg)

Prerequisites: ffmpeg built with libass, and a CJK font for Chinese captions.

```bash
# libass present?
ffmpeg -filters 2>/dev/null | grep -q subtitles && echo "libass OK"
# a Chinese font present?
fc-list :lang=zh | grep -i "Noto Sans CJK SC"
```

Burn (verified parameters; Chinese uses Noto Sans CJK SC, white text + black outline):

```bash
ffmpeg -y -i /abs/path/video.mp4 \
  -vf "subtitles='/abs/path/video.zh.srt':force_style='FontName=Noto Sans CJK SC,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=28'" \
  -c:v libx264 -crf 23 -preset medium -c:a copy \
  /abs/path/video.subbed.mp4
```

Notes:

- Use an **absolute path** for the `.srt` inside `subtitles=` (avoids ffmpeg
  working-directory ambiguity). On Windows, escape `:` in the drive letter.
- `force_style` colours are `&H00BBGGRR` (alpha + blue + green + red).
- `-c:a copy` avoids re-encoding audio; `-crf 23 -preset medium` is a sane
  quality/speed default (lower CRF = higher quality / larger file).
- To verify, extract a frame and view it:
  `ffmpeg -y -ss 00:00:10 -i out.mp4 -frames:v 1 /tmp/frame.png`.

## Notes

- Transcription and the CLI are fully local; no API keys or network are needed
  for steps 1–2.
- Proofreading (step 3) requires you (Claude); the CLI only rebuilds safely.
- Burning (step 4) requires ffmpeg with libass.
