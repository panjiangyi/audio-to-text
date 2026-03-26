from __future__ import annotations

import ctypes
import ctypes.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WhisperSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    device_used: str
    segments: list[WhisperSegment]


def has_cudnn() -> bool:
    """
    Best-effort check whether cuDNN is available on the system.
    Avoids hard crashes when attempting to use CUDA without cuDNN.
    """
    # Common sonames across distros / versions.
    candidates = [
        "libcudnn_ops.so.9.1.0",
        "libcudnn_ops.so.9.1",
        "libcudnn_ops.so.9",
        "libcudnn_ops.so",
        "libcudnn.so.9.1.0",
        "libcudnn.so.9.1",
        "libcudnn.so.9",
        "libcudnn.so",
    ]
    for name in candidates:
        try:
            ctypes.CDLL(name)
            return True
        except OSError:
            continue
        except Exception:
            continue

    # Fallback to linker lookup.
    for key in ["cudnn", "cudnn_ops"]:
        try:
            found = ctypes.util.find_library(key)
            if found:
                ctypes.CDLL(found)
                return True
        except OSError:
            continue
        except Exception:
            continue

    return False


def _auto_device() -> str:
    """
    Best-effort device selection for faster-whisper (CTranslate2 backend).
    """
    # IMPORTANT: On some systems ctranslate2's CUDA probing can crash hard
    # when cuDNN is missing/misconfigured. For reliability, default to CPU
    # unless the user explicitly requests CUDA.
    return "cpu"


def transcribe(
    audio_path: Path,
    *,
    model: str = "small",
    language: str = "zh",
    device: str = "auto",
    compute_type: str = "auto",
    vad_filter: bool = True,
) -> TranscriptionResult:
    """
    Transcribe an audio file using faster-whisper and return timestamped segments.
    """
    from faster_whisper import WhisperModel  # type: ignore

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    if device == "auto":
        device = _auto_device()

    def _make_model(dev: str) -> Any:
        return WhisperModel(model, device=dev, compute_type=compute_type)

    try:
        model_obj = _make_model(device)
        device_used = device
    except Exception as e:
        msg = str(e)
        cudnn_related = any(
            s in msg.lower()
            for s in [
                "cudnn",
                "libcudnn",
                "cublas",
                "cuda",
                "cannot load symbol",
                "invalid handle",
            ]
        )
        # If CUDA isn't usable (often missing cuDNN), fall back to CPU for robustness.
        if device == "cuda" and cudnn_related:
            model_obj = _make_model("cpu")
            device_used = "cpu"
        else:
            raise
    segments_iter, _info = model_obj.transcribe(
        str(audio_path),
        language=language,
        vad_filter=vad_filter,
    )

    out: list[WhisperSegment] = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        if not text:
            continue
        out.append(
            WhisperSegment(start=float(seg.start), end=float(seg.end), text=text)
        )
    return TranscriptionResult(device_used=device_used, segments=out)
