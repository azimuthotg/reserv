# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

<!-- Codex edit: synchronized with the current implementation on 2026-06-02.
Reference: doc/progress-2026-06-02.md -->

---

## ภาพรวมโครงการ

ระบบจองพื้นที่บริการ Smart Creative Learning Space — สำนักวิทยบริการ มหาวิทยาลัยนครพนม
Migration จาก Google Apps Script + Google Sheets → Django + MySQL

ผู้ใช้จองได้ **2 ช่องทาง:**
- **LINE OA:** กด "จองห้อง" ใน Rich Menu → LIFF เปิด `/booking/?room=X` → กรอกฟอร์มจอง
- **เว็บไซต์:** เปิด `https://lib.npu.ac.th/reserv/` ผ่าน browser → LINE Login → กรอกฟอร์มจอง

**การจองห้องทุกช่องทาง** ยืนยันตัวตนผ่าน LINE LIFF และ `api.npu.ac.th` — จองผ่านทางอื่นไม่ได้
Django session login ใช้กับ Staff Portal (`/manage/`) เท่านั้น
**ข้อยกเว้นที่ไม่ใช่การจอง:** `/card-login/` ให้นักศึกษา/บุคลากรล็อกอิน **AD บนเว็บโดยไม่ต้องผ่าน LINE**
เพื่อขอ QR เข้าประตูอย่างเดียว (จองห้องไม่ได้) — ใช้ signed cookie ของตัวเอง ไม่ใช่ Django session

**เวลาให้บริการสำหรับประชาสัมพันธ์:**
- จันทร์ – ศุกร์: `08:30 – 16:30 น.`
- เสาร์ – อาทิตย์: `09:00 – 17:00 น.`
- ปิดเฉพาะวันหยุดนักขัตฤกษ์ โดยแจ้งล่วงหน้า

**บริการเครื่องเสมือน (VM) — ไม่ต้องเข้าอาคาร:** ปัจจุบัน 3 บริการ ทุกตัวจองได้ `00:00 – 23:59`
ทุกวันรวมวันหยุด ใช้ผ่านเว็บล้วน **ไม่มีเครื่องจริงให้นั่งที่ชั้น 1 แล้ว**
- **Canva Pro 1 / Canva Pro 2** = VM คนละตัว **บัญชี Canva แยกกัน**
- **ChatGPT** = VM 1 ตัว บัญชี ChatGPT 1 บัญชี (เปิดกลับ 2026-08-09 บนเครื่องเดิมของ Netflix)

> **`netflix1_vm` (Netflix Pro) ปิดแล้ว `is_active=0` ตั้งแต่ 2026-08-09** — สำนักฯ เปลี่ยนบริการ
> บนเครื่องเสมือนตัวนั้นไปเป็น ChatGPT (ใบแจ้งทีม VM 9 ส.ค.) เก็บห้องและประวัติ 20 รายการไว้
> **Netflix ที่ Edutainment Zone ชั้น 3 ยังให้บริการตามปกติ — คนละเรื่องกับ VM ตัวนี้**

แบ่งเป็น 3 รอบ (เช้ามืด/กลางวัน/กลางคืน) จองได้รอบละ 1 ครั้ง — ดู Overlap / รอบบริการ ด้านล่าง

---

## Tech Stack

| ส่วน | เทคโนโลยี |
|---|---|
| Backend | Django 4.2 + Python 3.12 |
| Database | MySQL 8.0 (host: ดูใน .env, db: reserv_db) |
| Frontend | Django Template + Bootstrap 5.3 + FullCalendar v6 |
| LIFF | LINE Front-end Framework v2 (SDK 2.15+) |
| Process Manager | NSSM + Waitress (Windows Server) |
| Reverse Proxy | IIS + ARR → https://lib.npu.ac.th/reserv/ (static ผ่าน WhiteNoise) |

---

## Commands

```bash
# Development
python3 manage.py runserver 0.0.0.0:8001

# Database
python3 manage.py migrate
python3 manage.py createsuperuser

# Checks
python3 manage.py check
python3 manage.py makemigrations booking

# Production (Windows)
python deploy/waitress_serve.py      # อ่าน WAITRESS_HOST/PORT/THREADS จาก .env
```

---

## สถาปัตยกรรม

```
LINE OA → LIFF (https://lib.npu.ac.th/reserv/booking/?room=mini)
               ↓
          Django views.py
               ↓
    ┌──────────┴──────────┐
    │                     │
api.npu.ac.th         MySQL reserv_db
(auth + profiles)     (bookings, rooms)
```

**Sub-path deployment:** Django deploy ที่ `/reserv/` บน reverse proxy ต้องกำหนด `.env` เป็น
`FORCE_SCRIPT_NAME=/reserv` และ `STATIC_URL=/reserv/static/`

---

## URL Structure

| URL (dev) | URL (prod) | View |
|---|---|---|
| `/` | `/reserv/` | หน้าแรก เลือกห้อง + การจองของฉัน (LIFF) |
| `/register/` | `/reserv/register/` | ผูกบัญชี LINE + LDAP |
| `/booking/?room=X` | `/reserv/booking/?room=X` | form จอง (LIFF) |
| `/booking/success/` | `/reserv/booking/success/` | จองสำเร็จ |
| `/calendar/` | `/reserv/calendar/` | FullCalendar แบบ public ไม่ต้อง login |
| `/external/` | `/reserv/external/` | บุคคลภายนอกขอ QR **รายวัน** (public) — เรียก `/v2/external/issue/` ผ่าน JWT · บังคับแค่ชื่อ-สกุล เลขบัตรไม่บังคับ |
| `/external/permanent/` | `/reserv/external/permanent/` | บุคคลภายนอกสมัคร **สมาชิกถาวร** (public) — **บังคับเลขบัตร 13 หลัก** ต่างจากหน้ารายวัน · รอ staff อนุมัติที่ `/manage/external/` |
| `/room/<booking_name>/` | `/reserv/room/<booking_name>/` | รายละเอียดห้องแบบ public |
| `/card/` | `/reserv/card/` | Virtual Card + Walai status (LIFF) |
| `/card-login/` | `/reserv/card-login/` | **นักศึกษา/บุคลากรล็อกอิน AD บนเว็บ → QR เข้าประตู โดยไม่ต้องผ่าน LINE** (public) · จองห้องไม่ได้ · "จดจำ 90 วัน" ใช้ signed cookie แยกจาก Django session · rate limit ต่อบัญชี (ห้ามต่อ IP — ผู้ใช้อยู่หลัง NAT) |
| `/room-control/` | `/reserv/room-control/` | ควบคุมอุปกรณ์ IoT ระหว่างเวลาจอง (LIFF) |
| `/api/access-status/` | `/reserv/api/access-status/` | ตรวจสถานะ local user ก่อนใช้ frontend cache |
| `/api/check-user/` | `/reserv/api/check-user/` | ตรวจการผูก LINE userId |
| `/api/my-bookings/` | `/reserv/api/my-bookings/` | รายการจองของผู้ใช้ |
| `/api/checkin/` | `/reserv/api/checkin/` | Check-in ก่อน/หลังเวลาเริ่มไม่เกิน 15 นาที |
| `/api/calendar-events/` | `/reserv/api/calendar-events/` | JSON events |
| `/manage/` | `/reserv/manage/` | Staff Portal ใช้ Django session login |
| `/manage/external/` | `/reserv/manage/external/` | staff จัดการสมาชิกถาวร — `register/` · `<citizen_id>/` · `/edit/` · `/approve/` · `/revoke/` · `/delete/` · `/photo/` · **ทุกเส้นทาง proxy ไป api v2 — reserv ไม่เก็บข้อมูลสมาชิกเอง** (หน้า staff เว้นเลขบัตรได้ รองรับ VVIP api gen `V`+12 หลักให้) |
| `/admin/` | `/reserv/admin/` | Django Admin |
| `/health/` | `/reserv/health/` | Health check (NMS monitoring) — public, JSON `{status, db, db_ms}`, 200/503 |

room keys: `mini`, `edutainment`, `canva`, `canva2`, `meeting_f1`, `chat-gpt`
(`netflix1_vm` ปิดแล้ว `is_active=0` ตั้งแต่ 2026-08-09 — เก็บประวัติ 20 รายการ ·
`chat-gpt` เคยปิด 2026-08-08 แล้ว **เปิดกลับ 2026-08-09** เป็นบริการ VM 24 ชม.)

---

## Auth Flow

```
เปิดหน้า / หรือ /booking/?room=X จาก LINE OA หรือ browser
    ↓
JavaScript เรียก liff.init()
    ↓
liff.isLoggedIn() ?
    ├── ไม่ → liff.login({ redirectUri: window.location.href })
    └── ใช่ → liff.getProfile() เพื่อรับ LINE userId
                 ↓
          POST /api/access-status/
                 ↓
          local LineUser ถูกปิดใช้หรือไม่?
              ├── ใช่ → แจ้งให้ติดต่อเจ้าหน้าที่
              └── ไม่ → อ่าน profile cache ของ LINE userId ปัจจุบัน
                         หากไม่มี cache จึง POST /api/check-user/
                                 ↓
          POST /api/check-user/
                 ↓
          api.npu.ac.th/api/{userId}/ พบการผูกบัญชีหรือไม่?
              ├── พบ → cache profile ใน sessionStorage → เข้าใช้งาน
              └── ไม่พบ → redirect /register/?userId=...&page=...
                              ↓
                       เลือกประเภทผู้ใช้ + กรอก LDAP/password
                              ↓
                       ตรวจ LDAP → ผูกบัญชี LINE ครั้งแรก → redirect กลับ
```

**สำคัญ:** LIFF ต้องการ HTTPS เท่านั้น — ทดสอบ LINE login ไม่ได้ใน localhost ต้อง deploy ขึ้น `lib.npu.ac.th` ก่อน

**ประเภทผู้ใช้ในระบบ:** นักศึกษาเลือก `"นักศึกษา"` ส่วนอาจารย์และบุคลากรเลือก `"บุคลากรภายในมหาวิทยาลัย"`

**หมายเหตุ:** ไม่มี endpoint `/api/set-session/` ใน implementation ปัจจุบัน

**Registration guard:** หลัง LDAP ผ่าน ต้องตรวจผล `_register_npu_user()` ก่อนสร้าง `LineUser` ใน local DB
หาก NPU API ผูกบัญชีไม่สำเร็จ ให้คงอยู่หน้าลงทะเบียนและแจ้งผู้ใช้ลองใหม่ ห้ามสร้าง local user ต่อ

**Booking guard:** `create_booking()` ต้องปฏิเสธการสร้าง booking เมื่อ `LineUser.is_active=False`
และแจ้งให้ผู้ใช้ติดต่อเจ้าหน้าที่

**Inactive user guard:** API ที่ต้องใช้สิทธิ์ผู้ใช้ต้องเรียก `_get_active_line_user()`
เพื่อปฏิเสธ `LineUser.is_active=False` ครอบคลุม booking, my-bookings, cancel, check-in,
Walai card และ IoT room control ส่วน `check_user()` ตรวจสถานะก่อน refresh profile
หน้า LIFF ต้องเรียก `/api/access-status/` ก่อนอ่าน frontend cache เพื่อให้การระงับมีผลทันที

**Frontend profile cache:** หน้า landing, booking และ card ใช้ `sessionStorage`
key รูปแบบ `npu_user_v2:<LINE userId>` เพื่อไม่ให้ profile ค้างข้ามบัญชีเมื่อสลับ LINE user

**Service hours policy:** `Room.open_time` และ `Room.close_time` เป็นเวลาเปิด-ปิดวันจันทร์-ศุกร์
ส่วนเสาร์-อาทิตย์ใช้ `09:00–17:00` จาก `booking/service_hours.py`
ทุก booking ต้องตรวจช่วงเวลาอีกครั้งฝั่ง backend ด้วย `room_service_hours()`

**บริการออนไลน์ (`Room.is_online`):** ห้องที่เป็นเครื่องเสมือน (`canva`, `canva2`, `chat-gpt`)
เข้าใช้แบบ RDP ไปที่เครื่องแม่ที่เปิด 24 ชม. **ไม่ต้องเข้าอาคาร ไม่มีอุปกรณ์ IoT ผูกอยู่**
- ใช้ `open_time`/`close_time` ของห้องเองทุกวัน **ไม่ถูกตัดด้วยเวลาเปิดอาคารหรือเวลาเสาร์-อาทิตย์**
  ปัจจุบันตั้งไว้ `00:00–23:59`
- **จองวันหยุดนักขัตฤกษ์ได้** (`HolidayDate` ไม่บล็อก) และ date picker ไม่ปิดวันหยุดให้ห้องกลุ่มนี้

**`Room.day_round_enabled`:** ปิดรอบกลางวันของห้องนั้นได้ ใช้เมื่อทรัพยากรถูกใช้ที่จุดบริการอื่น
ในเวลาราชการ — **ตอนนี้ไม่มีห้องไหนตั้งเป็น `False` แล้ว** (เคยใช้กับ `netflix1_vm` เพราะบัญชี Netflix
บัญชีเดียวถูกใช้ที่ Edutainment Zone ช่วงกลางวัน · ห้องนั้นปิดไปแล้ว 2026-08-09)
ฟีเจอร์ยังอยู่ในระบบพร้อมใช้ ติ๊กผ่าน `/manage/rooms/` (ห้าม hardcode booking_name ใน code)

**รอบบริการ (booking rounds):** แบ่ง 3 รอบต่อวันใน `service_hours.py` — **1 สิทธิ์ต่อห้อง ต่อรอบ**
| รอบ | เวลา |
|---|---|
| `early` เช้ามืด | `00:00–08:30` |
| `day` กลางวัน | `08:30–17:00` |
| `night` กลางคืน | `17:00–23:59` |
- **ห้องจริงพฤติกรรมไม่เปลี่ยน** เพราะเปิดเฉพาะช่วงกลางวัน การจองจึงตกอยู่ในรอบ `day` เสมอ
- **จองคร่อมรอบไม่ได้** (เช่น 16:00–18:30) เพราะนับสิทธิ์ไม่ได้ — ตรวจด้วย `round_of_range()`
- ขอบรอบเป็นของรอบก่อนหน้า: `06:00–08:30` = เช้ามืด · `08:30–10:00` = กลางวัน
- โควตานับด้วย `round_start_filter()` (กรองจาก `start_time`) แทน guard เดิมที่นับทั้งวัน
- นโยบายจากผู้ใช้ 2026-08-08: นอกเวลาถือเป็นสิทธิ์คนละรอบกับกลางวัน (ดู MEM.md)

**Overlap policy:** ผู้ใช้คนเดียว **ห้ามมีการจองที่ช่วงเวลาทับซ้อนกันข้ามห้อง ในวันเดียวกัน**
(คนเดียวอยู่สองที่ไม่ได้ ห้องที่เหลือจะถูกล็อกทิ้ง) ตรวจใน `create_booking()`
ภายใน `transaction.atomic()` เดียวกับ conflict check โดยใช้ `select_for_update()`
- ใช้เงื่อนไข "ทับจริง" (`start < other_end AND other_start < end`) — ต่อกันพอดีเช่น 10:00-11:00 กับ 11:00-12:00 **จองได้**
- ห้องที่ `Room.allow_overlap=True` ยกเว้น **ทั้งขาใหม่และขาเดิม** (พื้นที่กลุ่ม/พื้นที่เปิด)
  ปัจจุบันติ๊กไว้เฉพาะ `meeting_f1` — **ห้าม hardcode booking_name ใน code** เปลี่ยนผ่าน `/manage/rooms/`
- กติกา "จองได้ห้องละ 1 ครั้งต่อวัน" เดิมยังอยู่ — 2 กติกานี้ทำงานคนละหน้าที่
- ขอตามใบแจ้งทีม LRS ARC VM Gateway 2026-08-08 (ดู MEM.md)

**Advance booking policy:** จองล่วงหน้าได้ไม่เกิน `7` วันเปิดบริการ โดยข้าม `HolidayDate`
ที่ active รวมถึงเสาร์-อาทิตย์ที่สำนักประกาศปิดผ่านรายการวันหยุด
backend ใช้ `MAX_ADVANCE_DAYS` และ `max_advance_service_date()` เป็นค่ากลาง
แล้วส่ง `max_booking_date` ให้ date picker โดยตรง ส่วน `RoomClosure` ไม่หักจากโควตาของทั้งสำนัก

**วันหยุดอัตโนมัติ (`HolidayDate.source`):** `sync_holidays` ดึงปฏิทินวันหยุดไทยจาก Google Calendar
(`booking/holiday_feed.py` — iCal สาธารณะ ไม่ต้องใช้ key) เข้ามาเป็น **ฉบับร่าง `is_active=False`
พร้อม `source='auto'` เสมอ** เจ้าหน้าที่ต้องกดเปิดใช้เองที่ `/manage/holidays/` จึงจะบล็อกการจอง
- **ห้ามให้ระบบเปิดใช้เอง** — ฟีดผิดได้ 2 ทาง มีวันที่ไม่ใช่วันหยุดราชการปนมา (วาเลนไทน์ ตรุษจีน
  คริสต์มาส — กรองด้วย `OBSERVANCE_KEYWORDS` แต่ไม่หมด) และขาดวันหยุดราชการบางวัน (เข้าพรรษา 2569)
  อีกทั้งวันหยุดของสำนักฯ (ปิดเทอม ซ้อมรับปริญญา ไฟดับ) ไม่มีในปฏิทินใด ๆ ต้องเพิ่มมือเหมือนเดิม
- sync **ไม่แตะแถว `source='manual'`** แม้วันตรงกัน — กันคำอธิบาย/สถานะที่คนตั้งไว้ถูกเขียนทับ
- แดชบอร์ด `/manage/` ขึ้นแถบแดงเมื่อมีฉบับร่างใน 30 วันข้างหน้า พร้อมจำนวนการจองที่ตกวันนั้น

**เตือนข้อมูลวันหยุดค้าง (`HolidaySyncRun`):** แถบแดงข้างบนขึ้นได้เฉพาะเมื่อ **มีแถวฉบับร่างอยู่จริง**
แดชบอร์ดที่เงียบเพราะตรวจครบ จึงแยกไม่ออกจากที่เงียบเพราะไม่มีใครกดดึงมาหลายเดือน
`HolidaySyncRun` บันทึกทุกครั้งที่ดึงสำเร็จ **แม้รอบนั้นไม่มีวันใหม่เลย** แล้ว `data_status()`
สรุปให้แดชบอร์ดและ `/manage/holidays/` ใช้ร่วมกัน — ขึ้นแถบเหลืองเมื่อ
`is_stale` (ไม่ได้ดึงเกิน `HOLIDAY_SYNC_STALE_DAYS`=45 วัน) หรือ
`horizon_short` (วันหยุดล่าสุดในตารางอยู่ใกล้กว่า `HOLIDAY_HORIZON_MIN_DAYS`=60 วัน)
- **ห้ามใช้วันที่สร้างของ `HolidayDate` แทน** — sync ที่รันตรงเวลาแต่ไม่เจอวันใหม่จะดูเหมือนไม่เคยรัน
- fetch ล้มเหลวต้อง **ไม่** บันทึก `HolidaySyncRun` และ `--dry-run` ก็ไม่บันทึก

---

## NPU API (https://api.npu.ac.th)

helper ปัจจุบันอยู่ใน `booking/views.py` และเรียก `api.npu.ac.th` โดยตรง

| Function | Endpoint | ใช้ทำอะไร |
|---|---|---|
| `_fetch_npu_user(line_user_id)` | GET `/api/{id}/` | เช็คว่าผูกบัญชีแล้วไหม |
| `_register_npu_user(...)` | POST `/api/` | ผูกบัญชีใหม่ |
| `_fetch_npu_profile(user_ldap, user_type)` | GET `/std-info/{id}/` หรือ `/staff-info/{id}/` | ดึงชื่อ-คณะ |
| `_verify_ldap(username, password)` | POST `/auth-ldap/auth_ldap/` | ตรวจ AD credentials |
| `walai_card(request)` | GET `/walai/check_user_walai/{id}/` | เช็คสมาชิก Walai สำหรับ Virtual Card |

`user_type` ต้องเป็น **ภาษาไทยเป๊ะ**: `"นักศึกษา"` หรือ `"บุคลากรภายในมหาวิทยาลัย"`

---

## Models

- **Room** — ห้องบริการ, `booking_name` เป็น unique key ใช้ใน URL · `allow_overlap` = ยอมให้คนเดียวจองทับเวลากับห้องอื่นได้ (ดู Overlap policy)
- **LineUser** — cache ผู้ใช้ที่ผูก LINE กับ LDAP แล้ว (source of truth อยู่ที่ api.npu.ac.th)
- **Booking** — การจอง, status: `confirmed` / `cancelled`
- **RoomDevice** — อุปกรณ์ Home Assistant `room` ว่างได้ = อุปกรณ์ส่วนกลางที่ไม่สังกัดห้องจอง (จับกลุ่มด้วย `group_name`)
- **RoomClosure** — ปิดห้องชั่วคราวตามวันและช่วงเวลา
- **HolidayDate** — วันหยุดที่ไม่เปิดให้จอง
- **HolidaySyncRun** — ประวัติการดึงปฏิทินวันหยุด (อ่านอย่างเดียว) ใช้ตอบว่า "ข้อมูลวันหยุดเก่าแค่ไหน"
- **BookingLog** — audit trail เช่น `created`, `cancelled`, `checked_in`, `auto_cancelled`, `auto_off`

**Conflict check** ต้องใช้ `select_for_update()` เสมอ — ดู `create_booking()` ใน `booking/views.py`

---

## Settings สำคัญ

```python
FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME', '')
STATIC_URL = os.getenv('STATIC_URL', 'static/')
USE_X_FORWARDED_HOST = True            # อยู่หลัง nginx
TIME_ZONE = 'Asia/Bangkok'
```

production ต้องกำหนด `FORCE_SCRIPT_NAME=/reserv` และ `STATIC_URL=/reserv/static/` ใน `.env`

ทุก secret อยู่ใน `.env` อ่านด้วย `python-dotenv`:
`SECRET_KEY`, `DB_*`, `LINE_*`, `HA_ACCESS_SECRET`

---

## Phases

| Phase | สถานะ | เนื้อหา |
|---|---|---|
| **Phase 1** | ✅ มีในระบบใช้งานจริง | Register, Booking, Calendar, Admin |
| **Phase 2** | ✅ มีใน codebase | Check-in, IoT Room Control, reminder, auto-off, auto-cancel |
| **Phase 3** | ✅ มีใน codebase | Virtual Card + Walai status + QR Code |
| **Phase 4** | ✅ มีใน codebase | Staff Portal, IoT Monitor, LINE message และ broadcast |

**IoT flow ปัจจุบัน:** Django เรียก Home Assistant โดยตรงผ่าน `HA_IP`, `HA_PORT`, `HA_TOKEN`
และตรวจสิทธิ์จาก booking ที่ active ก่อนควบคุมอุปกรณ์ ดู `room_status()` และ `device_toggle()` ใน `booking/views.py`

**อุปกรณ์ส่วนกลาง (RoomDevice ที่ `room=None`):** อุปกรณ์ที่ไม่สังกัดห้องจอง เช่น flip gate ทางเข้า
จับกลุ่มด้วย `group_name` แสดงเป็นการ์ดแยกบนหน้า `/manage/iot-monitor/` ให้ staff กดเปิด-ปิดได้
**ไม่ปรากฏในระบบจองใด ๆ** เพราะ `room_status()`, `device_toggle()` และ auto-off ใน `send_reminders`
filter ด้วย `room=booking.room` ที่เป็นห้องจริงเสมอ อุปกรณ์กลุ่มจึงไม่เข้าเงื่อนไข
ตารางเวลาของอุปกรณ์กลุ่ม**ให้ Home Assistant automation คุมทั้งหมด** ฝั่ง Django ไม่มี logic เรื่องเวลา
(flip gate: HA เปิด 07:20 ปิด 17:00 ต่างจากห้องจองที่ automation `Close ALL` ปิด 16:30)
หน้า monitor + refresh + แจ้งกลุ่ม LINE + `morning_iot_report` ใช้ helper กลางตัวเดียวคือ
`_iot_cards()` ใน `booking/manage_views.py` — เพิ่ม/แก้การจัดกลุ่มให้แก้ที่นี่ที่เดียว
เพิ่ม-ลบอุปกรณ์กลุ่มผ่าน Django Admin (`/admin/`) เพราะไม่มีหน้าห้องให้จัดการ

**หมายเหตุ:** ตาราง Phase ด้านบนสรุปจาก codebase ณ วันที่ sync เอกสาร ควรตรวจ production deployment แยกต่างหากก่อนประกาศฟีเจอร์ใหม่

---

## Deploy (Windows Server)

```bash
# ⚠️ production มี venv — ห้ามเรียก `python` / `pip` เปล่า ๆ (จะได้ ImportError: Couldn't import Django)

# 1. ติดตั้ง dependencies
.\venv\Scripts\pip.exe install -r requirements.txt

# 2. Database
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser

# 3. Static files
.\venv\Scripts\python.exe manage.py collectstatic --noinput

# 4. NSSM service (production จริงอยู่ที่ C:\project\reserv — ไม่ใช่ C:\projects\)
c:\nssm\nssm.exe install Reserv "C:\project\reserv\venv\Scripts\python.exe" "C:\project\reserv\deploy\waitress_serve.py"
c:\nssm\nssm.exe set Reserv AppDirectory "C:\project\reserv"
c:\nssm\nssm.exe start Reserv
```

**เมื่อ pull code ใหม่ขึ้น production:** หากมีการแก้ Python code ต้อง restart service
ก่อนทดสอบ เพื่อให้ Waitress โหลด code ชุดใหม่ — ถ้าแก้แต่ข้อมูล/static ไม่ต้อง restart

```powershell
cd C:\project\reserv
git pull origin master
.\venv\Scripts\python.exe manage.py collectstatic --noinput
c:\nssm\nssm.exe restart Reserv
```

> **ชื่อ NSSM service คือ `Reserv`** (ยืนยันบนเซิร์ฟเวอร์ 2026-08-08 — เอกสารเก่าที่เขียน `reserv-booking` ผิด)

**Reverse proxy คือ IIS + ARR ไม่ใช่ Nginx** — `web.config` rewrite `^reserv/(.*)` → `127.0.0.1:8003`
static ทั้งหมด serve ด้วย **WhiteNoise** ผ่าน Waitress **ห้ามตั้ง rule แยกให้ `/reserv/static/`**
(เคยทำแล้ว admin CSS หาย — ดู [doc/deploy_guide.md](doc/deploy_guide.md))

---

## LINE LIFF

- LIFF ID: `1653777241-BP070q31`
- Endpoint URL ที่ต้องตั้งใน LINE Developers Console: `https://lib.npu.ac.th/reserv/`
- LIFF ต้องการ HTTPS — ทดสอบใน localhost ไม่ได้ (ดู Capture.PNG)
- Handle ทั้ง 2 กรณี: เปิดใน LINE app (ได้ userId ทันที) และ browser ปกติ (ต้อง `liff.login()`)

---

## AI Collaboration Workflow

`AGENTS.md` และ `CLAUDE.md` เป็นเอกสารคู่สำหรับส่งต่องานระหว่าง Codex และ Claude Code
ต้องรักษาข้อมูลเชิงระบบให้ตรงกันเสมอ โดยต่างกันได้เฉพาะข้อความแนะนำเครื่องมือในส่วนต้นไฟล์

เมื่อพัฒนาหรือแก้ไขระบบ:
1. อ่าน `AGENTS.md` หรือ `CLAUDE.md` และ progress log ล่าสุดก่อนเริ่มงาน
2. ตรวจ implementation จริงก่อนแก้เอกสาร ห้ามอ้างอิง flow จากเอกสารเก่าเพียงอย่างเดียว
3. หาก behavior, architecture, URL, auth flow, deployment หรือสถานะ feature เปลี่ยน ให้ sync ทั้ง `AGENTS.md` และ `CLAUDE.md`
4. สร้างหรืออัปเดต `doc/progress-YYYY-MM-DD.md` เพื่อบันทึกสิ่งที่แก้ ไฟล์ที่เกี่ยวข้อง วิธีตรวจสอบ และงานค้าง
5. ใส่หมายเหตุใน progress log ว่าแก้โดยเครื่องมือใด เช่น `Codex edit` หรือ `Claude Code edit`
6. ก่อนส่งต่องาน ให้ตรวจ diff และระบุว่าได้รัน check/test อะไรแล้ว
7. เมื่อ deploy Python code ขึ้น production ให้ restart service ก่อนทดสอบ และบันทึกผล production test ใน progress log

Progress log สำหรับการ sync ครั้งนี้: `doc/progress-2026-06-02.md`
