from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SrtSegment:
    start: float
    end: float
    text: str


def format_timestamp(seconds: float) -> str:
    if seconds is None:
        seconds = 0.0
    seconds = float(seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = seconds % 60
    milliseconds = int((sec - int(sec)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(sec):02d},{milliseconds:03d}"


def segments_to_srt(segments: list[SrtSegment]) -> str:
    """
    Minimal, robust SRT rendering: one entry per segment.
    """
    lines: list[str] = []
    idx = 1
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        lines.append(str(idx))
        lines.append(f"{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}")
        lines.append(text)
        lines.append("")
        idx += 1
    return "\n".join(lines).rstrip() + "\n"
