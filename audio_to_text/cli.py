from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .media import FfmpegNotFoundError, extract_audio_to_temp_wav
from .stt.faster_whisper_engine import has_cudnn, transcribe

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()
stderr_console = Console(stderr=True)


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
) -> None:
    """
    Transcribe a local audio or video file and write plain text to stdout.
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
                )

            if device == "cuda" and result.device_used != "cuda":
                stderr_console.print(
                    "[yellow]CUDA requested but unavailable (likely missing cuDNN). "
                    "Falling back to CPU.[/yellow]"
                )

            text = "\n".join(segment.text for segment in result.segments).strip()
            if text:
                typer.echo(text)

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


def main() -> None:
    app()
