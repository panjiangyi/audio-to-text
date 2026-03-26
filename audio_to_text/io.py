from __future__ import annotations

import os
from enum import Enum
from pathlib import Path


class OnExists(str, Enum):
    rename = "rename"
    overwrite = "overwrite"
    skip = "skip"


def resolve_output_srt_path(
    video_path: Path,
    *,
    suffix: str,
    on_exists: OnExists = "rename",
) -> Path | None:
    """
    Return the output path for the SRT next to the video.

    Naming rule:
      - default: <video_stem>.<suffix>.srt  (if suffix is truthy)
      - else:    <video_stem>.srt

    Existence rule:
      - rename:  <base>(1).srt, <base>(2).srt, ...
      - overwrite: return the original path
      - skip: return None
    """
    video_path = Path(video_path)
    if suffix:
        base = f"{video_path.stem}.{suffix}"
    else:
        base = video_path.stem

    out = video_path.with_name(f"{base}.srt")
    if not out.exists():
        return out

    if on_exists == OnExists.overwrite:
        return out
    if on_exists == OnExists.skip:
        return None

    # rename
    n = 1
    while True:
        candidate = video_path.with_name(f"{base}({n}).srt")
        if not candidate.exists():
            return candidate
        n += 1


def write_text_atomic(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """
    Atomic-ish write: write to a temp file in the same directory then replace.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    try:
        tmp_path.write_text(content, encoding=encoding)
        os.replace(tmp_path, path)
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
