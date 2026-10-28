#!/usr/bin/env python3
"""
Helper script to clean, validate boundaries, and format Thai subtitles for Open edX.
Includes bidirectional context checking (Look-behind & Look-ahead) and single-line formatting.
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
    (r'แอปพลิเคชั', 'แอปพลิเคชัน'),
    (r'ดาวน์โหลดนานะ คะ', 'ดาวน์โหลด Now นะคะ'),
    (r'ดาวน์โหลดนา', 'ดาวน์โหลด Now'),
    (r'ขั้นเวลา', 'คั่นเวลา'),
    (r'digital\s+advertising', 'Digital Advertising'),
    (r'traditional\s*advertising', 'Traditional Advertising'),
    (r'call\s+to\s*action', 'Call to Action'),
    (r'audience\s*segmentation', 'Audience Segmentation'),
    (r'\bawareness\b', 'Awareness'),
    (r'\bconsideration\b', 'Consideration'),
    (r'\bdecision\b', 'Decision'),
    (r'Story ของเพื่อน', 'Stories ของเพื่อน')
]

def clean_thai_text(text: str) -> str:
    """Correct speech recognition errors while keeping verbatim words."""
    for pattern, repl in COMMON_TYPOS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text

def validate_bidirectional_boundaries(cues):
    """
    Perform Look-behind and Look-ahead checks across adjacent cues:
    - Heal split compound words (e.g. ลูก-ค้า, ตัดสิน-ใจ)
    - Reconnect dangling prepositions / nouns (e.g. แบรนด์ของ + เรา)
    - Ensure English technical terms stay unified (Call to Action, Audience Segmentation)
    """
    cleaned_cues = []
    for cue in cues:
        timing, text = cue['timing'], clean_thai_text(cue['text'])
        cleaned_cues.append({'timing': timing, 'text': text})
    
    # Cross-cue boundary adjustments
    for i in range(len(cleaned_cues) - 1):
        cur_txt = cleaned_cues[i]['text']
        next_txt = cleaned_cues[i+1]['text']
        
        # Example look-ahead/behind healing patterns:
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
    print("Thai Open edX Subtitle Helper initialized with Bidirectional Validation.")
