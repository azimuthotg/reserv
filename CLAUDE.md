# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ภาพรวมโครงการ

ระบบจองพื้นที่บริการ Smart Creative Learning Space — สำนักวิทยบริการ มหาวิทยาลัยนครพนม
Migration จาก Google Apps Script + Google Sheets → Django + MySQL

ผู้ใช้กด "จองเลย" ใน LINE OA → LIFF เปิด `/booking/?room=X` → Django ตรวจสิทธิ์ผ่าน LINE userId + api.npu.ac.th → กรอกฟอร์มจอง

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

**Sub-path deployment:** Django deploy ที่ `/reserv/` บน nginx ต้องใช้ `FORCE_SCRIPT_NAME = '/reserv'` ใน settings และ static URL เป็น `/reserv/static/`

---

## URL Structure

| URL (dev) | URL (prod) | View |
|---|---|---|
| `/register/` | `/reserv/register/` | ผูกบัญชี LINE + LDAP |
| `/booking/?room=X` | `/reserv/booking/?room=X` | form จอง (LIFF) |
| `/booking/success/` | `/reserv/booking/success/` | จองสำเร็จ |
| `/calendar/` | `/reserv/calendar/` | FullCalendar |
| `/api/calendar-events/` | `/reserv/api/calendar-events/` | JSON events |
| `/api/set-session/` | `/reserv/api/set-session/` | LIFF → session (POST) |
| `/admin/` | `/reserv/admin/` | Django Admin |

room keys: `mini`, `netflix`, `canva`, `chat-gpt`, `meeting_f1`

---

## Auth Flow

```
เปิดหน้า /booking/?room=X
    ↓
session['line_user_id'] มีไหม?
    ├── มี → หา LineUser ใน DB
    │         ├── เจอ → แสดง form จอง
    │         └── ไม่เจอ → เรียก api.npu.ac.th/api/{id}/ → cache → form
    └── ไม่มี → redirect /register/?next=/booking/?room=X

LIFF ส่ง userId มา 2 วิธี:
  1. POST /api/set-session/ (หลัง liff.init() ใน JS)
  2. hidden field ใน register form
```

**สำคัญ:** LIFF ต้องการ HTTPS เท่านั้น — ทดสอบ LINE login ไม่ได้ใน localhost ต้อง deploy ขึ้น `lib.npu.ac.th` ก่อน

---

## NPU API (https://api.npu.ac.th)

ทุก endpoint ไม่ต้องใช้ JWT ทั้งหมดอยู่ใน `booking/utils.py`

| Function | Endpoint | ใช้ทำอะไร |
|---|---|---|
| `get_npu_user(line_user_id)` | GET `/api/{id}/` | เช็คว่าผูกบัญชีแล้วไหม |
| `register_npu_user(...)` | POST `/api/` | ผูกบัญชีใหม่ |
| `get_profile(user_ldap, user_type)` | GET `/std-info/{id}/` หรือ `/staff-info/{id}/` | ดึงชื่อ-คณะ |
| `verify_ldap(username, password)` | POST `/auth-ldap/auth_ldap/` | ตรวจ AD credentials |
| `get_walai_status(user_ldap)` | GET `/walai/check_user_walai/{id}/` | Phase 3 |

`user_type` ต้องเป็น **ภาษาไทยเป๊ะ**: `"นักศึกษา"` หรือ `"บุคลากรภายในมหาวิทยาลัย"`

---

## Models

- **Room** — ห้องบริการ, `booking_name` เป็น unique key ใช้ใน URL
- **LineUser** — cache ผู้ใช้ที่ผูก LINE กับ LDAP แล้ว (source of truth อยู่ที่ api.npu.ac.th)
- **Booking** — การจอง, status: `confirmed` / `cancelled`
- **BookingLog** — audit trail, actions: `created`, `cancelled`, `accessed`, `auto_off`

**Conflict check** ต้องใช้ `select_for_update()` เสมอ — ดู `check_and_create_booking()` ใน `views.py`

---

## Settings สำคัญ

```python
FORCE_SCRIPT_NAME = '/reserv'          # sub-path deployment
STATIC_URL = '/reserv/static/'
USE_X_FORWARDED_HOST = True            # อยู่หลัง nginx
TIME_ZONE = 'Asia/Bangkok'
```

ทุก secret อยู่ใน `.env` อ่านด้วย `python-decouple`:
`SECRET_KEY`, `DB_*`, `LINE_*`, `HA_ACCESS_SECRET`

---

## Phases

| Phase | สถานะ | เนื้อหา |
|---|---|---|
| **Phase 1** | ✅ Code พร้อม, DB migrate แล้ว | Register, Booking, Calendar, Admin |
| **Phase 2** | ⏳ หลัง go-live | IoT Sonoff via `api.npu.ac.th/sonoff/` |
| **Phase 3** | ⏳ ทีหลังสุด | Virtual Card + Walai + JsBarcode |

**Phase 2:** ใช้ `/api/check-access/` (protected ด้วย `HA_ACCESS_SECRET` header `X-HA-Token`) + `ha_entity_id` field ใน Room model รองรับแล้ว

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
- Endpoint URL ที่ต้องตั้งใน LINE Developers Console: `https://lib.npu.ac.th/reserv/booking/?room=mini`
- LIFF ต้องการ HTTPS — ทดสอบใน localhost ไม่ได้ (ดู Capture.PNG)
- Handle ทั้ง 2 กรณี: เปิดใน LINE app (ได้ userId ทันที) และ browser ปกติ (ต้อง `liff.login()`)
