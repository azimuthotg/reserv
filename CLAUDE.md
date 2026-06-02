# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- Codex edit: synchronized with the current implementation on 2026-06-02.
Reference: doc/progress-2026-06-02.md -->

---

## ภาพรวมโครงการ

ระบบจองพื้นที่บริการ Smart Creative Learning Space — สำนักวิทยบริการ มหาวิทยาลัยนครพนม
Migration จาก Google Apps Script + Google Sheets → Django + MySQL

ผู้ใช้จองได้ **2 ช่องทาง:**
- **LINE OA:** กด "จองห้อง" ใน Rich Menu → LIFF เปิด `/booking/?room=X` → กรอกฟอร์มจอง
- **เว็บไซต์:** เปิด `https://lib.npu.ac.th/reserv/` ผ่าน browser → LINE Login → กรอกฟอร์มจอง

ผู้ใช้ทั่วไป **ทุกช่องทาง** ยืนยันตัวตนผ่าน LINE LIFF และ `api.npu.ac.th`
ไม่มี session login แยกสำหรับผู้ใช้ทั่วไปบนเว็บไซต์ ส่วน Django session login ใช้เฉพาะ Staff Portal (`/manage/`)

**เวลาให้บริการสำหรับประชาสัมพันธ์:**
- จันทร์ – ศุกร์: `08:30 – 16:30 น.`
- เสาร์ – อาทิตย์: `09:00 – 17:00 น.`
- ปิดเฉพาะวันหยุดนักขัตฤกษ์ โดยแจ้งล่วงหน้า

**ข้อจำกัดปัจจุบัน:** `Room.open_time` และ `Room.close_time` เก็บเวลาเดียวทุกวัน
ฟอร์มจองจึงยังไม่รองรับเวลาแยกวันธรรมดา/วันหยุดสุดสัปดาห์ ต้องแก้ code แยกก่อนเปิด slot เสาร์ – อาทิตย์ถึง `17:00 น.`

---

## Tech Stack

| ส่วน | เทคโนโลยี |
|---|---|
| Backend | Django 4.2 + Python 3.12 |
| Database | MySQL 8.0 (host: ดูใน .env, db: reserv_db) |
| Frontend | Django Template + Bootstrap 5.3 + FullCalendar v6 |
| LIFF | LINE Front-end Framework v2 (SDK 2.15+) |
| Process Manager | NSSM + Waitress (Windows Server) |
| Reverse Proxy | Nginx → https://lib.npu.ac.th/reserv/ |

---

## Commands

```bash
# Development
python3 manage.py runserver 0.0.0.0:8001

# Database
python3 manage.py migrate
python3 manage.py load_rooms        # โหลดข้อมูล 5 ห้องเริ่มต้น
python3 manage.py createsuperuser

# Checks
python3 manage.py check
python3 manage.py makemigrations booking

# Production (Windows)
python -m waitress --port=8000 --threads=4 reserv.wsgi:application
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
| `/room/<booking_name>/` | `/reserv/room/<booking_name>/` | รายละเอียดห้องแบบ public |
| `/card/` | `/reserv/card/` | Virtual Card + Walai status (LIFF) |
| `/room-control/` | `/reserv/room-control/` | ควบคุมอุปกรณ์ IoT ระหว่างเวลาจอง (LIFF) |
| `/api/access-status/` | `/reserv/api/access-status/` | ตรวจสถานะ local user ก่อนใช้ frontend cache |
| `/api/check-user/` | `/reserv/api/check-user/` | ตรวจการผูก LINE userId |
| `/api/my-bookings/` | `/reserv/api/my-bookings/` | รายการจองของผู้ใช้ |
| `/api/checkin/` | `/reserv/api/checkin/` | Check-in ก่อน/หลังเวลาเริ่มไม่เกิน 15 นาที |
| `/api/calendar-events/` | `/reserv/api/calendar-events/` | JSON events |
| `/manage/` | `/reserv/manage/` | Staff Portal ใช้ Django session login |
| `/admin/` | `/reserv/admin/` | Django Admin |

room keys: `mini`, `edutainment`, `canva`, `chat-gpt`, `meeting_f1`

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

**Advance booking policy:** จองล่วงหน้าได้ไม่เกิน `7` วัน นับทุกวัน
โดยใช้ `MAX_ADVANCE_DAYS` ใน `booking/views.py` เป็นค่ากลางร่วมกับ date picker

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

- **Room** — ห้องบริการ, `booking_name` เป็น unique key ใช้ใน URL
- **LineUser** — cache ผู้ใช้ที่ผูก LINE กับ LDAP แล้ว (source of truth อยู่ที่ api.npu.ac.th)
- **Booking** — การจอง, status: `confirmed` / `cancelled`
- **RoomDevice** — อุปกรณ์ Home Assistant ของแต่ละห้อง
- **RoomClosure** — ปิดห้องชั่วคราวตามวันและช่วงเวลา
- **HolidayDate** — วันหยุดที่ไม่เปิดให้จอง
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

**หมายเหตุ:** ตาราง Phase ด้านบนสรุปจาก codebase ณ วันที่ sync เอกสาร ควรตรวจ production deployment แยกต่างหากก่อนประกาศฟีเจอร์ใหม่

---

## Deploy (Windows Server)

```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt

# 2. Database
python manage.py migrate
python manage.py load_rooms
python manage.py createsuperuser

# 3. Static files
python manage.py collectstatic

# 4. NSSM service
nssm install reserv-booking "python" "-m waitress --port=8000 --threads=4 reserv.wsgi:application"
nssm set reserv-booking AppDirectory "C:\path\to\reserv"
nssm start reserv-booking
```

**เมื่อ pull code ใหม่ขึ้น production:** หากมีการแก้ Python code ต้องรัน
`nssm restart reserv-booking` ก่อนทดสอบ เพื่อให้ Waitress โหลด code ชุดใหม่

**Nginx config สำคัญ:**
```nginx
location /reserv/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header Host $host;
}
```

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
