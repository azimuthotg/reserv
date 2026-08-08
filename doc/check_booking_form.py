"""ตรวจฟอร์มจอง LIFF บน production ด้วย Playwright (headed ผ่าน WSLg)

ใช้ตรวจว่ากติกาเวลาในหน้าจองทำงานถูกต้องบนของจริง — เวลาเปิด-ปิดของแต่ละห้อง,
ห้องที่ปิดรอบกลางวัน, การไม่ให้จองคร่อมรอบ, และปุ่มจองด่วนที่ควรซ่อน/แสดง

**อ่านอย่างเดียว — ไม่กดยืนยันการจอง ไม่สร้างข้อมูลใด ๆ บน production**

    wsl -d Ubuntu -- python3 /mnt/c/projects/reserv/doc/check_booking_form.py

หมายเหตุการใช้งาน (เจ็บมาแล้ว ดู MEM.md 2026-08-08):
- ต้องรันใน WSL เพราะ playwright ติดตั้งไว้ที่นั่น และต้องเรียกผ่าน PowerShell
  ไม่ใช่ Git Bash (Git Bash แปลง /mnt/c/... เป็น path วินโดวส์แล้วหาไฟล์ไม่เจอ)
- ครั้งแรกจะเปิดหน้าต่างให้ล็อกอิน LINE เอง จากนั้น session ถูกเก็บไว้ใน PROFILE
  ครั้งต่อไปไม่ต้องล็อกอินซ้ำ
- ช่องวันที่เป็น flatpickr แบบ readonly การ set .value ตรง ๆ **ไม่ทำให้ dropdown rebuild**
  จึงเรียก buildStartOptions()/buildEndOptions() ของหน้าเว็บโดยตรง
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "https://lib.npu.ac.th/reserv"
PROFILE = "/home/admin_e/.cache/reserv-liff-profile"
LOGIN_TIMEOUT = 15 * 60  # ผู้ใช้มีเวลา 15 นาทีในการล็อกอิน

# playwright 1.58 มองหา chromium-1208 แต่เครื่องนี้มี 1217 ที่ติดตั้งไว้แล้ว
# ชี้ไปที่ตัวที่มีอยู่ เพื่อไม่ต้องดาวน์โหลดเบราว์เซอร์ใหม่
CHROME = "/home/admin_e/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome"

READ_FORM = """() => {
  const sel = document.getElementById('start_time');
  const opts = sel ? [...sel.options].map(o => o.value).filter(Boolean) : [];
  const quick = document.getElementById('quick-btns');
  return {
    room:        document.getElementById('room-name')?.textContent?.trim(),
    hours:       document.getElementById('room-hours')?.textContent?.trim(),
    quickShown:  quick ? getComputedStyle(quick).display !== 'none' : null,
    divider:     document.getElementById('or-divider')?.textContent?.trim(),
    date:        document.getElementById('booking_date')?.value,
    startCount:  opts.length,
    firstThree:  opts.slice(0, 3),
    lastThree:   opts.slice(-3),
    daySlots:    opts.filter(v => v >= '08:30' && v < '17:00').length,
    nightSlots:  opts.filter(v => v >= '17:00').length,
    earlySlots:  opts.filter(v => v < '08:30').length,
  };
}"""

# input วันที่เป็น flatpickr (readonly) ตั้ง value ตรง ๆ ไม่ทำให้ dropdown rebuild
# จึงเรียกฟังก์ชันของหน้าเว็บเองซึ่งเป็นตัวที่เราแก้จริง ๆ
REBUILD = """(dateStr) => {
  document.getElementById('booking_date').value = dateStr;
  buildStartOptions(dateStr);
  return dateStr;
}"""

END_FOR = """(hhmm) => {
  buildEndOptions(timeToMin(hhmm));
  const sel = document.getElementById('end_time');
  const v = [...sel.options].map(o => o.value).filter(Boolean);
  return {count: v.length, first: v[0] || null, last: v[v.length - 1] || null};
}"""

READ_END_OPTIONS = """() => {
  const sel = document.getElementById('end_time');
  return [...sel.options].map(o => o.value).filter(Boolean);
}"""


def wait_for_form(page):
    """รอจนผู้ใช้ล็อกอิน LINE เสร็จและฟอร์มพร้อมใช้งาน"""
    deadline = time.time() + LOGIN_TIMEOUT
    notified = False
    while time.time() < deadline:
        url = page.url
        if '/register/' in url:
            print('!! หน้าเด้งไป /register/ — บัญชี LINE นี้ยังไม่ได้ผูกกับระบบ', flush=True)
            return False
        try:
            ready = page.evaluate(
                "() => !!document.getElementById('start_time') "
                "&& document.getElementById('start_time').options.length > 1"
            )
        except Exception:
            ready = False
        if ready:
            print('>> ล็อกอินเรียบร้อย ฟอร์มพร้อมแล้ว เริ่มตรวจ', flush=True)
            return True
        if not notified and 'line.me' in url:
            print('>> กรุณาล็อกอิน LINE ในหน้าต่างที่เปิดขึ้นมา (รอได้ 15 นาที)', flush=True)
            notified = True
        time.sleep(2)
    print('!! หมดเวลารอล็อกอิน', flush=True)
    return False


TARGET_DATE = '2026-08-10'   # วันจันทร์ — วันทำการปกติ อยู่ในช่วงจองล่วงหน้าได้


def check_room(page, key, expect):
    page.goto(f'{BASE}/booking/?room={key}', wait_until='domcontentloaded')
    page.wait_for_timeout(2500)
    if not page.evaluate("() => !!document.getElementById('start_time')"):
        return {'room_key': key, 'error': 'ไม่พบฟอร์ม (อาจถูก redirect)', 'url': page.url}

    page.evaluate(REBUILD, TARGET_DATE)
    page.wait_for_timeout(400)
    data = page.evaluate(READ_FORM)
    data['room_key'] = key
    data['expect'] = expect
    data['checked_date'] = TARGET_DATE

    starts = page.evaluate(
        "() => [...document.getElementById('start_time').options].map(o=>o.value).filter(Boolean)")
    # ตรวจเพดานเวลาสิ้นสุดของแต่ละรอบ (ต้องไม่คร่อมรอบ)
    caps = {}
    for probe in ('06:00', '16:00', '20:00'):
        caps[probe] = page.evaluate(END_FOR, probe) if probe in starts \
            else 'ไม่มีตัวเลือกนี้ใน dropdown'
    data['end_cap'] = caps
    return data


def main():
    results = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport={'width': 430, 'height': 900},
            executable_path=CHROME, args=['--no-sandbox'],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print('>> เปิดหน้าจอง Netflix Pro ...', flush=True)
        page.goto(f'{BASE}/booking/?room=netflix1_vm', wait_until='domcontentloaded')
        page.wait_for_timeout(3000)

        if not wait_for_form(page):
            ctx.close()
            sys.exit(1)

        for key, expect in (('netflix1_vm', 'ไม่มี slot กลางวัน'),
                            ('canva2',      'มี slot ครบทุกรอบ ไม่มีปุ่มจองด่วน'),
                            ('mini',        'เหมือนเดิม 08:30-16:30 มีปุ่มจองด่วน')):
            print(f'>> ตรวจ {key} ...', flush=True)
            results.append(check_room(page, key, expect))

        ctx.close()

    print('\n===== ผลตรวจ =====', flush=True)
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
