# IoT Flow — ระบบควบคุมอุปกรณ์อัตโนมัติ
## Smart Creative Learning Space — สำนักวิทยบริการ มนพ.

---

## ภาพรวม Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                    เครือข่าย Wi-Fi ภายในห้องสมุด               │
│                                                                 │
│   Windows Server              Home Assistant        Sonoff      │
│   (Django + MySQL)  ←HTTP→   (HA_IP:HA_PORT)  ←Wi-Fi→  Smart  │
│                               Bearer Token                Plug  │
│                                                          (x N)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flow ที่ 1 — ผู้จองควบคุมอุปกรณ์ (User-initiated)

```
[Task Scheduler — ทุก 1 นาที]
    ↓ send_reminders.py
    ↓ ก่อนเวลาจอง 15 นาที

LINE push → ผู้จอง
  ┌─────────────────────────────┐
  │ ⏰ อีก 15 นาทีถึงเวลาใช้พื้นที่ │
  │ ห้อง / วันที่ / เวลา / กลุ่ม   │
  │ [✅ Check-in เลย]            │
  └─────────────────────────────┘
          ↓ ผู้จองกดปุ่ม

POST /api/checkin/ { userId }
    ↓ Django ตรวจสอบ active booking (วันนี้ + ในช่วงเวลา + confirmed)
    ├── ❌ ไม่มีสิทธิ์ → แจ้ง error
    └── ✅ มีสิทธิ์
            ↓ booking.checked_in = True
            ↓ LINE push → ผู้จอง

  ┌──────────────────────────────────────┐
  │ ✅ Check-in สำเร็จ                   │
  │ ห้อง / วันที่ / เวลา / กลุ่ม         │
  │ [🎛️ ควบคุมอุปกรณ์ในห้อง]            │
  └──────────────────────────────────────┘
          ↓ ผู้จองกดปุ่ม (เปิด LIFF)

GET /api/room-status/?userId=X&room_key=Y
    ↓ Django ตรวจสอบ active booking
    ↓ Django → HA REST API (GET /api/states/{entity_id})
    ↓ ดึงสถานะ on/off ของทุกอุปกรณ์ในห้อง
    ↓ คืนรายการอุปกรณ์ + สถานะให้ Room Control page

[หน้า /room-control/ — LIFF บนมือถือ]
    ↓ แสดงรายการอุปกรณ์ + สถานะปัจจุบัน
    ↓ ผู้จองกดปุ่ม toggle

POST /api/device-toggle/ { userId, room_key, entity_id }
    ↓ Django ตรวจสอบ active booking
    ↓ ตรวจว่า entity_id เป็นของห้องนี้จริง
    ↓ Django → HA REST API (POST /api/services/switch/toggle)
    ↓ HA → Sonoff Smart Plug (Wi-Fi — เครือข่ายภายใน)
    ↓ คืนสถานะใหม่ (on/off) ให้ผู้ใช้
```

---

## Flow ที่ 2 — ปิดอุปกรณ์อัตโนมัติเมื่อหมดเวลา

```
[Task Scheduler — ทุก 1 นาที]
    ↓ send_reminders.py
    ↓ ตรวจว่า booking.end_time ผ่านแล้วหรือไม่

    └── ✅ หมดเวลาแล้ว + notified_auto_off = False
            ↓ RoomDevice.objects.filter(room=booking.room)
            ↓ วนทุกอุปกรณ์ในห้อง

            Django → HA REST API
            (POST /api/services/switch/turn_off { entity_id })
                ↓
            HA → Sonoff Smart Plug (Wi-Fi)
                ↓ ปิดอุปกรณ์ทุกตัวในห้อง

            ↓ booking.notified_auto_off = True
            ↓ BookingLog: action = 'auto_off'
```

---

## Flow ที่ 3 — รายงานสถานะ IoT ประจำเช้า

```
[Task Scheduler — 07:30 ทุกวัน]
    ↓ morning_iot_report.py

    วนทุกห้องที่ is_active = True + กลุ่มอุปกรณ์ส่วนกลาง (RoomDevice ที่ room = NULL)
        ↓ วนทุกอุปกรณ์ใน RoomDevice
        ↓ Django → HA REST API (GET /api/states/{entity_id})
        ↓ รับสถานะ: on / off / unknown / HA offline

    สรุปผล:
    ┌─────────────────────────────────────┐
    │ ✅ IoT ปกติทุกอุปกรณ์ — DD/MM/YYYY │  ← ถ้าทุกตัวปกติ
    │ หรือ                               │
    │ ⚠️ พบอุปกรณ์ผิดปกติ — DD/MM/YYYY   │  ← ถ้ามีผิดปกติ
    │                                     │
    │ Online: N  Offline: N  ไม่ทราบ: N  │
    │                                     │
    │ ✅ ห้อง MINI THEATER                │
    │   🟢 ระบบแสงสว่าง: Online           │
    │ ⚠️ อุปกรณ์ส่วนกลาง                  │
    │   🔴 flip gate2: Offline            │
    └─────────────────────────────────────┘
        ↓
    LINE push → LINE Group ID (IOT_ADMIN_LINE_ID)
    (กลุ่มทีมผู้ดูแลระบบ)
```

---

## Flow ที่ 4 — เจ้าหน้าที่ตรวจสอบและควบคุม (Staff Portal)

```
[เจ้าหน้าที่] เปิด /manage/iot-monitor/ (Desktop)
    ↓ แสดงสถานะอุปกรณ์ทุกห้อง + กลุ่มอุปกรณ์ส่วนกลาง real-time
    ↓ (การ์ดทั้งหมดมาจาก helper กลางตัวเดียว `_iot_cards()` ใน manage_views.py)
    ↓ ดึงจาก HA REST API (/api/states/{entity_id})

    ├── กด "Refresh" → /manage/iot-monitor/refresh/
    │       ↓ อัพเดทสถานะใหม่จาก HA
    │
    ├── กด "ควบคุม" → /manage/iot-monitor/control/<pk>/
    │       ↓ Django → HA toggle/turn_on/turn_off
    │       ↓ HA → Sonoff (Wi-Fi)
    │
    └── กด "แจ้งเตือน" → /manage/iot-monitor/notify/
            ↓ LINE push → LINE Group ID
            ↓ แจ้งสถานะอุปกรณ์ให้ทีม
```

---

## สรุป API ที่เชื่อมต่อ Home Assistant

| Django Endpoint | HA REST API | หน้าที่ |
|---|---|---|
| `/api/room-status/` | `GET /api/states/{entity_id}` | ดึงสถานะอุปกรณ์ |
| `/api/device-toggle/` | `POST /api/services/switch/toggle` | toggle เปิด/ปิด |
| `send_reminders` (auto-off) | `POST /api/services/switch/turn_off` | ปิดอัตโนมัติ |
| `morning_iot_report` | `GET /api/states/{entity_id}` | รายงานเช้า |
| `/manage/iot-monitor/control/` | `POST /api/services/switch/*` | Staff ควบคุม |

**Authentication:** `Authorization: Bearer {HA_TOKEN}` ทุก request
**Network:** Wi-Fi ภายในห้องสมุด (Django → HA → Sonoff อยู่ใน LAN เดียวกัน)

---

## อุปกรณ์ส่วนกลาง (RoomDevice ที่ `room = NULL`)

อุปกรณ์ที่ไม่สังกัดห้องจอง เช่น **flip gate ทางเข้า 3 ตัว** จับกลุ่มด้วย `group_name`
แสดงเป็นการ์ดแยกบนหน้า `/manage/iot-monitor/` ให้เจ้าหน้าที่กดเปิด-ปิดได้

- **ไม่ปรากฏในระบบจองใด ๆ** — `room_status()`, `device_toggle()` และ auto-off ใน `send_reminders`
  filter ด้วย `room=booking.room` ที่เป็นห้องจริงเสมอ อุปกรณ์กลุ่มจึงไม่เข้าเงื่อนไข
- **ตารางเวลาให้ Home Assistant automation คุมทั้งหมด** ฝั่ง Django ไม่มี logic เรื่องเวลา
  (flip gate: HA เปิด 07:20 ปิด 17:00 ต่างจากห้องจองที่ automation `Close ALL` ปิด 16:30)
- เพิ่ม-ลบอุปกรณ์กลุ่มผ่าน Django Admin (`/admin/`) เพราะไม่มีหน้าห้องให้จัดการ

เพิ่มเมื่อ 2026-07-17 (migration `0012`) — ดู `doc/progress-2026-07-17.md`
