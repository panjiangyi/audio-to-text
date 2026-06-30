from __future__ import annotations

import pytest

from audio_to_text.subtitles.srt import (
    SrtSegment,
    _parse_timestamp,
    format_timestamp,
    parse_srt,
    segments_to_srt,
)


def test_format_timestamp_boundaries():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(2.5) == "00:00:02,500"
    assert format_timestamp(3661.5) == "01:01:01,500"
    assert format_timestamp(None) == "00:00:00,000"


def test_parse_timestamp_accepts_comma_and_dot():
    assert _parse_timestamp("00:00:02,500") == pytest.approx(2.5)
    assert _parse_timestamp("00:00:02.500") == pytest.approx(2.5)
    assert _parse_timestamp("01:01:01,500") == pytest.approx(3661.5)


def test_parse_timestamp_invalid():
    with pytest.raises(ValueError):
        _parse_timestamp("not a timestamp")


def test_format_parse_roundtrip_is_lossless():
    # Float drift must not corrupt millisecond timestamps on a round-trip
    # (e.g. 2.799s must not become ",798"). This is the core invariant the
    # proofread rebuild relies on.
    for ts in ["00:00:00,000", "00:00:02,799", "00:01:30,500", "01:02:03,999"]:
        assert format_timestamp(_parse_timestamp(ts)) == ts


def test_segments_to_srt_skips_empty_and_renumbers():
    segs = [
        SrtSegment(0.0, 1.0, "你好"),
        SrtSegment(1.0, 2.0, ""),  # empty text is skipped
        SrtSegment(2.0, 3.0, "世界"),
    ]
    out = segments_to_srt(segs)
    assert out.endswith("\n")
    assert out == (
        "1\n00:00:00,000 --> 00:00:01,000\n你好\n\n"
        "2\n00:00:02,000 --> 00:00:03,000\n世界\n"
    )


def test_parse_srt_roundtrip_preserves_timestamps_and_text():
    original = [
        SrtSegment(0.0, 1.0, "大家好"),
        SrtSegment(1.0, 2.5, "Git的worktree很好用"),
        SrtSegment(2.5, 3.5, "它概念很好"),
    ]
    parsed = parse_srt(segments_to_srt(original))
    assert len(parsed) == len(original)
    for a, b in zip(original, parsed):
        assert (a.start, a.end, a.text) == (b.start, b.end, b.text)


def test_parse_srt_tolerant_bom_crlf():
    raw = (
        "﻿1\r\n00:00:00,000 --> 00:00:01,000\r\n你好\r\n\r\n"
        "2\r\n00:00:01,000 --> 00:00:02,000\r\n世界\r\n"
    )
    parsed = parse_srt(raw)
    assert [s.text for s in parsed] == ["你好", "世界"]
    assert parsed[0].start == 0.0
    assert parsed[1].end == 2.0


def test_parse_srt_tolerant_dot_separator_and_bad_index():
    # non-sequential index numbers; '.' as the millisecond separator
    raw = (
        "99\n00:00:00,000 --> 00:00:01.500\n第一句\n\n"
        "2\n00:00:01,500 --> 00:00:02,500\n第二句\n"
    )
    parsed = parse_srt(raw)
    assert [s.text for s in parsed] == ["第一句", "第二句"]
    assert parsed[0].end == 1.5


def test_parse_srt_missing_timestamp_raises():
    raw = "1\n你好\n\n2\n00:00:01,000 --> 00:00:02,000\n世界\n"
    with pytest.raises(ValueError):
        parse_srt(raw)


def test_parse_srt_empty_raises():
    with pytest.raises(ValueError):
        parse_srt("   \n  \n")
