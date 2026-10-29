#!/usr/bin/env python3
"""
Subtitle verification script

Compares a raw auto‑generated VTT file with a cleaned SRT subtitle file and
produces a diff file in SRT format.

Features required by the user:
* Default diff output file is ``diff_subtitles.srt`` (configurable via ``--output``).
* Option ``--ignore-space`` collapses consecutive whitespace before comparison.
* Option ``--no-exit-code`` forces the script to exit with code 0 even when
  differences are found (useful for pipelines that must continue).
"""

import argparse
import re
import sys
from pathlib import Path


def read_vtt(path: Path):
    """Parse a VTT file into a list of cue dicts.
    Each dict contains: ``index``, ``start``, ``end``, ``text``.
    """
    cues = []
    with path.open(encoding="utf-8") as f:
        lines = [l.rstrip() for l in f]
    i = 0
    while i < len(lines):
        # Skip possible header lines (e.g., WEBVTT)
        if lines[i].startswith("WEBVTT") or lines[i] == "":
            i += 1
            continue
        # Optional cue number – ignore if not numeric
        if re.fullmatch(r"\d+", lines[i]):
            index = int(lines[i])
            i += 1
        else:
            index = len(cues) + 1
        # Timing line
        timing = lines[i]
        i += 1
        m = re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})", timing)
        if not m:
            # malformed timing – skip this cue
            continue
        start, end = m.groups()
        # Text lines until blank line or end of file
        text_lines = []
        while i < len(lines) and lines[i] != "":
            text_lines.append(lines[i])
            i += 1
        text = " ".join(text_lines)
        cues.append({"index": index, "start": start, "end": end, "text": text})
        # Skip the blank line separator
        while i < len(lines) and lines[i] == "":
            i += 1
    return cues


def read_srt(path: Path):
    """Parse an SRT file – same structure as VTT but timestamps use commas.
    """
    cues = []
    with path.open(encoding="utf-8") as f:
        lines = [l.rstrip() for l in f]
    i = 0
    while i < len(lines):
        if lines[i] == "":
            i += 1
            continue
        # Cue number
        index = int(lines[i])
        i += 1
        # Timing line
        timing = lines[i]
        i += 1
        m = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", timing)
        if not m:
            continue
        start, end = m.groups()
        # Text lines until blank line
        text_lines = []
        while i < len(lines) and lines[i] != "":
            text_lines.append(lines[i])
            i += 1
        text = " ".join(text_lines)
        cues.append({"index": index, "start": start, "end": end, "text": text})
        while i < len(lines) and lines[i] == "":
            i += 1
    return cues


def normalize(text: str, ignore_space: bool) -> str:
    if ignore_space:
        # Collapse any whitespace sequence into a single space
        text = re.sub(r"[ \t\r\n]+", " ", text)
    return text.strip()


def write_diff(diff_cues, out_path: Path):
    """Write diff cues to an SRT file.
    Each cue shows the raw line (<<< RAW:) and the cleaned line (>>> CLEAN:).
    """
    lines = []
    for cue in diff_cues:
        lines.append(str(cue["index"]))
        # Preserve original timestamps from the raw file (they are already in SRT‑style)
        lines.append(f"{cue['start']} --> {cue['end']}")
        lines.append(f"<<< RAW: {cue['raw']}")
        lines.append(f">>> CLEAN: {cue['clean']}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Verify subtitle correctness by diffing raw VTT against cleaned SRT.")
    parser.add_argument("raw_vtt", type=Path, help="Path to the original auto‑generated VTT file.")
    parser.add_argument("clean_srt", type=Path, help="Path to the cleaned SRT file produced by the skill.")
    parser.add_argument("--output", type=Path, default=Path("diff_subtitles.srt"), help="Output diff file in SRT format (default: diff_subtitles.srt).")
    parser.add_argument("--ignore-space", action="store_true", help="Collapse consecutive whitespace before comparison.")
    parser.add_argument("--no-exit-code", action="store_true", help="Always exit with code 0, even if differences are found.")
    args = parser.parse_args()

    raw_cues = read_vtt(args.raw_vtt)
    clean_cues = read_srt(args.clean_srt)

    # Align by index – assume both lists are ordered.
    diff_cues = []
    for raw, clean in zip(raw_cues, clean_cues):
        raw_text = normalize(raw["text"], args.ignore_space)
        clean_text = normalize(clean["text"], args.ignore_space)
        if raw_text != clean_text:
            diff_cues.append({
                "index": raw["index"],
                "start": raw["start"].replace('.', ','),  # ensure SRT comma format
                "end": raw["end"].replace('.', ','),
                "raw": raw["text"],
                "clean": clean["text"],
            })

    if diff_cues:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_diff(diff_cues, args.output)
        print(f"Found {len(diff_cues)} mismatched cues. Diff written to {args.output}")
        if not args.no_exit_code:
            sys.exit(1)
    else:
        print("No differences found between raw VTT and cleaned SRT.")
        # Ensure an empty diff file is not left behind (optional)
        if args.output.exists():
            args.output.unlink()
        sys.exit(0)


if __name__ == "__main__":
    main()
