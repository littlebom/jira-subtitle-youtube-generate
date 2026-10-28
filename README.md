# YouTube to Open edX Subtitle Generator & Optimizer (Thai)

เครื่องมือและ **AI Agent Skill** สำหรับดึงบทบรรยายภาษาไทยจาก YouTube, แก้ไขคำผิดจากระบบรู้จำเสียง (Speech-to-Text), ซ่อมแซมรอยต่อคำที่ฉีกขาดด้วย **Bidirectional Context Validation (Look-behind & Look-ahead Checks)** และจัดรูปแบบเป็น `.srt` / `.vtt` แบบ **บรรทัดเดียว (Single-line)** ที่พร้อมใช้งานบน **Open edX Video Component** ทันที

---

## 🌟 ฟีเจอร์หลัก (Key Features)

1. **ดึงคำบรรยายเฉพาะเจาะจง (Fast Extraction via `yt-dlp`):**
   * ดึงเฉพาะแทร็กภาษาไทย (`th-orig` หรือ `th`) จาก YouTube โดยตรง ไม่ต้องดาวน์โหลดไฟล์วิดีโอขนาดใหญ่
2. **แก้ไขคำผิดจากระบบรู้จำเสียงอัตโนมัติ (Speech-to-Text Cleanup):**
   * แก้ไขคำผิดยอดนิยม เช่น `ดิจิตอล` $\rightarrow$ `ดิจิทัล`, `ป้ายบิบอร์ด` $\rightarrow$ `ป้ายบิลบอร์ด`, `พรีเซ็นตอร` $\rightarrow$ `พรีเซนเตอร์`, `แอปพลิเคชัก็` $\rightarrow$ `แอปพลิเคชันก็`
   * จัดรูปแบบตัวพิมพ์ใหญ่ของคำศัพท์เทคนิคภาษาอังกฤษ เช่น `Digital Advertising`, `Call to Action`, `Audience Segmentation`, `Awareness`, `Consideration`, `Decision`
3. **ระบบตรวจสอบและเชื่อมรอยต่อคำแบบ 2 ทิศทาง (Bidirectional Context Validation):**
   * **Look-behind Check (ตรวจย้อนหลัง):** ดึงพยางค์/คำที่หลุดมาจากคิวก่อนหน้ากลับมารวมกัน เช่น `ลูก/ค้า` $\rightarrow$ `ลูกค้า`, `ตัดสิน/ใจ` $\rightarrow$ `ตัดสินใจ`
   * **Look-ahead Check (ตรวจไปข้างหน้า):** ป้องกันการทิ้งคำลอย เช่น รวม `ถึงแบรนด์ของ` + `เรา` $\rightarrow$ `ถึงแบรนด์ของเรา` และไม่ฉีกกลุ่มคำเฉพาะภาษาอังกฤษข้ามคิว
   * รักษาคำพูดของวิทยากรเดิมครบถ้วน 100% (Verbatim)
4. **จัดรูปแบบเพื่อ Open edX โดยเฉพาะ:**
   * **Single-line format (Default):** แสดง 1 บรรทัดต่อช่วง เพื่อไม่ให้บดบังสไลด์หรือภาพประกอบการสอน
   * ควบคุม Timecode ให้ตรงกับเสียงพูดระดับมิลลิวินาที

---

## 📁 โครงสร้างโปรเจกต์ (Repository Structure)

```text
jira-subtitle-youtube-generate/
├── .agents/
│   └── skills/
│       └── youtube-openedx-subtitles/
│           ├── SKILL.md            # ไฟล์คำสั่ง Skill สำหรับ Google Antigravity
│           └── scripts/
│               └── process_transcript.py
├── scripts/
│   └── process_transcript.py      # สคริปต์ Python สำหรับประมวลผลคำบรรยาย
├── examples/
│   ├── digital_advertising.srt    # ตัวอย่างไฟล์ .srt มาตรฐาน Open edX
│   └── digital_advertising.vtt    # ตัวอย่างไฟล์ .vtt
├── SKILL.md
├── requirements.txt
└── README.md
```

---

## 🚀 วิธีนำไปใช้งานบนเครื่องอื่น (Installation & Usage)

### วิธีที่ 1: ติดตั้งเป็น Google Antigravity Skill

#### แบบที่ 1.1: ใช้งานเฉพาะโปรเจกต์ (Workspace Skill)
Clone หรือคัดลอกโฟลเดอร์ `.agents/` ไปไว้ที่ Root ของโฟลเดอร์โปรเจกต์ของคุณ:
```bash
git clone https://github.com/littlebom/jira-subtitle-youtube-generate.git temp_skill
cp -r temp_skill/.agents <your-project-root>/
rm -rf temp_skill
```
Antigravity จะตรวจพบ Skill `youtube-openedx-subtitles` ทันที

#### แบบที่ 1.2: ใช้งานทั่วทั้งเครื่อง (Global Skill)
คัดลอกโฟลเดอร์ Skill ไปไว้ที่ Global Directory:
* **macOS / Linux:**
  ```bash
  mkdir -p ~/.gemini/antigravity/skills/
  cp -r .agents/skills/youtube-openedx-subtitles ~/.gemini/antigravity/skills/
  ```
* **Windows:**
  ```cmd
  xcopy /E /I .agents\skills\youtube-openedx-subtitles %USERPROFILE%\.gemini\antigravity\skills\youtube-openedx-subtitles
  ```

---

### วิธีที่ 2: รันผ่านคำสั่ง CLI ทั่วไป

1. ติดตั้ง Dependencies:
   ```bash
   pip install -r requirements.txt
   # หรือบน macOS ผ่าน Homebrew:
   brew install yt-dlp ffmpeg
   ```
2. ดึงบทบรรยายจาก YouTube:
   ```bash
   yt-dlp --write-auto-subs --sub-lang "th-orig,th" --skip-download --sub-format "vtt" -o "lecture.%(ext)s" "<YOUTUBE_URL>"
   ```
3. รันสคริปต์เพื่อคลีนและจัดรอยต่อคำ:
   ```bash
   python3 scripts/process_transcript.py
   ```

---

## 🎓 วิธีนำไฟล์ไปใส่ใน Open edX Studio

1. เข้าไปยังคอร์สใน **Open edX Studio** $\rightarrow$ ไปที่ **Unit** ที่มีวิดีโอนั้น
2. คลิก **Edit** ที่บล็อก **Video Component**
3. ไปที่แท็บ **Advanced** $\rightarrow$ หัวข้อ **Timed Transcript**
4. เลือกภาษาเป็น **Thai (th)** แล้วคลิก **Upload** ไฟล์ `.srt` (เช่น [examples/digital_advertising.srt](examples/digital_advertising.srt))
5. คลิก **Save** และ **Publish** ระบบจะแสดงคำบรรยายและไฮไลต์ข้อความตามเวลาจริงทันที

---

## 📄 License
MIT License
