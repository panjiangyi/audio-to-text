from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SrtSegment:
    start: float
    end: float
    text: str


def format_timestamp(seconds: float) -> str:
    if seconds is None:
        seconds = 0.0
    # Round to the nearest millisecond (avoids float drift, e.g. 2.799s
    # rendering as ",798") so parse -> format round-trips losslessly.
    total_ms = round(float(seconds) * 1000)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


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


_TS_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})")


def _parse_timestamp(value: str) -> float:
    """
    Inverse of format_timestamp. Accepts ',' or '.' as the millisecond
    separator and tolerates 1-2 digit hours / 1-3 digit milliseconds.
    Raises ValueError if the string is not a valid SRT timestamp.
    """
    m = _TS_RE.fullmatch(value.strip())
    if m is None:
        raise ValueError(f"Invalid timestamp: {value!r}")
    hours, minutes, seconds, millis = (int(g) for g in m.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_srt(content: str) -> list[SrtSegment]:
    """
    Parse an SRT string into segments.

    Tolerant of: leading UTF-8 BOM, CRLF/CR/LF endings, missing trailing
    blank line, and non-sequential/missing index numbers (the index line is
    ignored; order follows the physical block order).

    Raises ValueError on unrecoverable structural errors (a block without a
    timestamp line, a malformed timestamp, or empty content).
    """
    content = content.lstrip("﻿")
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ newlines so blank-line splitting is stable.
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    if not content:
        raise ValueError("Empty SRT content")

    segments: list[SrtSegment] = []
    for i, block in enumerate(content.split("\n\n")):
        lines = block.split("\n")
        # First line is the (optional, ignored) index. The timestamp line is
        # the first one containing ' --> '.
        ts_index = next(
            (j for j, line in enumerate(lines) if "-->" in line), None
        )
        if ts_index is None:
            raise ValueError(f"Block {i + 1}: missing timestamp line")
        start_str, _, end_str = lines[ts_index].partition("-->")
        try:
            start = _parse_timestamp(start_str)
            end = _parse_timestamp(end_str)
        except ValueError as exc:
            raise ValueError(f"Block {i + 1}: {exc}") from exc
        text = "\n".join(lines[ts_index + 1 :]).strip()
        segments.append(SrtSegment(start=start, end=end, text=text))

    return segments
