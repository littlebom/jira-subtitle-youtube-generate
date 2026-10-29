#!/usr/bin/env python3
"""
Helper script to clean, validate boundaries, and format Thai subtitles for Open edX.
Includes:
- STT error correction
- Bidirectional context checking (Look-behind & Look-ahead)
- Thai-English, numeric, and clause spacing standardization
- Single-line formatting for Open edX video components
"""
import re
import sys
import os

COMMON_TYPOS = [
    (r'ดิจิตอล', 'ดิจิทัล'),
    (r'ป้ายบิบอร์ด', 'ป้ายบิลบอร์ด'),
    (r'บิบอร์ด', 'บิลบอร์ด'),
    (r'พรีเซ็นตอร', 'พรีเซนเตอร์'),
    (r'แอปพลิเคชัก็', 'แอปพลิเคชันก็'),
    (r'แอปพลิเคชั\b', 'แอปพลิเคชัน'),
    (r'ดาวน์โหลดนานะ คะ', 'ดาวน์โหลด Now นะคะ'),
    (r'ดาวน์โหลดนา', 'ดาวน์โหลด Now'),
    (r'ขั้นเวลา', 'คั่นเวลา'),
    (r'แนวนนโนม', 'แนวโน้ม'),
    (r'\bเาเพิ่ม\b', 'เพิ่ม'),
    (r'\bเา้า\b', 'เขา'),
    (r'โซเชียลมีดีย', 'โซเชียลมีเดีย'),
    (r'VR\s+Social', 'We Are Social'),
    (r'Host\s+Sweet', 'Hootsuite'),
    (r'Vimio', 'Vimeo'),
    (r'\bpersuate\b', 'Persuade'),
    (r'รีind', 'Remind'),
    (r'แจกเวชอร์', 'แจก Voucher'),
    (r'มีเวอร์แจก', 'มี Voucher แจก'),
    (r'\bby\s+now\b', 'Buy Now'),
    (r'สร้างความcreเอที', 'สร้างความ Creative'),
    (r'Audi\s+ของ\s+Facebook\s+Ad', 'Audience ของ Facebook Ads'),
    (r'เลือกแอ\s+format', 'เลือก Ad Format'),
    (r'decision\s+state', 'Decision Stage'),
    (r'buyer\s+Journey', "Buyer's Journey"),
    (r'Buyer\s+Journey', "Buyer's Journey"),
    (r'call\s+to\s*action', 'Call to Action'),
    (r'contact\s+us', 'Contact Us'),
    (r'get\s+free\s+consultant', 'Get Free Consultant'),
    (r'Body\s+Shop', 'The Body Shop'),
    (r'digital\s+advertising', 'Digital Advertising'),
    (r'traditional\s*advertising', 'Traditional Advertising'),
    (r'audience\s*segmentation', 'Audience Segmentation'),
    (r'\bawareness\b', 'Awareness'),
    (r'\bconsideration\b', 'Consideration'),
    (r'\bdecision\b', 'Decision'),
    (r'\bremind\b', 'Remind'),
    (r'\binform\b', 'Inform'),
    (r'\breport\b', 'Report'),
    (r'Story ของเพื่อน', 'Stories ของเพื่อน'),
    (r'วีดีโอ', 'วิดีโอ'),
    (r'คลิปถัดถัดไป', 'คลิปถัดไป')
]

def clean_thai_text(text: str) -> str:
    """Correct speech recognition errors while keeping verbatim words."""
    for pattern, repl in COMMON_TYPOS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text

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
    
    # Spacing around Maiyamok (ๆ) - space before and after
    text = re.sub(r'\s*ๆ\s*', ' ๆ ', text)
    
    # Spacing after %
    text = re.sub(r'%([ก-๙])', r'% \1', text)
    
    # Clause spacing after polite endings
    text = re.sub(r'(นะคะ|ค่ะ|ครับ)([ก-๙])', r'\1 \2', text)
    
    # Remove unwanted space before Thai punctuation / question marks
    text = re.sub(r'\s+([?.!,])', r'\1', text)
    
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return text

def validate_bidirectional_boundaries(cues):
    """
    Perform Look-behind and Look-ahead checks across adjacent cues:
    - Move leading 'นะคะ' to the previous cue/section
    - Heal split compound words (e.g. ลูก-ค้า, ตัดสิน-ใจ, ข้อ-มูล, เป้า-หมาย)
    - Reconnect dangling prepositions / nouns (e.g. แบรนด์ของ + เรา)
    - Ensure English technical terms stay unified (Call to Action, Audience Segmentation)
    """
    cleaned_cues = []
    for cue in cues:
        timing = cue['timing']
        text = clean_thai_text(cue['text'])
        text = standardize_spacing(text)
        cleaned_cues.append({'timing': timing, 'text': text})
    
    # Cross-cue boundary adjustments & moving leading polite particles
    for i in range(len(cleaned_cues) - 1):
        c1 = cleaned_cues[i]
        c2 = cleaned_cues[i+1]
        
        # 1. Healing split นะ / คะ
        if c1['text'].strip().endswith('นะ') and re.match(r'^คะ', c2['text'].strip()):
            c1['text'] = re.sub(r'นะ$', 'นะคะ', c1['text'].strip())
            c2['text'] = re.sub(r'^คะ\s*', '', c2['text'].strip())

        # 2. Move leading นะคะ to previous cue/section
        if re.match(r'^(?:นะคะ|นะ\s+คะ)', c2['text'].strip()):
            c2['text'] = re.sub(r'^(?:นะคะ|นะ\s+คะ)\s*', '', c2['text'].strip())
            c1_txt = c1['text'].strip()
            if not c1_txt.endswith('นะคะ'):
                c1['text'] = c1_txt + ' นะคะ'

        cur_txt = cleaned_cues[i]['text']
        next_txt = cleaned_cues[i+1]['text']
        
        # Example healing patterns
        if cur_txt.endswith('ทำให้ลูก') and next_txt.startswith('ค้า'):
            cleaned_cues[i]['text'] = cur_txt + 'ค้า'
            cleaned_cues[i+1]['text'] = next_txt[3:].strip()
        
        if cur_txt.endswith('ตัดสิน') and next_txt.startswith('ใจ'):
            cleaned_cues[i]['text'] = cur_txt + 'ใจ'
            cleaned_cues[i+1]['text'] = next_txt[2:].strip()
            
        if cur_txt.endswith('ค้นหาข้อ') and next_txt.startswith('มูล'):
            cleaned_cues[i]['text'] = cur_txt + 'มูล'
            cleaned_cues[i+1]['text'] = next_txt[3:].strip()

        if cur_txt.endswith('แบรนด์ของ') and next_txt.startswith('เรา'):
            cleaned_cues[i]['text'] = cur_txt + 'เรา'
            cleaned_cues[i+1]['text'] = next_txt[3:].strip()

    return cleaned_cues

def format_single_line(cues):
    """Format each cue into a single clean line for Open edX."""
    formatted = []
    for idx, cue in enumerate(cues, 1):
        text = ' '.join(cue['text'].split())
        formatted.append(f"{idx}\n{cue['timing']}\n{text}\n")
    return '\n'.join(formatted)

if __name__ == '__main__':
    print("Thai Open edX Subtitle Helper initialized with Spacing & Bidirectional Validation.")
