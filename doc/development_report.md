# รายงานการพัฒนาระบบจองพื้นที่บริการ Smart Creative Learning Space
## สำนักวิทยบริการ มหาวิทยาลัยนครพนม
### การย้ายระบบจากโครงสร้างภายนอก (Cloud-based) สู่โครงสร้างภายใน (On-premise)

---

**เวอร์ชัน:** 1.0
**วันที่จัดทำ:** เมษายน 2569
**ผู้พัฒนา:** สำนักวิทยบริการ มหาวิทยาลัยนครพนม

---

## บทคัดย่อ

รายงานฉบับนี้บันทึกกระบวนการพัฒนาและย้ายระบบจองพื้นที่บริการ Smart Creative Learning Space จากระบบเดิมที่พึ่งพาบริการคลาวด์ภายนอก (Google Apps Script + Google Sheets + PHP บน external hosting) ไปสู่ระบบใหม่ที่ทำงานบนโครงสร้างพื้นฐานภายในองค์กร (Django + MySQL + Windows Server) โดยยังคงการเชื่อมต่อกับ LINE LIFF เพื่อประสบการณ์ผู้ใช้ที่คุ้นเคย ระบบใหม่เพิ่มความสามารถด้านการตรวจสอบสิทธิ์ผ่าน Active Directory ของมหาวิทยาลัย การแจ้งเตือนแบบ real-time ผ่าน LINE Messaging API และการบริหารจัดการวันหยุดและข้อจำกัดการจอง

---

## 1. ที่มาและความสำคัญของปัญหา

### 1.1 บริบทการให้บริการ

สำนักวิทยบริการ มหาวิทยาลัยนครพนม จัดพื้นที่บริการ Smart Creative Learning Space สำหรับนักศึกษาและบุคลากรเพื่อใช้ในการศึกษา ทำงานกลุ่ม และกิจกรรมเชิงสร้างสรรค์ พื้นที่ประกอบด้วยห้องย่อย 5 ประเภท ได้แก่

| รหัสห้อง | ชื่อห้อง | ความจุ |
|---|---|---|
| `mini` | Mini Theater | — |
| `netflix` | Edutainment Zone | — |
| `canva` | Canva Studio | — |
| `chat-gpt` | AI Learning Zone | — |
| `meeting_f1` | Meeting Room F1 | — |

ระบบการจองเป็นกลไกสำคัญในการบริหารพื้นที่ให้มีประสิทธิภาพ ป้องกันการจองซ้ำซ้อน และสร้างหลักฐานการใช้งานสำหรับการรายงาน

### 1.2 ระบบเดิมและข้อจำกัด

ระบบเดิมถูกพัฒนาในรูปแบบ **Quick Solution** โดยใช้เครื่องมือที่หาได้ทันทีโดยไม่ต้องใช้งบประมาณเพิ่มเติม ได้แก่

**สถาปัตยกรรมระบบเดิม:**
```
ผู้ใช้ใน LINE OA
    ↓ กด Flex Message Card
    ↓ เปิด LIFF
HTML Form (netflix.html บน arc.npu.ac.th)
    ↓ ผู้ใช้กรอกข้อมูล
Google Apps Script (Web App)
    ↓ บันทึกข้อมูล
Google Sheets (ฐานข้อมูล)
    ↓ ตรวจสิทธิ์
testdb.php บน external server
    ↓ ดึงข้อมูลผู้ใช้
ฐานข้อมูล LDAP / AD ของมหาวิทยาลัย
```

**ข้อจำกัดที่พบ:**

1. **การพึ่งพาบริการภายนอก (Vendor Lock-in)**
   - Google Sheets มีข้อจำกัดด้านจำนวน API calls ต่อวัน
   - Google Apps Script มี execution time limit (6 นาที/ครั้ง)
   - หากนโยบาย Google เปลี่ยนแปลง ระบบอาจหยุดทำงานทันที
   - LINE Notify ซึ่งใช้แจ้งเตือนประกาศปิดบริการถาวรในเดือนเมษายน 2568

2. **ความปลอดภัยของข้อมูล**
   - ข้อมูลผู้ใช้และบันทึกการจองถูกเก็บใน Google Sheets บนระบบคลาวด์ภายนอก
   - ไม่สอดคล้องกับนโยบายการจัดเก็บข้อมูลภายในองค์กร
   - ขาดกลไก audit trail ที่เป็นมาตรฐาน

3. **ข้อจำกัดด้านฟังก์ชันการทำงาน**
   - ไม่สามารถตรวจสอบ conflict การจองแบบ real-time ได้อย่างน่าเชื่อถือ (race condition)
   - ไม่มีระบบแจ้งเตือนเมื่อใกล้ถึงเวลาจอง
   - ไม่สามารถกำหนดวันหยุดหรือข้อจำกัดการจองล่วงหน้าได้
   - ขาดรายงานและสถิติการใช้งานที่ยืดหยุ่น

4. **ความยากในการบำรุงรักษา**
   - โค้ด Google Apps Script ไม่มี version control
   - การ debug ทำได้ยากเนื่องจากไม่มี log ที่เป็นระบบ
   - การ deploy ต้องอาศัยผู้ที่มีสิทธิ์เข้าถึง Google Account เฉพาะ

---

## 2. การวิเคราะห์และวางแผนระบบใหม่

### 2.1 ข้อกำหนดความต้องการ (Requirements)

จากการวิเคราะห์ระบบเดิมและสัมภาษณ์ผู้ใช้งาน กำหนดความต้องการระบบใหม่ดังนี้

**ความต้องการเชิงฟังก์ชัน (Functional Requirements):**

| รหัส | ความต้องการ | ความสำคัญ |
|---|---|---|
| FR-01 | ผู้ใช้จองห้องผ่าน LINE LIFF ได้ | สูงสุด |
| FR-02 | ตรวจสอบสิทธิ์ผ่าน LINE userId และ api.npu.ac.th | สูงสุด |
| FR-03 | ดึงข้อมูลชื่อ-นามสกุล คณะ สาขา จาก NPU API อัตโนมัติ | สูง |
| FR-04 | ตรวจสอบ conflict การจองแบบ real-time | สูงสุด |
| FR-05 | บริหารจัดการวันหยุดและการปิดบริการชั่วคราว | สูง |
| FR-06 | จำกัดการจองล่วงหน้าไม่เกิน 3 วันทำงาน | สูง |
| FR-07 | แจ้งเตือนจองสำเร็จผ่าน LINE ทันที | สูง |
| FR-08 | แจ้งเตือนก่อนถึงเวลาจอง 15 นาที | ปานกลาง |
| FR-09 | แจ้งเตือนก่อนหมดเวลา 10 นาที | ปานกลาง |
| FR-10 | ผู้ดูแลระบบจัดการข้อมูลผ่าน Admin Panel | สูง |

**ความต้องการเชิงไม่ใช่ฟังก์ชัน (Non-Functional Requirements):**

| รหัส | ความต้องการ | เป้าหมาย |
|---|---|---|
| NFR-01 | ข้อมูลเก็บบนเซิร์ฟเวอร์ภายในองค์กร | 100% on-premise |
| NFR-02 | รองรับผู้ใช้พร้อมกัน | ≥ 50 concurrent users |
| NFR-03 | เวลาตอบสนอง API | < 2 วินาที |
| NFR-04 | ความพร้อมใช้งาน (Uptime) | ≥ 95% |
| NFR-05 | รองรับทั้ง LINE In-App Browser และ External Browser | — |

### 2.2 การเลือก Technology Stack

| ส่วนประกอบ | ทางเลือกที่พิจารณา | ที่เลือกใช้ | เหตุผล |
|---|---|---|---|
| Backend Framework | Flask, FastAPI, **Django** | **Django 4.2** | มี ORM, Admin Panel, Migration ในตัว เหมาะกับทีมขนาดเล็ก |
| Database | SQLite, PostgreSQL, **MySQL** | **MySQL 8.0** | Infrastructure ที่มีอยู่แล้วในองค์กร |
| WSGI Server | Gunicorn, uWSGI, **Waitress** | **Waitress** | รองรับ Windows Server ได้โดยตรง |
| Reverse Proxy | Apache, **Nginx**, IIS ARR | **IIS ARR** | Windows Server มี IIS อยู่แล้ว |
| Static Files | Django Dev Server, **WhiteNoise** | **WhiteNoise** | Serve ผ่าน Waitress ได้โดยไม่ต้องตั้ง IIS แยก |
| Process Manager | Windows Service, **NSSM** | **NSSM** | จัดการ Python process บน Windows ได้ง่าย |
| Frontend | React, Vue, **Django Template** | **Django Template + Bootstrap 5** | ลด complexity เหมาะกับ LIFF single-page |
| LINE Integration | LINE SDK, **LIFF SDK** | **LIFF 2.15** | ดึง userId โดยตรงใน LINE app |

### 2.3 สถาปัตยกรรมระบบใหม่

```
ผู้ใช้ใน LINE OA
    ↓ กด Flex Message Card
    ↓ URL: https://lib.npu.ac.th/reserv/booking/?room=<key>

IIS ARR (lib.npu.ac.th)
    ↓ web.config rewrite: ^reserv/(.*) → 127.0.0.1:8003

Waitress WSGI Server (:8003)
    ├── /reserv/static/* → WhiteNoise (serve staticfiles/)
    └── /reserv/*        → Django Application

Django Application (booking/views.py)
    ├── booking_page()      → render LIFF form
    ├── check_user()        → ตรวจสิทธิ์ + cache profile
    ├── create_booking()    → conflict check + บันทึก
    └── booking_success()   → หน้ายืนยัน

External APIs:
    ├── api.npu.ac.th/api/{userId}/         → ตรวจ LINE-LDAP mapping
    ├── api.npu.ac.th/std-info/{ldap}/      → ข้อมูลนักศึกษา
    ├── api.npu.ac.th/staff-info/{ldap}/    → ข้อมูลบุคลากร
    └── api.line.me/v2/bot/message/push     → LINE push notification

Database (MySQL reserv_db):
    ├── booking_room        → ข้อมูลห้อง
    ├── booking_lineuser    → cache ผู้ใช้ที่ผูก LINE+LDAP
    ├── booking_booking     → บันทึกการจอง
    ├── booking_bookinglog  → audit trail
    └── booking_holidaydate → วันหยุดและการปิดบริการ

Windows Task Scheduler:
    └── ทุก 1 นาที → manage.py send_reminders
                      → แจ้งเตือน 15 นาที / 10 นาที
```

### 2.4 ออกแบบ Database Schema

```sql
-- ห้องบริการ
booking_room (
    id, name, booking_name [UNIQUE KEY],
    description, location, capacity,
    open_time, close_time,
    is_active, ha_entity_id
)

-- ผู้ใช้ที่ผูก LINE กับ LDAP แล้ว (cache จาก api.npu.ac.th)
booking_lineuser (
    id, line_user_id [UNIQUE],
    display_name, user_ldap, user_type,
    full_name, faculty, department,    -- cache จาก NPU API
    profile_updated_at,                -- timestamp cache ล่าสุด
    created_at, updated_at, is_active
)

-- การจอง
booking_booking (
    id, room_id → booking_room,
    line_user_id → booking_lineuser,
    faculty, department, group_name,
    booking_date, start_time, end_time,
    attendees, status [confirmed/cancelled],
    created_at, cancelled_at, cancel_reason,
    notified_start, notified_15min, notified_10min  -- LINE notification tracking
)
INDEX: (room_id, booking_date, status)  -- สำหรับ conflict check

-- Audit Trail
booking_bookinglog (
    id, booking_id → booking_booking,
    action [created/cancelled/notified_15min/notified_10min],
    note, timestamp
)

-- วันหยุดและการปิดบริการ
booking_holidaydate (
    id, date [UNIQUE], description, is_active
)
```

**การออกแบบ Index:** field `(room_id, booking_date, status)` ถูก index เพื่อให้ conflict check query เร็วที่สุด เนื่องจากเป็น query ที่รันทุกครั้งที่มีการจอง

---

## 3. กระบวนการพัฒนาและปัญหาที่พบ

### Phase A: การตั้งค่าโครงสร้างพื้นฐาน

**สิ่งที่ทำ:**
- สร้าง Django project พร้อม `booking` app
- ตั้งค่า MySQL connection ผ่าน `mysqlclient`
- ตั้งค่า sub-path deployment ด้วย `FORCE_SCRIPT_NAME = '/reserv'`
- ตั้งค่า `WhiteNoise` สำหรับ serve static files ผ่าน Waitress
- กำหนด Models: `Room`, `LineUser`, `Booking`, `BookingLog`
- สร้าง Django Admin สำหรับจัดการข้อมูล

**ปัญหาที่พบและวิธีแก้:**

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| Static files 404 (Admin ไม่มี CSS) | IIS มี rule `Reserv Static` ที่ block request ไม่ให้ถึง Waitress | ลบ rule `Reserv Static` และ `Reserv Media` ออก ให้ `Reserv App` rule จัดการทุก path แทน |
| `ImportError: Couldn't import Django` | ยังไม่ได้ activate venv | `venv\Scripts\activate` ก่อนรัน manage.py |
| Service ค้างใน `SERVICE_PAUSED` | NSSM throttle เพราะ app crash หลายครั้ง | `sc.exe queryex reserv` → get PID → `taskkill /F /PID` → `nssm start reserv` |
| `NSSM ใช้ Python ผิดตัว` | NSSM ชี้ไปยัง system Python แทน venv | แก้ path ใน NSSM ให้ใช้ `venv\Scripts\python.exe` |

### Phase B: LINE LIFF Integration และระบบตรวจสิทธิ์

**สิ่งที่ทำ:**
- เชื่อมต่อ LIFF SDK 2.15.0
- พัฒนา `check_user()` API ที่ทำหน้าที่เป็น proxy ไปยัง `api.npu.ac.th`
- ออกแบบระบบ cache profile 30 วัน เพื่อลด API calls ไปยัง NPU API
- รองรับ 2 กรณี: เปิดใน LINE app (ได้ userId ทันที) และใน browser ปกติ (ต้อง `liff.login()`)
- จัดการ `liff.state` parameter ที่ LIFF encode URL params ไว้

**การออกแบบ Profile Cache:**

```
ผู้ใช้เปิดหน้า booking
    ↓
LIFF getProfile() → userId, displayName
    ↓
POST /api/check-user/ { userId, displayName }
    ↓
LineUser ใน DB มีไหม? + profile_updated_at < 30 วัน?
    ├── ใช่ (fast path) → คืน cached data ทันที (~50ms)
    └── ไม่ → GET api.npu.ac.th/api/{userId}/
                ↓
              ได้ userLdap, user_type
                ↓
              GET /std-info/{ldap}/ หรือ /staff-info/{ldap}/
                ↓
              บันทึก/อัปเดต LineUser
                ↓
              คืน full_name, faculty, department (~800ms)
```

**ปัญหาที่พบและวิธีแก้:**

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| Spinner แสดงแต่ JS ไม่ทำงาน | `<script>` setup block อยู่หลัง LIFF SDK | แยกเป็น 2 blocks: setup ก่อน SDK load, liff.init() หลัง |
| `SyntaxError: Unexpected token '&'` | Django escape `"` เป็น `&quot;` ใน JSON | เปลี่ยน `{{ room_json }}` เป็น `{{ room_json\|safe }}` |
| `full_name` ว่างเปล่า | ใช้ `data.get('user_ldap')` แต่ API คืน camelCase `userLdap` | แก้เป็น `data.get('userLdap', '')` |
| `LIFF init error: channel not found` | `LINE_LIFF_ID` ไม่ได้ตั้งใน .env | เพิ่ม `LINE_LIFF_ID=...` ใน .env แล้ว restart |
| 400 Bad Request หลัง liff.login() | LIFF Endpoint URL ยังเป็น URL เดิม | อัปเดตใน LINE Developers Console เป็น `https://lib.npu.ac.th/reserv/booking/` |

**การ parse ข้อมูล NPU Profile:**

NPU API คืน format ต่างกันระหว่างนักศึกษาและบุคลากร จึงต้องตรวจสอบก่อนแกะข้อมูล:

```python
# บุคลากร — ตรวจด้วย key 'staffname'
fields: prefixfullname, staffname, staffsurname, departmentname, posnameth

# นักศึกษา — ตรวจด้วย key 'student_name'
fields: prefix_name, student_name, student_surname, faculty_name, program_name
```

### Phase C: Business Logic — Conflict Check และ Booking

**การออกแบบ Conflict Check:**

ใช้ `SELECT FOR UPDATE` เพื่อป้องกัน race condition กรณีผู้ใช้หลายคนจองเวลาเดียวกันพร้อมกัน:

```python
with transaction.atomic():
    conflict = Booking.objects.select_for_update().filter(
        room         = room,
        booking_date = b_date,
        status       = 'confirmed',
        start_time__lt = e_time,   # booking เริ่มก่อนเวลาสิ้นสุดที่จะจอง
        end_time__gt   = s_time,   # booking สิ้นสุดหลังเวลาเริ่มที่จะจอง
    ).exists()
```

เงื่อนไข overlap: booking A ทับกับ booking B เมื่อ `A.start < B.end AND A.end > B.start`

**ปัญหาที่พบและวิธีแก้:**

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| ปุ่มปิดหน้าสำเร็จไม่ทำงาน | ใช้ `window.close()` ซึ่ง browser ปฏิเสธถ้าไม่ได้เปิดด้วย JS | ตรวจด้วย `liff.isInClient()` แล้วใช้ `liff.closeWindow()` แทน |

### Phase D: ระบบวันหยุดและข้อจำกัดการจอง

**สิ่งที่ทำ:**
- สร้าง `HolidayDate` model สำหรับบันทึกวันหยุดราชการและประกาศปิดชั่วคราว
- ตรวจสอบใน `create_booking()` ก่อนบันทึก: ห้ามจองวันหยุด และห้ามจองเกิน 3 วันทำงาน
- ส่ง holiday list ไปยัง frontend เพื่อ disable วันที่ใน date picker อัตโนมัติ
- Management command `load_holidays` สำหรับโหลดวันหยุดประจำปีทีเดียว
- ผู้ดูแลระบบเพิ่มวันหยุดพิเศษ (ประกาศปิดชั่วคราว) ได้ตลอดเวลาผ่าน Admin

**อัลกอริทึมนับวันทำงาน:**

```python
def _count_workdays_between(start, end_inclusive, holidays):
    count = 0
    cur = start
    while cur <= end_inclusive:
        if cur.weekday() < 5 and cur not in holidays:  # จันทร์–ศุกร์ + ไม่ใช่วันหยุด
            count += 1
        cur += timedelta(days=1)
    return count

# ใช้งาน: นับวันทำงานจาก "พรุ่งนี้" ถึง "วันที่จะจอง"
workdays_ahead = _count_workdays_between(today + timedelta(1), b_date, holidays)
if workdays_ahead > 3:
    return error("จองล่วงหน้าได้ไม่เกิน 3 วันทำงาน")
```

**หมายเหตุ:** ห้องสมุดเปิดทำการวันเสาร์-อาทิตย์ด้วย ดังนั้นการนับ "วันทำงาน" สำหรับข้อจำกัดการจองล่วงหน้านับเฉพาะวันจันทร์–ศุกร์ที่ไม่ใช่วันหยุดราชการ แต่ผู้ใช้ยังสามารถ**จองวันเสาร์-อาทิตย์ได้** ตราบเท่าที่ไม่ได้ประกาศปิด

### Phase E: ระบบแจ้งเตือน LINE Messaging API

**สิ่งที่ทำ:**
- พัฒนา `_push_line()` helper สำหรับส่ง push message ผ่าน LINE Messaging API
- แจ้งเตือนจองสำเร็จทันทีหลัง `create_booking()` สำเร็จ
- Management command `send_reminders` รันทุก 1 นาทีผ่าน Windows Task Scheduler
- เพิ่ม tracking fields ใน Booking: `notified_start`, `notified_15min`, `notified_10min`
- บันทึก `BookingLog` ทุกครั้งที่ส่งแจ้งเตือน

**หมายเหตุด้านเทคนิค:** LINE Notify ปิดบริการถาวรตั้งแต่ 1 เมษายน 2568 จึงใช้ LINE Messaging API (Push Message) แทน โดยใช้ `LINE_CHANNEL_ACCESS_TOKEN` เดิมที่มีอยู่แล้ว เงื่อนไขคือผู้จองต้อง add LINE Official Account เป็นเพื่อนก่อน

**กลไกป้องกันการแจ้งเตือนซ้ำ:**
```python
# send_reminders.py
if not b.notified_15min:           # ตรวจ flag
    if target - window <= now <= target + window:  # หน้าต่าง ±1 นาที
        if _push_text(user_id, msg):
            b.notified_15min = True
            b.save(update_fields=['notified_15min'])
```

ใช้หน้าต่าง ±1 นาทีเพื่อรองรับ Task Scheduler ที่อาจรันไม่ตรงวินาทีพอดี และ flag `notified_*` ป้องกันการส่งซ้ำแม้ command จะรันหลายรอบ

---

## 4. โครงสร้างไฟล์ระบบ

```
reserv/
├── reserv/
│   ├── settings.py          — ค่าตั้งค่าระบบ (อ่านจาก .env)
│   ├── urls.py              — URL routing หลัก
│   └── wsgi.py              — WSGI entry point
│
├── booking/
│   ├── models.py            — Room, LineUser, Booking, BookingLog, HolidayDate
│   ├── views.py             — business logic ทั้งหมด
│   ├── urls.py              — URL patterns
│   ├── admin.py             — Django Admin configuration
│   ├── templates/
│   │   └── booking/
│   │       ├── booking.html — LIFF form หน้าจอง
│   │       └── success.html — หน้าจองสำเร็จ
│   ├── migrations/
│   │   ├── 0001_initial.py              — Room, LineUser, Booking, BookingLog
│   │   ├── 0002_lineuser_profile_fields.py — full_name, faculty, department, profile_updated_at
│   │   ├── 0003_holiday_date.py         — HolidayDate model
│   │   └── 0004_notification_fields.py  — notified_start/15min/10min
│   └── management/commands/
│       ├── load_holidays.py  — โหลดวันหยุดประจำปี
│       ├── send_reminders.py — แจ้งเตือน 15/10 นาที (รันด้วย Task Scheduler)
│       └── test_notify.py    — ทดสอบ LINE push notification
│
├── deploy/
│   └── waitress_serve.py    — script สำหรับ start Waitress
│
├── doc/
│   ├── deploy_guide.md      — คู่มือ deploy และปัญหาที่พบ
│   └── development_report.md — รายงานการพัฒนา (ฉบับนี้)
│
├── sample/
│   └── 05_2025 โต๊ะประชุมห้องวารสาร.xlsx — ข้อมูล reference จากระบบเดิม
│
├── requirements.txt         — Django, mysqlclient, requests, waitress, whitenoise, python-dotenv
├── .env                     — ค่า secret (ไม่ commit ใน git)
└── CLAUDE.md                — คำแนะนำสำหรับ AI assistant
```

---

## 5. API Endpoints

| Method | URL | หน้าที่ |
|---|---|---|
| GET | `/reserv/booking/?room=<key>` | หน้า LIFF form จอง |
| GET | `/reserv/booking/success/?id=<id>` | หน้าจองสำเร็จ |
| POST | `/reserv/api/check-user/` | ตรวจ userId + ดึง profile |
| POST | `/reserv/api/booking/` | สร้างการจอง |
| * | `/reserv/admin/` | Django Admin Panel |

---

## 6. การจัดการ Secret และ Environment Variables

ข้อมูลสำคัญทั้งหมดถูกแยกออกจาก codebase ใน `.env` file และไม่ถูก commit เข้า Git:

```env
SECRET_KEY=...                    # Django secret key
DEBUG=False                       # production mode
ALLOWED_HOSTS=localhost,lib.npu.ac.th
FORCE_SCRIPT_NAME=/reserv         # sub-path deployment
STATIC_URL=/reserv/static/
CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th
WAITRESS_HOST=127.0.0.1
WAITRESS_PORT=8003
DB_NAME=reserv_db
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=3306
LINE_LIFF_ID=...                  # LIFF App ID
LINE_CHANNEL_SECRET=...           # LINE Bot Channel Secret
LINE_CHANNEL_ACCESS_TOKEN=...     # สำหรับ push message
HA_ACCESS_SECRET=...              # Phase 2: IoT integration
```

---

## 7. สรุปผลการพัฒนาและเปรียบเทียบระบบ

### 7.1 เปรียบเทียบระบบเดิมและระบบใหม่

| หัวข้อ | ระบบเดิม | ระบบใหม่ |
|---|---|---|
| **การเก็บข้อมูล** | Google Sheets (cloud) | MySQL on-premise |
| **ตำแหน่งข้อมูล** | ภายนอกองค์กร | ภายในองค์กร |
| **Conflict Check** | ไม่น่าเชื่อถือ (race condition) | `SELECT FOR UPDATE` + `transaction.atomic()` |
| **ตรวจสิทธิ์** | testdb.php | api.npu.ac.th + cache 30 วัน |
| **ดึงชื่อผู้ใช้** | กรอกเอง | อัตโนมัติจาก NPU API |
| **วันหยุด** | ไม่มี | HolidayDate model + Admin UI |
| **จำกัดล่วงหน้า** | ไม่มี | 3 วันทำงาน (คำนวณอัตโนมัติ) |
| **แจ้งเตือนจองสำเร็จ** | ไม่มี | LINE push ทันที |
| **แจ้งเตือน 15 นาที** | ไม่มี | Windows Task Scheduler |
| **แจ้งเตือน 10 นาที** | ไม่มี | Windows Task Scheduler |
| **Audit Trail** | ไม่มี | BookingLog ทุก action |
| **Admin Panel** | Google Sheets | Django Admin |
| **Version Control** | ไม่มี | Git (GitHub) |
| **ค่าบริการรายเดือน** | $0 (แต่มีข้อจำกัด) | $0 (on-premise) |

### 7.2 สถานะฟีเจอร์

| ฟีเจอร์ | สถานะ | หมายเหตุ |
|---|---|---|
| จองห้อง + conflict check | ✅ พร้อมใช้งาน | |
| ตรวจสิทธิ์ NPU API + cache | ✅ พร้อมใช้งาน | |
| รองรับนักศึกษาและบุคลากร | ✅ พร้อมใช้งาน | |
| วันหยุด + จำกัด 3 วันทำงาน | ✅ พร้อมใช้งาน | |
| แจ้งเตือนจองสำเร็จ | ✅ พร้อมใช้งาน | |
| แจ้งเตือนก่อนเริ่ม 15 นาที | ✅ พร้อมใช้งาน | |
| แจ้งเตือนก่อนหมด 10 นาที | ✅ พร้อมใช้งาน | |
| ยกเลิกการจอง (UI) | ⏳ รอพัฒนา | ทำได้ผ่าน Admin |
| Blacklist / No-show count | ⏳ รอพัฒนา | |
| Phase 2: IoT Sonoff | ⏳ รอพัฒนา | field `ha_entity_id` รองรับแล้ว |
| Phase 3: Virtual Card + Walai | ⏳ รอพัฒนา | |

---

## 8. ขั้นตอน Deploy

### 8.1 ติดตั้งครั้งแรก

```powershell
cd C:\project
git clone https://github.com/azimuthotg/reserv.git reserv
cd reserv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy deploy\.env.production .env
notepad .env                            # แก้ค่าให้ครบ
python manage.py migrate
python manage.py load_holidays          # โหลดวันหยุด 2026
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 8.2 ตั้งค่า NSSM Service

```powershell
c:\nssm\nssm.exe install reserv "C:\project\reserv\venv\Scripts\python.exe" "C:\project\reserv\deploy\waitress_serve.py"
c:\nssm\nssm.exe set reserv AppDirectory "C:\project\reserv"
c:\nssm\nssm.exe start reserv
```

### 8.3 ตั้งค่า Windows Task Scheduler

```powershell
schtasks /create /tn "ReservReminder" /tr "C:\project\reserv\venv\Scripts\python.exe C:\project\reserv\manage.py send_reminders" /sc MINUTE /mo 1 /ru SYSTEM /f
```

### 8.4 อัปเดตระบบ

```powershell
git pull origin master
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
c:\nssm\nssm.exe restart reserv
```

---

## 9. แผนการพัฒนาในอนาคต (Roadmap)

### Phase 2 — IoT Integration (หลัง go-live)
- เชื่อมต่อ Sonoff smart plug ผ่าน `api.npu.ac.th/sonoff/`
- เปิด/ปิดอุปกรณ์ไฟฟ้าในห้องอัตโนมัติตามเวลาจอง
- API `/api/check-access/` สำหรับ Home Assistant trigger (protected ด้วย `HA_ACCESS_SECRET`)

### Phase 3 — Virtual Card และ Walai Integration
- บัตรเข้าใช้บริการแบบดิจิทัล (JsBarcode)
- ตรวจสอบสิทธิ์การเข้าห้องสมุดผ่าน Walai system

### ฟีเจอร์เสริมที่วางแผน
- UI ยกเลิกการจองสำหรับผู้ใช้ (ปัจจุบันทำได้แค่ผ่าน Admin)
- ระบบ Blacklist สำหรับผู้ที่จองแล้วไม่มา (no-show counter)
- Dashboard สถิติการใช้งานสำหรับผู้บริหาร

---

## ภาคผนวก ก: ปัญหาที่พบทั้งหมดระหว่างพัฒนา

| # | ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|---|
| 1 | Static files 404, Admin ไม่มี CSS | IIS rule block request ก่อนถึง Waitress | ลบ rule Reserv Static/Media ออก |
| 2 | NSSM ค้าง SERVICE_PAUSED | App crash หลายครั้ง NSSM throttle | kill PID → nssm start |
| 3 | ImportError: Couldn't import Django | ลืม activate venv | `venv\Scripts\activate` |
| 4 | LIFF channel not found | LINE_LIFF_ID ไม่ได้ตั้งใน .env | เพิ่มใน .env + restart |
| 5 | 400 Bad Request หลัง liff.login() | LIFF Endpoint URL เป็น URL เดิม | อัปเดตใน LINE Developers Console |
| 6 | NSSM ใช้ Python ผิดตัว | ชี้ไปยัง system Python | แก้ path เป็น venv\Scripts\python.exe |
| 7 | Spinner ค้าง JS ไม่รัน | Script block ลำดับผิด | แยก 2 blocks: setup ก่อน SDK |
| 8 | SyntaxError: Unexpected token '&' | Django escape JSON | ใช้ `\|safe` filter |
| 9 | full_name ว่างเปล่า | camelCase vs snake_case field name | แก้เป็น `userLdap` |
| 10 | ปุ่มปิดไม่ทำงาน | window.close() ถูก browser block | ใช้ liff.closeWindow() |

---

*เอกสารนี้จัดทำเพื่อใช้เป็นอ้างอิงในงานวิจัยการพัฒนาระบบและเพื่อการบำรุงรักษาระบบในอนาคต*
