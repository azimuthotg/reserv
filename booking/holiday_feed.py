"""ดึงวันหยุดราชการไทยจากปฏิทินสาธารณะ แล้วแปลงเป็นรายการวันที่

ใช้ Google Calendar "วันหยุดในประเทศไทย" (iCal สาธารณะ ไม่ต้องใช้ API key)

⚠️ **ฟีดนี้ไม่ตรงกับวันหยุดราชการ 100% — ผิดได้ทั้งสองทาง** (ตรวจจริง 2026-08-09)
- **มีวันที่ไม่ใช่วันหยุดราชการปนมา** เช่น วันวาเลนไทน์ · ตรุษจีน · คริสต์มาส
  → กรองด้วย `OBSERVANCE_KEYWORDS` แต่กรองไม่หมดแน่นอน
- **ขาดวันหยุดราชการบางวัน** เช่น วันเข้าพรรษา 30 ก.ค. 2569 ไม่มีในฟีด

เพราะแบบนี้ วันที่ดึงมาจึงถูกบันทึกเป็น **ฉบับร่าง (`is_active=False`)** เสมอ
ให้เจ้าหน้าที่เป็นคนเคาะว่าสำนักฯ ปิดวันไหนจริง — ดู `sync_holidays` และ MEM.md
"""
import re
from datetime import date, timedelta

import requests

FEED_URL = ("https://calendar.google.com/calendar/ical/"
            "th.th%23holiday%40group.v.calendar.google.com/public/basic.ics")

TIMEOUT = 20

# วันสำคัญที่ "ไม่ใช่" วันหยุดราชการ — ปนมาในฟีดและไม่ควรเสนอให้ปิดบริการ
OBSERVANCE_KEYWORDS = (
    'วาเลนไทน์', 'ตรุษจีน', 'คริสต์มาส', 'ฮาโลวีน', 'ลอยกระทง',
    'วันพ่อแห่งชาติ (ไม่ใช่วันหยุด)', 'สารทจีน', 'ไหว้พระจันทร์',
)


class HolidayFeedError(RuntimeError):
    pass


def _unfold(text):
    """iCal ตัดบรรทัดยาวด้วยการขึ้นบรรทัดใหม่แล้วเว้นวรรค 1 ตัว — ต่อกลับก่อนแกะ"""
    return re.sub(r'\r?\n[ \t]', '', text)


def _parse_date(raw):
    return date(int(raw[0:4]), int(raw[4:6]), int(raw[6:8]))


def parse_ics(text):
    """แกะ VEVENT แบบวันเต็มออกมาเป็น [(date, summary), ...] เรียงตามวันที่

    รองรับ event ที่กินหลายวัน (DTEND ของ iCal เป็นวันถัดจากวันสุดท้าย)
    """
    out = {}
    for block in _unfold(text).split('BEGIN:VEVENT')[1:]:
        m_start = re.search(r'DTSTART;VALUE=DATE:(\d{8})', block)
        m_sum = re.search(r'\nSUMMARY:(.*)', block)
        if not (m_start and m_sum):
            continue
        summary = m_sum.group(1).strip().replace('​', '')
        start = _parse_date(m_start.group(1))
        m_end = re.search(r'DTEND;VALUE=DATE:(\d{8})', block)
        end = _parse_date(m_end.group(1)) if m_end else start + timedelta(days=1)

        d = start
        while d < end:
            out.setdefault(d, summary)     # วันซ้ำ ให้ยึดรายการแรกที่เจอ
            d += timedelta(days=1)
    return sorted(out.items())


def is_observance(summary):
    """วันสำคัญที่ไม่ใช่วันหยุดราชการ (ไม่ควรเสนอให้ปิดบริการ)"""
    return any(k in summary for k in OBSERVANCE_KEYWORDS)


def fetch_holidays(year=None, start=None, end=None, url=FEED_URL, timeout=TIMEOUT,
                   session=None):
    """ดึงและแกะปฏิทิน คืน [(date, summary), ...] — กรองวันสำคัญที่ไม่ใช่วันหยุดออกแล้ว

    กรองได้ 2 แบบ (ใช้ร่วมกันได้)
    - `year` — เฉพาะปีนั้น (ค.ศ.) ใช้กับปุ่ม "ดึงวันหยุดราชการ <ปี>" ในหน้าเจ้าหน้าที่
    - `start` / `end` — ช่วงวันที่ (รวมปลายทั้งสองข้าง) ใช้กับหน้าต่างกลิ้ง 12 เดือนของ command

    ไม่ระบุอะไรเลย = คืนทุกปีที่ฟีดมี (ปัจจุบัน 2021–2031)
    """
    getter = (session or requests).get
    try:
        resp = getter(url, timeout=timeout)
    except requests.RequestException as exc:
        raise HolidayFeedError(f'เชื่อมต่อปฏิทินวันหยุดไม่ได้: {exc}') from exc
    if resp.status_code != 200:
        raise HolidayFeedError(f'ปฏิทินวันหยุดตอบกลับ HTTP {resp.status_code}')

    events = parse_ics(resp.content.decode('utf-8'))
    return [
        (d, s) for d, s in events
        if (year is None or d.year == year)
        and (start is None or d >= start)
        and (end is None or d <= end)
        and not is_observance(s)
    ]
