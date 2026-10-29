#!/usr/bin/env python3
"""
Process Thai YouTube subtitles for Open edX.
Includes STT error corrections, bidirectional context validation,
compound word healing, Thai/English/numeric/clause spacing standardization,
and Open edX .srt / .vtt formatting.
"""

import os
import re

def to_sec(ts):
    parts = ts.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s

def sec_to_vtt(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def sec_to_srt(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    s_int = int(s)
    ms = int(round((s - s_int) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s_int:02d},{ms:03d}"

def load_vtt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = text.strip().split('\n\n')
    cues = []
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        timing_idx = -1
        for i, l in enumerate(lines):
            if '-->' in l:
                timing_idx = i
                break
        if timing_idx == -1:
            continue
        parts = lines[timing_idx].split()
        start_t, end_t = parts[0], parts[2]
        if to_sec(end_t) - to_sec(start_t) < 0.1:
            continue
        content_lines = lines[timing_idx+1:]
        target_line = content_lines[-1]
        cleaned = re.sub(r'<[^>]+>', '', target_line).strip()
        if cleaned:
            cues.append({'start': start_t, 'end': end_t, 'text': cleaned})
    return cues

def standardize_spacing(text: str) -> str:
    """
    Standardize Thai-English, numeric, punctuation, and clause spacing:
    1. Spacing between Thai and English words
    2. Spacing between Thai and digits/numbers
    3. Spacing around symbols and Maiyamok (ๆ)
    4. Clause break spacing after polite particles (นะคะ, ค่ะ, ครับ)
    5. Clean redundant intra-word spaces and multiple whitespace characters
    """
    # Spacing between Thai and English
    text = re.sub(r'([ก-๙])([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z])([ก-๙])', r'\1 \2', text)
    
    # Spacing between Thai and digits
    text = re.sub(r'([ก-๙])([0-9])', r'\1 \2', text)
    text = re.sub(r'([0-9])([ก-๙])', r'\1 \2', text)
    
    # Spacing around Maiyamok (ๆ) - space before and space after
    text = re.sub(r'\s*ๆ\s*', ' ๆ ', text)
    
    # Spacing after %
    text = re.sub(r'%([ก-๙])', r'% \1', text)
    
    # Clause spacing after polite endings
    text = re.sub(r'(นะคะ|ค่ะ|ครับ)([ก-๙])', r'\1 \2', text)
    
    # Remove unwanted space before Thai punctuation
    text = re.sub(r'\s+([?.!,])', r'\1', text)
    
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return text

def process():
    raw_vtt_path = 'transcripts/raw_sub.th-orig.vtt'
    cues = load_vtt(raw_vtt_path)
    
    # Merge intro music cues
    merged_cues = []
    merged_cues.append({
        'start': cues[0]['start'],
        'end': cues[1]['end'],
        'text': '[ดนตรี]'
    })
    for c in cues[2:]:
        merged_cues.append(dict(c))
    
    # 1. Base vocabulary and typo corrections
    vocab_replacements = [
        (r'ดิจิตอล', 'ดิจิทัล'),
        (r'แนวนนโนม', 'แนวโน้ม'),
        (r'\bเาเพิ่ม\b', 'เพิ่ม'),
        (r'\bเา้า\b', 'เขา'),
        (r'โซเชียลมีดีย', 'โซเชียลมีเดีย'),
        (r'VR\s+Social', 'We Are Social'),
        (r'Host\s+Sweet', 'Hootsuite'),
        (r'Vimio', 'Vimeo'),
        (r'\bpersuate\b', 'Persuade'),
        (r'\bPersuate\b', 'Persuade'),
        (r'รีind', 'Remind'),
        (r'แอปพลิเคชั\b', 'แอปพลิเคชัน'),
        (r'แจกเวชอร์', 'แจก Voucher'),
        (r'มีเวอร์แจก', 'มี Voucher แจก'),
        (r'\bby\s+now\b', 'Buy Now'),
        (r'สร้างความcreเอที', 'สร้างความ Creative'),
        (r'Audi\s+ของ\s+Facebook\s+Ad', 'Audience ของ Facebook Ads'),
        (r'เลือกแอ\s+format', 'เลือก Ad Format'),
        (r'decision\s+state', 'Decision Stage'),
        (r'buyer\s+Journey', "Buyer's Journey"),
        (r'Buyer\s+Journey', "Buyer's Journey"),
        (r'Call\s+to\s+action', 'Call to Action'),
        (r'Contact\s+us', 'Contact Us'),
        (r'Get\s+free\s+consultant', 'Get Free Consultant'),
        (r'Body\s+Shop', 'The Body Shop'),
        (r'วีดีโอ', 'วิดีโอ'),
        (r'คลิปถัดถัดไป', 'คลิปถัดไป'),
        (r'โฆษณาี่เหมาะสม', 'โฆษณาที่เหมาะสม'),
        (r'Story ของเพื่อน', 'Stories ของเพื่อน')
    ]
    
    for c in merged_cues:
        for pat, repl in vocab_replacements:
            c['text'] = re.sub(pat, repl, c['text'], flags=re.IGNORECASE)

    # 2. Sequential Cross-Cue Boundary Validations
    for i in range(len(merged_cues) - 1):
        c1 = merged_cues[i]
        c2 = merged_cues[i+1]
        
        # 2.1 Heal split นะ / คะ across cues
        if c1['text'].strip().endswith('นะ') and re.match(r'^คะ', c2['text'].strip()):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', c1['text'].strip())
            c2['text'] = re.sub(r'^คะ\s*', '', c2['text'].strip())

        # 2.2 Move leading นะคะ to previous cue/section
        if re.match(r'^(?:นะคะ|นะ\s+คะ)', c2['text'].strip()):
            c2['text'] = re.sub(r'^(?:นะคะ|นะ\s+คะ)\s*', '', c2['text'].strip())
            c1_txt = c1['text'].strip()
            if not c1_txt.endswith('นะคะ'):
                c1['text'] = c1_txt + ' นะคะ'

        t1, t2 = c1['text'], c2['text']
        
        # เนี่ยเพิ่ม -> เพิ่มมากขึ้นทุกปี
        if t1.endswith('เนี่ยเพิ่ม') and t2.startswith('มากขึ้นทุกปี'):
            c1['text'] = re.sub(r'เพิ่ม$', '', t1).strip()
            c2['text'] = 'เพิ่ม' + t2
            
        # ซึ่งรวบ -> รวบรวมโดย
        elif t1.endswith('ซึ่งรวบ') and t2.startswith('รวมโดย'):
            c1['text'] = re.sub(r'รวบ$', '', t1).strip()
            c2['text'] = 'รวบ' + t2

        # Hootsuite นะ / คะจะเห็นว่า -> Hootsuite นะคะ / จะเห็นว่า
        elif t1.endswith('นะ') and t2.startswith('คะจะเห็นว่า'):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', t1).strip()
            c2['text'] = re.sub(r'^คะ', '', t2).strip()

        # โทรศัพท์มือถือจำนวนผู้ใช้งานโซเชียล / Media ซึ่งจะเห็นว่า -> ...โซเชียลมีเดีย / ซึ่งจะเห็นว่า
        elif t1.endswith('โซเชียล') and 'Media' in t2:
            c1['text'] = t1 + 'มีเดีย'
            c2['text'] = re.sub(r'^Media\s*', '', t2).strip()

        # เป้าหมายของตัว / เองได้นะคะ -> เป้าหมาย / ของตัวเองได้นะคะ
        elif t1.endswith('ของตัว') and t2.startswith('เองได้นะคะ'):
            c1['text'] = re.sub(r'ของตัว$', '', t1).strip()
            c2['text'] = 'ของตัวเองได้นะคะ' + re.sub(r'^เองได้นะคะ', '', t2).strip()

        # นะคะส่วน / บางแบรนด์ -> นะคะ / ส่วนบางแบรนด์
        elif t1.endswith('นะคะส่วน') and t2.startswith('บางแบรนด์'):
            c1['text'] = re.sub(r'ส่วน$', '', t1).strip()
            c2['text'] = 'ส่วน ' + t2

        # สินค้าและ / บริการให้ได้เลย -> สินค้า / และบริการให้ได้เลย
        elif t1.endswith('สินค้าและ') and t2.startswith('บริการให้ได้เลย'):
            c1['text'] = re.sub(r'และ$', '', t1).strip()
            c2['text'] = 'และ' + t2

        # Persuade นะ / คะเป็นการชักชวน -> Persuade นะคะ / เป็นการชักชวน
        elif 'Persuade' in t1 and t1.endswith('นะ') and t2.startswith('คะ'):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', t1).strip()
            c2['text'] = re.sub(r'^คะ', '', t2).strip()

        # ก่อนเลยนะ / คะ Inform -> ก่อนเลยนะคะ / Inform
        elif t1.endswith('ก่อนเลยนะ') and re.search(r'^คะ\s*Inform', t2):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', t1).strip()
            c2['text'] = re.sub(r'^คะ\s*', '', t2).strip()

        # ความรู้จากหัว / ข้อที่ -> ความรู้ / จากหัวข้อที่
        elif t1.endswith('จากหัว') and t2.startswith('ข้อที่'):
            c1['text'] = re.sub(r'จากหัว$', '', t1).strip()
            c2['text'] = 'จากหัว' + t2

        # Harvard Business / School นะคะ -> Harvard Business School นะคะ
        elif t1.endswith('Harvard Business') and t2.startswith('School นะคะ'):
            c1['text'] = t1 + ' School นะคะ'
            c2['text'] = re.sub(r'^School\s+นะคะ', '', t2).strip()

        # ตัดสินใจนะ / คะจะซื้อ -> ตัดสินใจนะคะ / จะซื้อ
        elif t1.endswith('ตัดสินใจนะ') and t2.startswith('คะ'):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', t1).strip()
            c2['text'] = re.sub(r'^คะ', '', t2).strip()

        # เพื่อเน้น / ย้ำถึง -> ... / เพื่อเน้นย้ำถึง
        elif t1.endswith('เพื่อเน้น') and t2.startswith('ย้ำถึง'):
            c1['text'] = re.sub(r'เพื่อเน้น$', '', t1).strip()
            c2['text'] = 'เพื่อเน้น' + t2

        # การตั้ง Call / to Action -> การตั้ง / Call to Action
        elif t1.endswith('การตั้ง Call') and 'action' in t2.lower():
            c1['text'] = re.sub(r'Call$', '', t1).strip()
            c2['text'] = 'Call ' + t2

        # ก็จะตัดสิน / ใจซื้อ -> ก็จะ / ตัดสินใจซื้อ
        elif t1.endswith('ก็จะตัดสิน') and t2.startswith('ใจซื้อ'):
            c1['text'] = re.sub(r'ตัดสิน$', '', t1).strip()
            c2['text'] = 'ตัดสิน' + t2

        # บรรลุตาม buyer / Journey -> บรรลุตาม / Buyer's Journey
        elif re.search(r'buyer$', t1, re.IGNORECASE) and re.search(r'^journey', t2, re.IGNORECASE):
            c1['text'] = re.sub(r'buyer$', '', t1, flags=re.IGNORECASE).strip()
            c2['text'] = "Buyer's " + t2

        # ตามที่แบรนด์ตั้งเป้า / หมายเอาไว้นะคะ -> ตามที่แบรนด์ / ตั้งเป้าหมายเอาไว้นะคะ
        elif t1.endswith('ตั้งเป้า') and t2.startswith('หมายเอาไว้นะคะ'):
            c1['text'] = re.sub(r'ตั้งเป้า$', '', t1).strip()
            c2['text'] = 'ตั้งเป้า' + t2

        # ไปยังกลุ่มลูก / ค้าของเรา -> ไปยัง / กลุ่มลูกค้าของเรา
        elif t1.endswith('กลุ่มลูก') and t2.startswith('ค้าของเรา'):
            c1['text'] = re.sub(r'กลุ่มลูก$', '', t1).strip()
            c2['text'] = 'กลุ่มลูก' + t2

        # เลือกรูป / แบบของโฆษณา -> ... / เลือกรูปแบบของโฆษณา
        elif t1.endswith('เลือกรูป') and t2.startswith('แบบของโฆษณา'):
            c1['text'] = re.sub(r'เลือกรูป$', '', t1).strip()
            c2['text'] = 'เลือกรูป' + t2

        # วิดีโอสั้นนะ / คะคลิปยาว -> วิดีโอสั้นนะคะ / คลิปยาว
        elif t1.endswith('วิดีโอสั้นนะ') and t2.startswith('คะคลิปยาว'):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', t1).strip()
            c2['text'] = re.sub(r'^คะ', '', t2).strip()

    # Final sentence, term, and SPACING polish
    for c in merged_cues:
        txt = c['text']
        
        # Fix specific phrase anomalies
        txt = txt.replace('ขั้นที่ 2 รีนะคะ', 'ขั้นที่ 2 Remind นะคะ')
        txt = txt.replace('Hootsuiteนะคะ', 'Hootsuite นะคะ')
        txt = txt.replace('Persuade นนะคะ', 'Persuade นะคะ')
        txt = txt.replace('โฆษณาี่เหมาะสม', 'โฆษณาที่เหมาะสม')
        txt = txt.replace('Creativeลงไป', 'Creative ลงไป')
        txt = txt.replace('interaction', 'Interaction')
        txt = re.sub(r'แบรนด์ต$', 'แบรนด์', txt)
        
        # Capitalizations
        txt = re.sub(r'\bawareness\b', 'Awareness', txt)
        txt = re.sub(r'\bconsideration\b', 'Consideration', txt)
        txt = re.sub(r'\binform\b', 'Inform', txt)
        txt = re.sub(r'\bremind\b', 'Remind', txt)
        txt = re.sub(r'\bpersuade\b', 'Persuade', txt)
        txt = re.sub(r'\breport\b', 'Report', txt)
        txt = re.sub(r'\bline\b', 'LINE', txt)
        txt = re.sub(r'\bcall to action\b', 'Call to Action', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\bcontact us\b', 'Contact Us', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\bbuy now\b', 'Buy Now', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\bget free consultant\b', 'Get Free Consultant', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\bretargeting\b', 'Retargeting', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\bthe body shop\b', 'The Body Shop', txt, flags=re.IGNORECASE)
        
        # Apply standard spacing (Thai-English, numbers, Maiyamok, clause breaks)
        txt = standardize_spacing(txt)
        c['text'] = txt

    if merged_cues[-1]['text'].strip() == 'ขอบคุณ':
        merged_cues[-1]['text'] = 'ขอบคุณค่ะ'

    # Build Output
    srt_lines = []
    vtt_lines = ["WEBVTT\n"]
    
    for idx, c in enumerate(merged_cues, 1):
        s_srt = sec_to_srt(to_sec(c['start']))
        e_srt = sec_to_srt(to_sec(c['end']))
        s_vtt = sec_to_vtt(to_sec(c['start']))
        e_vtt = sec_to_vtt(to_sec(c['end']))
        
        txt = c['text']
        srt_lines.append(f"{idx}\n{s_srt} --> {e_srt}\n{txt}\n")
        vtt_lines.append(f"{idx}\n{s_vtt} --> {e_vtt}\n{txt}\n")

    os.makedirs('transcripts', exist_ok=True)
    
    with open('transcripts/2_แนวคิดการโฆษณาในยุคดิจิทัล.srt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_lines).strip() + '\n')
        
    with open('transcripts/2_แนวคิดการโฆษณาในยุคดิจิทัล.vtt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(vtt_lines).strip() + '\n')

    with open('transcripts/02_Digital_Advertising_Concepts.srt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_lines).strip() + '\n')

    with open('transcripts/02_Digital_Advertising_Concepts.vtt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(vtt_lines).strip() + '\n')

    print(f"Successfully generated {len(merged_cues)} cues with Spacing Standardization!")

if __name__ == '__main__':
    process()
