from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class FfmpegNotFoundError(RuntimeError):
    pass


def require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FfmpegNotFoundError(
            "ffmpeg not found in PATH. Please install ffmpeg and retry."
        )
    return ffmpeg


@dataclass(frozen=True)
class TempAudio:
    path: Path

    def cleanup(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass


def extract_audio_to_temp_wav(
    video_path: Path,
    *,
    sample_rate: int = 16000,
    mono: bool = True,
) -> TempAudio:
    """
    Extract audio from a video into a temporary WAV file (pcm_s16le).
    This keeps the user's folder clean and avoids intermediate artifacts.
    """
    require_ffmpeg()
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    tmp = tempfile.NamedTemporaryFile(prefix="att_", suffix=".wav", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(sample_rate),
    ]
    if mono:
        cmd += ["-ac", "1"]
    cmd += [str(tmp_path)]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or "").strip()
        tail = "\n".join(msg.splitlines()[-20:]) if msg else ""
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise RuntimeError(f"ffmpeg failed while extracting audio.\n{tail}") from e
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return TempAudio(path=tmp_path)
