---
name: youtube-openedx-subtitles
description: >-
  Extract, clean, segment, and format Thai YouTube video transcripts/subtitles into
  high-quality .srt and .vtt timed files optimized for Open edX video components.
  Use when the user wants to transcribe YouTube educational videos, fix word-splitting
  issues in Thai subtitles, balance line breaks, or prepare transcripts for Open edX.
---

# YouTube to Open edX Subtitle Processor (Thai)

A specialized workflow to extract YouTube video transcripts, correct speech recognition errors, heal broken word boundaries via bidirectional context validation, and produce clean `.srt` and `.vtt` subtitles ready for Open edX.

---

## Workflow Steps

### Step 1: Extract Captions from YouTube
Check available subtitles and download the original Thai auto-generated or manual captions without downloading the heavy video file:

```bash
# 1. Check available captions
yt-dlp --list-subs "<YOUTUBE_URL>"

# 2. Download Thai subtitles in VTT format
yt-dlp --write-auto-subs --sub-lang "th-orig,th" --skip-download --sub-format "vtt" -o "raw_sub.%(ext)s" "<YOUTUBE_URL>"
```

### Step 2: Clean Speech-to-Text Glitches & Misspellings
Correct typical Thai speech recognition mistakes while strictly preserving verbatim speech:
- `ดิจิตอล` $\rightarrow$ `ดิจิทัล`
- `ป้ายบิบอร์ด` / `บิบอร์ด` $\rightarrow$ `ป้ายบิลบอร์ด`
- `พรีเซ็นตอร` $\rightarrow$ `พรีเซนเตอร์`
- `แอปพลิเคชัก็` $\rightarrow$ `แอปพลิเคชันก็`
- `ดาวน์โหลดนา` $\rightarrow$ `ดาวน์โหลด Now`
- `ขั้นเวลา` $\rightarrow$ `คั่นเวลา`
- English terms capitalization: `Digital Advertising`, `Call to Action`, `CTA`, `Audience Segmentation`, `Awareness`, `Consideration`, `Decision`

### Step 3: Bidirectional Sentence & Boundary Validation (Cross-Cue Completeness)
To ensure sentences and phrases are complete and natural across subtitle cues, perform two-way validation:

1. **Look-behind Check (ตรวจลำดับก่อนหน้า):**
   - Check if the current cue begins with a fragment severed from the previous cue (e.g. `ค้า` from `ลูก/ค้า`, `ใจ` from `ตัดสิน/ใจ`).
   - Pull the severed syllable into the correct cue to preserve compound word integrity.
2. **Look-ahead Check (ตรวจลำดับถัดไป):**
   - Check if the current cue ends with an incomplete phrase or dangling preposition (e.g. `ถึงแบรนด์ของ` $\rightarrow$ pull `เรา` from the next cue to make `ถึงแบรนด์ของเรา`).
   - Prevent splitting technical terms across cues (e.g. ensure `Call to Action` or `Audience Segmentation` stays unified).
3. **Compound Word & Phrase Integrity:**
   - Thai compound words (`ลูกค้า`, `ตัดสินใจ`, `ข้อมูล`, `เป้าหมาย`) must never be broken across cues.
   - Each cue should represent a coherent semantic clause (Semantic Chunk).

### Step 4: Line Formatting (Single-line vs Multi-line)
1. **Single-line format (Default/Recommended):**
   - 1 continuous line per cue without manual `\n` line breaks.
   - Prevents vertical obstruction on lecture slides and video components.
2. **Multi-line format:**
   - 2 balanced lines per cue (≤ 35 chars per line) when strict width constraint is needed.
3. Maintain original cue pacing and timestamps.

### Step 5: Generate Output Files
Write standards-compliant output files into the workspace `transcripts/` directory:
- `.srt` file: Uses comma for milliseconds (`00:00:14,879 --> 00:00:22,269`)
- `.vtt` file: Starts with `WEBVTT` and uses period for milliseconds (`00:00:14.879 --> 00:00:22.269`)

---

## Open edX Integration Guide

To upload to Open edX Studio:
1. Navigate to the course unit containing the **Video Component**.
2. Click **Edit** on the video component.
3. Go to the **Advanced** tab $\rightarrow$ **Timed Transcript**.
4. Select language **Thai (th)** and upload the `.srt` file.
5. Click **Save** and **Publish**.
