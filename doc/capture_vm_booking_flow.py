"""แคปขั้นตอนการจองบริการเครื่องเสมือน (Canva Pro / ChatGPT) จาก production

ใช้ทำคู่มือ "ขั้นตอนการจองใช้บริการ VM" สำหรับแจกผู้ใช้ก่อนเปิด Rich Menu บน LINE OA
ภาพ 1920x1080 เก็บที่ doc/screenshots/vmflow/

    wsl -d Ubuntu -u admin_e -- python3 /mnt/c/projects/reserv/doc/capture_vm_booking_flow.py

⚠️ **สคริปต์นี้สร้างการจองจริงบน production แล้วยกเลิกให้เองตอนจบ**
เพราะหน้า "จองสำเร็จ" และ "การจองของฉัน" แคปไม่ได้ถ้าไม่มีการจองจริง
- จองห้อง `canva` วันพรุ่งนี้ **รอบเช้ามืด 06:00–07:00** (ช่วงที่มีคนใช้น้อยที่สุด) เพียง 1 ชั่วโมง
- ตั้ง `group_name` เป็นข้อความทดสอบที่ระบุตัวได้ชัด แล้ว**ยกเลิกเฉพาะรายการที่มีข้อความนั้น**
- ห้อง `chat-gpt` แคปแค่หน้าฟอร์ม **ไม่จอง** เพราะขั้นตอนเหมือนกันทุกประการ
  และการจอง 2 ห้องเวลาเดียวกันติดกติกา "ห้ามจองทับเวลาข้ามห้อง" อยู่แล้ว
- ถ้าสคริปต์หยุดกลางคัน **ต้องเข้าไปยกเลิกเองที่ /manage/bookings/** (ดูข้อความที่พิมพ์ออกมา)

หมายเหตุการใช้งาน (ดู MEM.md 2026-08-08 · 2026-08-09):
- ต้องรันใน WSL ผ่าน PowerShell ไม่ใช่ Git Bash (Git Bash แปลง /mnt/c/... เป็น path วินโดวส์)
- ครั้งแรกจะเปิดหน้าต่างให้ล็อกอิน LINE เอง จากนั้น session ถูกเก็บใน PROFILE เดียวกับสคริปต์อื่น
- playwright 1.58 มองหา chromium-1208 แต่เครื่องนี้มี 1217 — หา binary เองด้วย chromium_path()
"""
import glob
import os
import sys
import time
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

BASE    = "https://lib.npu.ac.th/reserv"
HERE    = os.path.dirname(os.path.abspath(__file__))
SHOTS   = os.path.join(HERE, "screenshots", "vmflow")
PROFILE = "/home/admin_e/.cache/reserv-liff-profile"

# หน้าผู้ใช้ทั้งหมดเป็น mobile-first (max-width 480px) — แคปที่ 1920 กว้าง เนื้อหาจริง
# กินแค่ ~27% ของเฟรม พอย่อลงคู่มือกว้าง 16.2 ซม. ตัวหนังสือเหลือกว้างจริง ~4.4 ซม. อ่านไม่ออก
# 760px คือความกว้างที่เนื้อหาเต็มเฟรมพอดีและยังเป็นหน้าต่างเบราว์เซอร์บน PC (เท่าหน้าต่าง LIFF
# ที่ LINE PC เปิดจริง) · scale 2 เท่าเพื่อให้ภาพคมพอสำหรับงานพิมพ์
VIEWPORT      = {"width": 760, "height": 1040}
SCALE         = 2
LOGIN_TIMEOUT = 10 * 60

ROOM_BOOK = "canva"        # ห้องที่จองจริงจนจบขั้นตอน
ROOM_ALSO = "chat-gpt"     # แคปแค่ฟอร์ม ขั้นตอนเหมือนกัน

# ข้อความที่ใช้ระบุว่าเป็นการจองของสคริปต์นี้ — ใช้หาแถวตอนยกเลิก ห้ามเปลี่ยนกลางคัน
GROUP_NAME = "ทดสอบขั้นตอนการจอง (เจ้าหน้าที่)"
ATTENDEES  = "เจ้าหน้าที่สำนักวิทยบริการ"

# โหมด --button-shot: แคปปุ่ม "เข้าใช้งาน" ของห้องออนไลน์
# ปุ่มโผล่เฉพาะ 5 นาทีก่อนเวลาเริ่มจนสิ้นสุดการจอง สคริปต์จองเองไม่ได้เพราะการจอง
# แบบนั้นต้องเริ่มในอีกไม่กี่นาที และ **ยกเลิกไม่ได้เลยหลังถึงเวลาเริ่ม** (API บล็อก)
# จึงให้เจ้าหน้าที่จองเองแล้วสคริปต์มาแคป + ยกเลิกให้ก่อนถึงเวลาเริ่ม
BUTTON_GROUP_NAME = "ทดสอบปุ่มเข้าใช้งาน"

BOOK_DATE  = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
BOOK_START = "06:00"
BOOK_END   = "07:00"


def chromium_path():
    """หา chrome ที่ติดตั้งไว้จริงใน ms-playwright cache (revision ไม่ตรงกับที่ playwright คาด)"""
    cache = os.path.expanduser("~/.cache/ms-playwright")
    found = sorted(glob.glob(os.path.join(cache, "chromium-*", "chrome-linux64", "chrome")))
    return found[-1] if found else None


def shot(page, name, wait=900, full=False):
    os.makedirs(SHOTS, exist_ok=True)
    page.wait_for_timeout(wait)
    path = os.path.join(SHOTS, f"{name}.png")
    page.screenshot(path=path, full_page=full)
    print("   บันทึกแล้ว:", os.path.basename(path), flush=True)


def tall_shot(page, name, anchor=None, max_h=1700):
    """แคปหน้าที่ยาวเกินจอ โดย**ขยายความสูงของ viewport** ไม่ใช่ full_page

    `page.screenshot(full_page=True)` ใช้กับหน้านี้ไม่ได้ — bottom sheet รายละเอียดการจอง
    เป็น `position: fixed` ที่ปกติซ่อนอยู่นอกจอ พอ playwright ต่อภาพทีละจอ มันถูกวาดซ้ำ
    ลงกลางภาพจนบังการ์ดห้อง Canva Pro 2 กับ ChatGPT ทั้งใบ (เจอจริงรอบ 2026-08-10)

    จำกัดความสูงไว้ที่ max_h เพราะภาพที่สูงกว่านี้ใส่ลงคู่มือ A4 แล้วล้นหน้ากระดาษ
    anchor = css selector ที่ต้องการให้อยู่บนสุดของภาพ
    """
    height = page.evaluate("() => document.documentElement.scrollHeight")
    page.set_viewport_size({"width": VIEWPORT["width"], "height": min(max(height, 600), max_h)})
    page.wait_for_timeout(600)
    load_all_images(page)
    if anchor:
        page.evaluate("(sel) => document.querySelector(sel)?.scrollIntoView(true)", anchor)
        page.wait_for_timeout(500)
    shot(page, name)
    page.set_viewport_size(VIEWPORT)
    page.wait_for_timeout(400)


def load_all_images(page):
    """เลื่อนลงสุดแล้วกลับขึ้นบน เพื่อบังคับให้รูปห้องที่โหลดแบบ lazy โหลดครบก่อนแคป

    รอบแรกที่ทำได้ภาพหน้าแรกที่รูปห้องยังขาวอยู่ทั้งใบ
    """
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1200)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(600)


def wait_for_login(page):
    """รอจนผู้ใช้ล็อกอิน LINE เสร็จและหน้าแรกโหลดรายการห้องได้"""
    deadline = time.time() + LOGIN_TIMEOUT
    notified = False
    while time.time() < deadline:
        if "/register/" in page.url:
            print("!! เด้งไป /register/ — บัญชี LINE นี้ยังไม่ได้ผูกกับระบบ", flush=True)
            return False
        try:
            ready = page.evaluate(
                "() => { const el = document.getElementById('room-list');"
                " return !!el && el.children.length > 0; }")
        except Exception:
            ready = False
        if ready:
            print(">> ล็อกอินเรียบร้อย เริ่มแคปภาพ", flush=True)
            return True
        if not notified and "line.me" in page.url:
            print(">> กรุณาล็อกอิน LINE ในหน้าต่างที่เปิดขึ้นมา (รอได้ 10 นาที)", flush=True)
            notified = True
        time.sleep(2)
    print("!! หมดเวลารอล็อกอิน", flush=True)
    return False


def open_booking_form(page, room_key):
    """เปิดหน้าฟอร์มจองและรอจน dropdown เวลาถูกสร้างเสร็จ"""
    page.goto(f"{BASE}/booking/?room={room_key}", wait_until="domcontentloaded")
    for _ in range(30):
        page.wait_for_timeout(500)
        if page.evaluate("() => !!document.getElementById('start_time')"
                         " && document.getElementById('start_time').options.length > 1"):
            return True
    return False


def fill_form(page):
    """กรอกฟอร์มผ่านทางเดียวกับที่ผู้ใช้ทำจริง

    ใช้ `_picker.setDate(d, true)` แทนการ set .value ตรง ๆ เพราะช่องวันที่เป็น flatpickr
    แบบ readonly — set value เฉย ๆ จะไม่ยิง onChange ทำให้ dropdown เวลาไม่ถูกสร้างใหม่
    (ดู MEM.md 2026-08-08)
    """
    page.evaluate("(d) => _picker.setDate(d, true)", BOOK_DATE)
    page.wait_for_timeout(1500)                       # onChange ยิง fetch การจองของวันนั้น
    page.select_option("#start_time", BOOK_START)     # onchange → buildEndOptions()
    page.wait_for_timeout(600)
    page.select_option("#end_time", BOOK_END)
    page.fill("#group_name", GROUP_NAME)
    page.fill("#attendees", ATTENDEES)


def find_our_booking(page):
    """คืน id ของการจองที่สคริปต์นี้สร้างและ**ยังไม่ถูกยกเลิก**

    หาแบบเจาะจงจาก group_name เสมอ ห้ามใช้ "รายการล่าสุด" — ผู้ใช้อาจมีการจองจริงของตัวเองอยู่ด้วย

    ต้องข้ามการ์ดที่ยกเลิกแล้ว (class `cancelled`) ด้วย ไม่งั้นรอบถัดไปจะไปเจอการ์ดของ
    รอบก่อนซึ่งมีชื่อกลุ่มเดียวกัน แล้วพยายามยกเลิกใบที่ยกเลิกไปแล้ว ปล่อยให้การจองใบใหม่
    ค้างอยู่บน production (เกิดขึ้นจริงรอบ 2026-08-10 — ทิ้ง booking #515 ไว้)
    """
    return page.evaluate(
        """(marker) => {
            for (const card of document.querySelectorAll('.my-booking-card')) {
                if (card.classList.contains('cancelled')) continue;
                const g = card.querySelector('.mbk-group');
                if (g && g.textContent.trim() === marker) {
                    return card.id.replace('bk-', '');
                }
            }
            return null;
        }""", GROUP_NAME)


def cancel_booking(page, booking_id):
    """ยกเลิกผ่านปุ่มในหน้าเว็บ (ไม่แก้ฐานตรง ๆ) เพื่อให้ audit log และการแจ้งเตือนทำงานตามปกติ"""
    page.wait_for_selector(f"#bk-{booking_id} .btn-cancel-bk", timeout=30000)
    page.click(f"#bk-{booking_id} .btn-cancel-bk")
    page.wait_for_timeout(2500)


def hide_stale_test_cards(page, keep_id=None):
    """ซ่อนการ์ดการจองทดสอบของรอบก่อน ๆ ออกจากภาพ (เฉพาะตอนแคป ไม่แตะข้อมูล)

    การจองที่ยกเลิกแล้วยังแสดงอยู่ในรายการของผู้ใช้ต่อไป พอรันสคริปต์ซ้ำหลายรอบ
    ภาพจะมีการ์ด "ยกเลิกแล้ว" ชื่อกลุ่มเดียวกันซ้อนกันหลายใบ ซึ่งเป็นขยะจากกระบวนการ
    แคปเอง ไม่ใช่สิ่งที่ผู้ใช้จริงจะเห็น — ซ่อนออกเพื่อให้ภาพในคู่มือสื่อสารตรงความจริง
    เก็บไว้เฉพาะใบของรอบปัจจุบัน (keep_id) ซึ่งเป็นใบที่คู่มืออธิบายถึง
    """
    page.evaluate(
        """(args) => {
            for (const card of document.querySelectorAll('.my-booking-card')) {
                if (args.keep && card.id === 'bk-' + args.keep) continue;
                const g = card.querySelector('.mbk-group');
                if (g && g.textContent.trim() === args.marker) card.style.display = 'none';
            }
        }""", {"marker": GROUP_NAME, "keep": keep_id})


def wait_bookings(page):
    """รอให้ส่วน "การจองของฉัน" โหลดเสร็จ — ผู้ใช้ที่ไม่มีการจองเลยก็ผ่านได้

    ส่วนนี้โหลดผ่าน API แยกจากรายการห้อง ถ้าไม่รอ การเก็บกวาด/ซ่อนการ์ดจะทำงานกับ
    DOM ที่ยังว่างอยู่ แล้วการ์ดค่อยโผล่มาทีหลังในภาพ
    """
    try:
        page.wait_for_selector(".my-booking-card", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(800)


def cancel_leftovers(page):
    """เก็บกวาดการจองทดสอบที่ค้างจากรอบก่อน ก่อนเริ่มแคปรอบใหม่

    ทำให้สคริปต์รันซ้ำได้อย่างปลอดภัย — ถ้ารอบก่อนพังกลางคัน รอบนี้เคลียร์ให้เอง
    """
    for _ in range(5):
        stale = find_our_booking(page)
        if not stale:
            return
        print(f"   พบการจองทดสอบค้างจากรอบก่อน id={stale} — ยกเลิกให้", flush=True)
        try:
            cancel_booking(page, stale)
        except Exception as exc:
            print(f"!! ยกเลิก id={stale} ไม่สำเร็จ ({exc}) — ต้องยกเลิกเองที่ /manage/bookings/",
                  flush=True)
            return
        page.reload(wait_until="domcontentloaded")
        wait_bookings(page)


def find_booking_by_group(page, marker):
    """หาการ์ดการจองที่ยังไม่ถูกยกเลิก ตามชื่อกลุ่มที่กำหนด"""
    return page.evaluate(
        """(marker) => {
            for (const card of document.querySelectorAll('.my-booking-card')) {
                if (card.classList.contains('cancelled')) continue;
                const g = card.querySelector('.mbk-group');
                if (g && g.textContent.trim() === marker) {
                    return card.id.replace('bk-', '');
                }
            }
            return null;
        }""", marker)


def button_shot_mode(booking_id=None):
    """แคปปุ่ม "เข้าใช้งาน" จากการจองที่เจ้าหน้าที่จองไว้ให้ แล้วยกเลิกให้

    ต้องรันในช่วง 5 นาทีก่อนเวลาเริ่มของการจองนั้น — เร็วกว่านั้นปุ่มยังไม่ขึ้น
    ช้ากว่านั้น (เลยเวลาเริ่ม) ปุ่มขึ้นแต่ยกเลิกไม่ได้อีกแล้ว

    ระบุ --booking-id ได้ตรง ๆ ซึ่งแม่นกว่าการหาจากชื่อกลุ่ม เพราะชื่อกลุ่มซ้ำกันได้
    ระหว่างการจองหลายใบของคนเดียวกัน
    """
    chrome = chromium_path()
    print("chromium:", chrome or "(ใช้ค่า default)", flush=True)
    if booking_id:
        print(f"ใช้การจองเลขที่ #{booking_id}", flush=True)
    else:
        print(f"หาการจองชื่อกลุ่ม {BUTTON_GROUP_NAME!r}", flush=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport=VIEWPORT, device_scale_factor=SCALE,
            executable_path=chrome, args=["--no-sandbox"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("dialog", lambda d: d.accept())

        page.goto(f"{BASE}/", wait_until="domcontentloaded")
        if not wait_for_login(page):
            ctx.close()
            sys.exit(1)
        wait_bookings(page)

        if booking_id:
            if not page.evaluate("(id) => !!document.getElementById('bk-' + id)", booking_id):
                ctx.close()
                sys.exit(f"ไม่พบการ์ดของการจอง #{booking_id} ในหน้าแรก")
        else:
            booking_id = find_booking_by_group(page, BUTTON_GROUP_NAME)
            if not booking_id:
                ctx.close()
                sys.exit(f"ไม่พบการจองชื่อกลุ่ม {BUTTON_GROUP_NAME!r} — ตรวจว่าจองแล้วและชื่อตรงกัน")
        print("   booking id =", booking_id, flush=True)

        has_button = page.evaluate(
            "(id) => !!document.querySelector('#bk-' + id + ' a[target=\"_blank\"]')", booking_id)
        if not has_button:
            print("!! ปุ่ม 'เข้าใช้งาน' ยังไม่ขึ้น — ยังไม่ถึง 5 นาทีก่อนเวลาเริ่ม", flush=True)
            print("!! รอให้ถึงเวลาแล้วรันใหม่ (ยังไม่ยกเลิกอะไรทั้งสิ้น)", flush=True)
            ctx.close()
            sys.exit(1)

        hide_stale_test_cards(page, booking_id)
        shot(page, "12_vm_access_button")

        print("ยกเลิกการจองทดสอบ", flush=True)
        try:
            page.evaluate("(id) => cancelBooking(Number(id), 'ทดสอบ', 'ทดสอบ')", booking_id)
            page.wait_for_timeout(3000)
            print("   สั่งยกเลิกแล้ว — ตรวจผลอีกทีที่ฐานข้อมูล", flush=True)
        except Exception as exc:
            print(f"!! ยกเลิกไม่สำเร็จ ({exc}) — ยกเลิกเองที่ {BASE}/manage/bookings/", flush=True)

        ctx.close()
    print("\nเสร็จแล้ว — ภาพ 12_vm_access_button.png", flush=True)


def rooms_only_mode():
    """แคปเฉพาะหน้ารายละเอียดห้อง — เป็นหน้าสาธารณะ ไม่ต้องล็อกอิน ไม่แตะการจองใด ๆ

    ใช้เมื่อแก้เนื้อหาห้องแล้วต้องการภาพใหม่ โดยไม่ต้องเดินขั้นตอนจองทั้งชุดซ้ำ
    """
    chrome = chromium_path()
    print("chromium:", chrome or "(ใช้ค่า default)", flush=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport=VIEWPORT, device_scale_factor=SCALE,
            executable_path=chrome, args=["--no-sandbox"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for key, name in ((ROOM_BOOK, "02_room_detail_canva"),
                          (ROOM_ALSO, "03_room_detail_chatgpt")):
            print(f"[{key}]", flush=True)
            page.goto(f"{BASE}/room/{key}/", wait_until="networkidle")
            tall_shot(page, name, max_h=2400)
        ctx.close()
    print("เสร็จแล้ว", flush=True)


def main():
    if "--rooms-only" in sys.argv:
        rooms_only_mode()
        return
    if "--button-shot" in sys.argv:
        bid = None
        if "--booking-id" in sys.argv:
            bid = sys.argv[sys.argv.index("--booking-id") + 1]
        button_shot_mode(bid)
        return

    chrome = chromium_path()
    print("chromium:", chrome or "(ใช้ค่า default ของ playwright)", flush=True)
    print(f"จะจอง {ROOM_BOOK} วันที่ {BOOK_DATE} เวลา {BOOK_START}-{BOOK_END}"
          f" แล้วยกเลิกให้ตอนจบ", flush=True)

    booking_id = None
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport=VIEWPORT, device_scale_factor=SCALE,
            executable_path=chrome, args=["--no-sandbox"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # ปุ่มยกเลิกใช้ confirm() ถ้าไม่รับ dialog ไว้ playwright จะกด "ยกเลิก" ให้อัตโนมัติ
        page.on("dialog", lambda d: d.accept())

        try:
            print("[1] หน้าแรก — เลือกบริการ", flush=True)
            page.goto(f"{BASE}/", wait_until="domcontentloaded")
            if not wait_for_login(page):
                ctx.close()
                sys.exit(1)
            wait_bookings(page)
            cancel_leftovers(page)
            hide_stale_test_cards(page)
            tall_shot(page, "01_landing_room_list")
            # เลื่อนให้รายการห้องอยู่บนสุด เพื่อให้เห็นบริการ VM ทั้ง 3 ตัวในภาพเดียว
            tall_shot(page, "01b_landing_vm_services", anchor="#room-list")

            print("[2] หน้ารายละเอียดห้อง", flush=True)
            page.goto(f"{BASE}/room/{ROOM_BOOK}/", wait_until="networkidle")
            tall_shot(page, "02_room_detail_canva")
            page.goto(f"{BASE}/room/{ROOM_ALSO}/", wait_until="networkidle")
            tall_shot(page, "03_room_detail_chatgpt")

            print("[3] ฟอร์มจอง — ยังไม่กรอก", flush=True)
            if not open_booking_form(page, ROOM_BOOK):
                raise RuntimeError("เปิดฟอร์มจอง canva ไม่สำเร็จ")
            shot(page, "04_booking_form_empty")

            print("[4] เลือกวันที่ (ปฏิทิน)", flush=True)
            page.click("#booking_date")
            shot(page, "05_date_picker_open", wait=600)
            page.keyboard.press("Escape")

            print("[5] กรอกฟอร์มครบ", flush=True)
            fill_form(page)
            shot(page, "06_form_filled")

            print("[6] กดยืนยันการจอง", flush=True)
            page.click('button[type="submit"]')
            page.wait_for_url("**/booking/success/**", timeout=30000)
            shot(page, "07_booking_success")
            print("   *** สร้างการจองจริงแล้ว — ต้องยกเลิกก่อนจบสคริปต์ ***", flush=True)

            print("[7] การจองของฉัน", flush=True)
            page.goto(f"{BASE}/", wait_until="domcontentloaded")
            page.wait_for_selector(".my-booking-card", timeout=30000)

            booking_id = find_our_booking(page)
            if not booking_id:
                raise RuntimeError("หาการจองของสคริปต์ในรายการไม่เจอ")
            print("   booking id =", booking_id, flush=True)

            hide_stale_test_cards(page, booking_id)
            shot(page, "08_my_bookings")      # ไม่เต็มหน้า — ต้องการเห็นเฉพาะส่วนการจองของฉัน

            print("[8] รายละเอียดการจอง", flush=True)
            page.click(f"#bk-{booking_id}")
            shot(page, "09_booking_detail")
            page.evaluate("() => closeSheet()")

            print("[9] ฟอร์มจอง ChatGPT (แคปอย่างเดียว ไม่จอง)", flush=True)
            if open_booking_form(page, ROOM_ALSO):
                shot(page, "10_booking_form_chatgpt")
            else:
                print("!! เปิดฟอร์ม chat-gpt ไม่สำเร็จ ข้ามภาพนี้", flush=True)

        finally:
            # ยกเลิกให้เสมอ แม้ขั้นตอนหลังจากจองจะพัง — ไม่งั้นทิ้งการจองค้างบน production
            if booking_id:
                print("[10] ยกเลิกการจองทดสอบ", flush=True)
                page.goto(f"{BASE}/", wait_until="domcontentloaded")
                try:
                    # ต้องรอให้รายการโหลดเสร็จก่อน ไม่งั้นยังไม่มีการ์ดให้ซ่อน
                    page.wait_for_selector(f"#bk-{booking_id}", timeout=30000)
                    wait_bookings(page)
                    hide_stale_test_cards(page, booking_id)
                    cancel_booking(page, booking_id)
                    shot(page, "11_cancelled")
                    print("   ยกเลิกเรียบร้อย", flush=True)
                except Exception as exc:
                    print(f"!! ยกเลิกอัตโนมัติไม่สำเร็จ ({exc})", flush=True)
                    print(f"!! กรุณายกเลิกการจอง id={booking_id} เองที่ {BASE}/manage/bookings/",
                          flush=True)
            ctx.close()

    print("\nเสร็จแล้ว — ภาพอยู่ที่ doc/screenshots/vmflow/", flush=True)
    print("ต่อด้วย: python doc/make_vm_booking_guide_docx.py", flush=True)


if __name__ == "__main__":
    main()
