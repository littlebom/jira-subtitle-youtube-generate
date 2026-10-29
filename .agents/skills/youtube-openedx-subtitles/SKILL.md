---
name: youtube-openedx-subtitles
description: >-
  Extract, clean, segment, and format Thai YouTube video transcripts/subtitles into
  high-quality .srt and .vtt timed files optimized for Open edX video components.
  Includes Thai word-splitting healing, speech-to-text error correction, Thai-English/numeric
  word spacing standardization, and balanced single-line cue formatting.
---

# YouTube to Open edX Subtitle Processor (Thai)

A specialized workflow to extract YouTube video transcripts, correct speech recognition errors, heal broken word boundaries via bidirectional context validation, standardize Thai-English/numeric word spacing, and produce clean `.srt` and `.vtt` subtitles ready for Open edX.

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

1. **Move Leading "นะคะ" to Previous Section/Cue (ย้าย "นะคะ" ต้นประโยคไปท้าย section ก่อนหน้า):**
   - If a cue/section begins with `นะคะ` (or `นะ / คะ` split across cues), move `นะคะ` to the end of the previous cue/section.
   - Preserves natural conversational flow so polite sentence-ending particles do not unnaturally start a new sentence (e.g. Cue A: `... 3 อย่างด้วยกัน`, Cue B: `นะคะ ก็คือตัวแรก...` $\rightarrow$ Cue A: `... 3 อย่างด้วยกัน นะคะ`, Cue B: `ก็คือตัวแรก...`).
2. **Look-behind Check (ตรวจลำดับก่อนหน้า):**
   - Check if the current cue begins with a fragment severed from the previous cue (e.g. `ค้า` from `ลูก/ค้า`, `ใจ` from `ตัดสิน/ใจ`).
   - Pull the severed syllable into the correct cue to preserve compound word integrity.
3. **Look-ahead Check (ตรวจลำดับถัดไป):**
   - Check if the current cue ends with an incomplete phrase or dangling preposition (e.g. `ถึงแบรนด์ของ` $\rightarrow$ pull `เรา` from the next cue to make `ถึงแบรนด์ของเรา`).
   - Prevent splitting technical terms across cues (e.g. ensure `Call to Action` or `Audience Segmentation` stays unified).
4. **Compound Word & Phrase Integrity:**
   - Thai compound words (`ลูกค้า`, `ตัดสินใจ`, `ข้อมูล`, `เป้าหมาย`, `รูปแบบ`) must never be broken across cues.
   - Each cue should represent a coherent semantic clause (Semantic Chunk).

### Step 4: Spacing Standardization (การตรวจสอบการเว้นวรรคคำและอนุประโยค)
Standardize spacing across the transcript according to Thai Royal Society rules and readability guidelines:

1. **Thai and English / Technical Terms (ไทย - อังกฤษ):**
   - Add exactly 1 space between Thai characters and English terms (e.g. `สร้าง Awareness การรับรู้`, `แบรนด์ Vimeo`, `We Are Social และ Hootsuite`).
2. **Thai and Numbers / Symbols (ไทย - ตัวเลข):**
   - Add exactly 1 space between Thai text and numbers/percentages (e.g. `ข้อที่ 1 นะคะ`, `ปี 2021`, `316 ล้านคน`, `100% ก็ได้`).
3. **Maiyamok Spacing (การเว้นวรรคไม้ยมก `ๆ` ทั้งหน้าและหลัง):**
   - Always place exactly 1 space both **before** and **after** `ๆ` according to Royal Society of Thailand rules (e.g. `เรื่อย ๆ ทุกปี`, `คล้าย ๆ กับ`, `แบบต่าง ๆ ได้`, `ต่าง ๆ นานา`, `ต่าง ๆ นะคะ`).
4. **Intra-word & Whitespace Cleaning:**
   - Eliminate unintended spaces inside Thai compound words (e.g. `ข้อ มูล` $\rightarrow$ `ข้อมูล`).
   - Collapse duplicate spaces into a single space (`[ \t]+` $\rightarrow$ ` `).
5. **Clause & Breathing Pause Spacing (วรรคตอนคั่นประโยคย่อย):**
   - Insert natural spacing when transitioning between sub-clauses to aid fast visual scanning on screen (e.g. `นะคะ ข้อแรกเลย`, `นะคะ ส่วนบางแบรนด์`, `ได้นะคะ ปัจจุบันที่`).

### Step 5: Line Formatting (Single-line vs Multi-line)
1. **Single-line format (Default/Recommended):**
   - 1 continuous line per cue without manual `\n` line breaks.
   - Prevents vertical obstruction on lecture slides and video components.
2. **Multi-line format:**
   - 2 balanced lines per cue (≤ 35 chars per line) when strict width constraint is needed.
3. Maintain original cue pacing and timestamps without overlapping cues.

### Step 6: Generate Output Files
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

## Verification

สคริปต์ตรวจสอบ **`verify_subtitles.py`** ถูกเพิ่มในโฟลเดอร์ `scripts/` ของ Skill นี้ โดยเปรียบเทียบไฟล์ VTT ดิบกับไฟล์ SRT ที่ทำความสะอาดแล้วและสร้างไฟล์ diff ในรูปแบบ SRT

### ฟีเจอร์ที่ผู้ใช้ร้องขอ
- `--output <path>` – ระบุตำแหน่งไฟล์ SRT diff ที่ต้องการบันทึก (ค่าเริ่มต้น `diff_subtitles.srt`).
- `--ignore-space` – ไม่สนใจช่องว่างต่อเนื่อง (หลายช่องว่างจะถูกบีบเป็นหนึ่งช่องว่างก่อนเปรียบเทียบ).
- `--no-exit-code` – ปิดการส่ง exit code ที่ไม่เป็นศูนย์เมื่อพบ diff; สคริปต์จะออกด้วยค่า 0 เสมอ (เหมาะกับ pipeline ที่ต้องดำเนินต่อ).

### วิธีใช้ตัวอย่าง
```bash
python3 .agents/skills/youtube-openedx-subtitles/scripts/verify_subtitles.py \
    transcripts/raw_sub.th-orig.vtt \
    transcripts/02_Digital_Advertising_Concepts.srt \
    --output transcripts/diff_subtitles.srt \
    --ignore-space \
    --no-exit-code
```

หากพบความแตกต่าง จะสร้างไฟล์ `diff_subtitles.srt` ที่มีรูปแบบ:
```
1
00:00:12,340 --> 00:00:15,120
<<< RAW: ทำไมแบรนด์ต้องพึ่งพาการโฆษณาออนไลน์ด้วย
>>> CLEAN: ทำไมแบรนด์ต้องพึ่งพาการโฆษณาออนไลน์ด้วย
```
(หากไม่มีความแตกต่าง ไฟล์ diff จะไม่ถูกสร้างและจะแสดงข้อความ *No differences found* บน console.)

### การรวมเข้ากับ Workflow
หลังจากรัน `process_transcript.py` เพื่อสร้างไฟล์ SRT แล้ว ให้เรียก `verify_subtitles.py` เพื่อตรวจสอบว่าการทำความสะอาดไม่มีข้อผิดพลาดสำคัญ ก่อนอัปโหลดไปยัง Open edX.
