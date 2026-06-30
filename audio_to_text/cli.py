from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer
from rich.console import Console

from .io import resolve_output_srt_path, write_text_atomic
from .media import FfmpegNotFoundError, extract_audio_to_temp_wav
from .stt.faster_whisper_engine import has_cudnn, transcribe
from .subtitles.srt import SrtSegment, parse_srt, segments_to_srt

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()
stderr_console = Console(stderr=True)


class OutputFormat(str, Enum):
    txt = "txt"
    srt = "srt"


@app.callback()
def _root() -> None:  # pyright: ignore[reportUnusedFunction]
    """
    att: audio/video to text (SRT subtitles).
    """
    return


@app.command()
def stt(
    audio_file_path: Path = typer.Argument(..., exists=True, readable=True),
    model: str = typer.Option(
        "small", help="faster-whisper model name/path (e.g. small, medium)"
    ),
    language: str = typer.Option("zh", help="Language code (e.g. zh, en)"),
    device: str = typer.Option(
        "cpu", help="cpu/cuda (use cuda only if you have a working CUDA+cuDNN setup)"
    ),
    compute_type: str = typer.Option("auto", help="auto/int8/float16/... (advanced)"),
    vad_filter: bool = typer.Option(True, help="Enable VAD filtering (recommended)"),
    keep_temp_audio: bool = typer.Option(
        False, help="Keep extracted temp WAV (for debugging)"
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.txt,
        help="Output format: txt (plain text) or srt (timestamped subtitles)",
    ),
    output_path: Path | None = typer.Option(
        None,
        "--output-path",
        help="Write to this file instead of stdout (txt) / default SRT path (srt)",
    ),
    context: str | None = typer.Option(
        None,
        "--context",
        help="Optional terminology/hint passed to faster-whisper as "
        "initial_prompt (e.g. names, jargon). Keep it short - it only "
        "biases the first decoding window.",
    ),
) -> None:
    """
    Transcribe a local audio or video file.

    Output:
      - txt (default): plain text to stdout.
      - srt: timestamped SRT subtitles, written next to the input as
        <name>.<lang>.srt (or to --output-path).
    """
    audio_file_path = Path(audio_file_path)

    try:
        stderr_console.print(f"[cyan]Input:[/cyan] {audio_file_path}")

        audio_exts = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
        tmp_audio = None
        audio_path = audio_file_path

        if device == "cuda" and not has_cudnn():
            stderr_console.print(
                "[yellow]--device cuda requested but cuDNN was not found. "
                "Falling back to CPU to avoid a crash. "
                "Install cuDNN to use GPU.[/yellow]"
            )
            device = "cpu"

        if audio_file_path.suffix.lower() not in audio_exts:
            with console.status("Extracting audio (temp)..."):
                tmp_audio = extract_audio_to_temp_wav(audio_file_path)
            audio_path = tmp_audio.path

        try:
            with console.status(f"Transcribing with faster-whisper ({model})..."):
                result = transcribe(
                    audio_path,
                    model=model,
                    language=language,
                    device=device,
                    compute_type=compute_type,
                    vad_filter=vad_filter,
                    initial_prompt=context,
                )

            if device == "cuda" and result.device_used != "cuda":
                stderr_console.print(
                    "[yellow]CUDA requested but unavailable (likely missing cuDNN). "
                    "Falling back to CPU.[/yellow]"
                )

            if output is OutputFormat.srt:
                content = segments_to_srt(
                    [
                        SrtSegment(start=seg.start, end=seg.end, text=seg.text)
                        for seg in result.segments
                    ]
                )
            else:
                content = "\n".join(
                    segment.text for segment in result.segments
                ).strip()

            if output_path is not None:
                out_path = Path(output_path)
                write_text_atomic(out_path, content)
                stderr_console.print(
                    f"[green]Wrote {output.value.upper()}:[/green] {out_path}"
                )
            elif output is OutputFormat.srt:
                out_path = resolve_output_srt_path(
                    audio_file_path, suffix=language
                )
                if out_path is not None:
                    write_text_atomic(out_path, content)
                    stderr_console.print(
                        f"[green]Wrote SRT:[/green] {out_path}"
                    )
            else:
                if content:
                    typer.echo(content)

            if tmp_audio is not None:
                if keep_temp_audio:
                    stderr_console.print(
                        f"[yellow]Temp audio kept at:[/yellow] {tmp_audio.path}"
                    )
                else:
                    tmp_audio.cleanup()
        except Exception:
            if tmp_audio is not None and not keep_temp_audio:
                tmp_audio.cleanup()
            raise

    except FfmpegNotFoundError as e:
        stderr_console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2)


@app.command()
def srt(
    file: Path = typer.Argument(..., exists=True, readable=True),
    apply: Path | None = typer.Option(
        None,
        "--apply",
        help="Path to a UTF-8 text file with ONE corrected line per subtitle "
        "entry (same count/order as the SRT). Rebuilds the SRT with these "
        "texts and the original timestamps.",
    ),
    output_path: Path | None = typer.Option(
        None,
        "--output-path",
        help="Output path. Default: <name>.proofed.srt next to the input.",
    ),
) -> None:
    """
    Inspect or rebuild an SRT without touching timestamps.

    Without --apply: prints the entry count (stderr) and one text line per
    entry (stdout), for proofreading.

    With --apply: reads the corrected-texts file, asserts the line count
    equals the entry count (refuses and exits 1 on mismatch, writing no
    file), then rebuilds the SRT using the original timestamps.
    """
    content = Path(file).read_text(encoding="utf-8")
    try:
        segments = parse_srt(content)
    except ValueError as exc:
        stderr_console.print(f"[red]Failed to parse {file}:[/red] {exc}")
        raise typer.Exit(code=1)

    if apply is None:
        stderr_console.print(f"[{len(segments)} entries]")
        for seg in segments:
            typer.echo(seg.text)
        return

    corrections = Path(apply).read_text(encoding="utf-8").splitlines()
    # Tolerate a single trailing blank line (editors often append one).
    if corrections and corrections[-1] == "":
        corrections.pop()
    if len(corrections) != len(segments):
        stderr_console.print(
            f"[red]Count mismatch:[/red] SRT has {len(segments)} entries, "
            f"but {apply} has {len(corrections)} lines. "
            "Each entry must map to exactly one line; do not merge or split."
        )
        raise typer.Exit(code=1)

    rebuilt = segments_to_srt(
        [
            SrtSegment(start=seg.start, end=seg.end, text=text)
            for seg, text in zip(segments, corrections)
        ]
    )
    out = (
        Path(output_path)
        if output_path is not None
        else Path(file).with_name(f"{Path(file).stem}.proofed.srt")
    )
    write_text_atomic(out, rebuilt)
    stderr_console.print(f"[green]Wrote SRT:[/green] {out}")


def main() -> None:
    app()
