from __future__ import annotations

from typing import Any

from typer.testing import CliRunner

import audio_to_text.cli as cli_module
from audio_to_text.cli import app
from audio_to_text.stt.faster_whisper_engine import (
    TranscriptionResult,
    WhisperSegment,
)

runner = CliRunner()


def _fake_transcribe(segments: list[WhisperSegment]) -> Any:
    """Return a transcribe() replacement that records its kwargs."""

    def _transcribe(audio_path, **kwargs):  # noqa: ANN001
        _fake_transcribe.last_kwargs = kwargs  # type: ignore[attr-defined]
        return TranscriptionResult(device_used="cpu", segments=segments)

    return _transcribe


def test_stt_context_is_passed_as_initial_prompt(monkeypatch, tmp_path):
    # A .wav path skips the ffmpeg extraction branch.
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"")
    segs = [WhisperSegment(0.0, 1.0, "你好")]
    monkeypatch.setattr(cli_module, "transcribe", _fake_transcribe(segs))

    result = runner.invoke(
        app,
        ["stt", str(audio), "--output", "txt", "--context", "git, worktree"],
    )

    assert result.exit_code == 0, result.output
    assert "你好" in result.output
    assert (
        _fake_transcribe.last_kwargs.get("initial_prompt")  # type: ignore[attr-defined]
        == "git, worktree"
    )


def test_srt_prints_entries(tmp_path):
    srt = tmp_path / "a.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n你好\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\n世界\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["srt", str(srt)])
    assert result.exit_code == 0, result.output
    assert "你好" in result.output
    assert "世界" in result.output


def test_srt_apply_rebuilds_keeping_timestamps(tmp_path):
    srt = tmp_path / "a.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nOLD1\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\nOLD2\n",
        encoding="utf-8",
    )
    corrections = tmp_path / "corpus.txt"
    corrections.write_text("NEW1\nNEW2\n", encoding="utf-8")
    out = tmp_path / "out.srt"

    result = runner.invoke(
        app,
        ["srt", str(srt), "--apply", str(corrections), "--output-path", str(out)],
    )
    assert result.exit_code == 0, result.output
    written = out.read_text(encoding="utf-8")
    assert "NEW1" in written and "NEW2" in written
    assert "OLD1" not in written and "OLD2" not in written
    # Timestamps preserved verbatim.
    assert "00:00:00,000 --> 00:00:01,000" in written
    assert "00:00:01,000 --> 00:00:02,000" in written


def test_srt_apply_rejects_count_mismatch(tmp_path):
    srt = tmp_path / "a.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nA\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\nB\n",
        encoding="utf-8",
    )
    corrections = tmp_path / "corpus.txt"
    corrections.write_text("ONLY ONE\n", encoding="utf-8")  # 1 line, SRT has 2
    out = tmp_path / "out.srt"

    result = runner.invoke(
        app,
        ["srt", str(srt), "--apply", str(corrections), "--output-path", str(out)],
    )
    assert result.exit_code == 1
    assert not out.exists()  # nothing written on mismatch
