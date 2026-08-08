# System Architecture Flow
## ระบบจองพื้นที่บริการ Smart Creative Learning Space
### สำนักวิทยบริการ มหาวิทยาลัยนครพนม

---

## ระบบเดิม (Before)

```
┌─────────────────────────────────────────────────────────────┐
│                      ระบบเดิม (Before)                      │
│               Google Cloud + External Hosting               │
└─────────────────────────────────────────────────────────────┘

ผู้ใช้ใน LINE OA
    ↓ กด Flex Message Card → เปิด LIFF
    ↓ โหลด netflix.html (arc.npu.ac.th)

testdb.php (external server)
    ↓ ตรวจว่าผูกบัญชี LINE ไว้ไหม
    │
    ├── ❌ ยังไม่ผูก
    │       ↓ redirect หน้าผูกบัญชี
    │       ↓ กรอก User/Pass อินเทอร์เน็ต
    │       ↓ ตรวจสอบ LDAP / AD มหาวิทยาลัย
    │       ↓ บันทึกผูก LINE userId ↔ account
    │       ↓ กลับมาที่ฟอร์มจอง
    │
    └── ✅ ผูกแล้ว
            ↓ ดึงข้อมูลผู้ใช้จาก LDAP / AD

HTML Form (netflix.html — arc.npu.ac.th)
    ↓ ผู้ใช้กรอกข้อมูลการจอง

Google Apps Script (Web App)
    ↓ ตรวจ conflict check (query Google Sheets)
    │
    ├── ❌ มี conflict → แจ้งผู้ใช้ (จองไม่ได้)
    │
    └── ✅ ไม่มี conflict
            ↓ บันทึกลง Google Sheets
            ↓ เพิ่ม event ใน Google Calendar
            ↓ ส่ง LINE Notify แจ้งผู้จอง

┌──────────────────────────────────────────────┐
│  External Services (ทั้งหมดอยู่นอกองค์กร)    │
│  • Google Sheets    — ฐานข้อมูลการจอง        │
│  • Google Calendar  — แสดงการจองที่สำเร็จ    │
│  • LINE Notify      — แจ้งเตือนผู้จอง        │
│    ⚠ ติด limit 300 msg/เดือน                 │
│    ⚠ ปิดบริการถาวร เมษายน 2568              │
└──────────────────────────────────────────────┘
```

---

## ระบบใหม่ (After)

```
┌─────────────────────────────────────────────────────────────┐
│                      ระบบใหม่ (After)                       │
│                  On-premise — Windows Server                │
└─────────────────────────────────────────────────────────────┘

     ช่องทางที่ 1                      ช่องทางที่ 2
   LINE OA (มือถือ)              เว็บไซต์ (Desktop/Browser)
         ↓                                ↓
  กด "จองห้อง"               https://lib.npu.ac.th/reserv/
  ใน Rich Menu                     login LDAP
         ↓                                ↓
         └──────────────┬─────────────────┘
                        ↓
             IIS ARR (lib.npu.ac.th)
             Reverse Proxy → port 8003
                        ↓
             Waitress WSGI Server
                        ↓
             Django Application
                        ↓
         ตรวจสอบ session / LINE userId
         │
         ├── ❌ ยังไม่ผูกบัญชี
         │       ↓ redirect หน้าลงทะเบียน
         │       ↓ กรอก User/Pass LDAP
         │       ↓ ตรวจสอบผ่าน api.npu.ac.th
         │       ↓ บันทึก LineUser ใน MySQL
         │       ↓ กลับมาที่ฟอร์มจอง
         │
         └── ✅ ผูกแล้ว
                 ↓ ดึงโปรไฟล์จาก cache (MySQL)
                   หรือ api.npu.ac.th ถ้า cache หมดอายุ

HTML Form (Django Template — LIFF / Browser)
    ↓ ผู้ใช้กรอกข้อมูลการจอง

Django View — create_booking()
    ↓ SELECT FOR UPDATE + transaction.atomic()
    ↓ ตรวจ conflict check (MySQL)
    │
    ├── ❌ มี conflict → แจ้งผู้ใช้ (จองไม่ได้)
    │
    └── ✅ ไม่มี conflict
            ↓ บันทึกลง MySQL (booking_booking)
            ↓ บันทึก BookingLog (audit trail)
            ↓ ส่ง LINE Messaging API → แจ้งผู้จองทันที

Windows Task Scheduler (ทุก 1 นาที)
    ↓ send_reminders command
    ↓ แจ้งเตือนก่อนเริ่ม 15 นาที
    ↓ แจ้งเตือนก่อนหมด 10 นาที

Home Assistant + Sonoff Smart Plug
    ↓ /api/check-access/ (X-HA-Token)
    ↓ เปิด/ปิดอุปกรณ์ในห้องอัตโนมัติ

┌──────────────────────────────────────────────┐
│  Internal Services (ทั้งหมดอยู่ในองค์กร)     │
│  • MySQL 8.0        — ฐานข้อมูลการจอง        │
│  • Django Admin     — จัดการระบบ (Staff)     │
│  • BookingLog       — audit trail ทุก action  │
│  • NSSM             — Windows Service         │
└──────────────────────────────────────────────┘
│  External APIs (เฉพาะที่จำเป็น)              │
│  • api.npu.ac.th    — ตรวจสิทธิ์ + โปรไฟล์  │
│  • LINE Messaging API — push notification     │
└──────────────────────────────────────────────┘
```

---

## เปรียบเทียบจุดเปลี่ยนสำคัญ

| จุด | ระบบเดิม | ระบบใหม่ |
|---|---|---|
| ฐานข้อมูล | Google Sheets (cloud) | MySQL on-premise |
| Conflict check | Google Apps Script | SELECT FOR UPDATE (MySQL) |
| Auth | testdb.php (external) | api.npu.ac.th + cache |
| แจ้งเตือน | LINE Notify (limit/ปิดแล้ว) | LINE Messaging API |
| ช่องทางจอง | LINE LIFF เท่านั้น | LINE LIFF + เว็บไซต์ |
| ปฏิทิน | Google Calendar | FullCalendar (on-premise) |
| Audit Trail | ไม่มี | BookingLog ทุก action |
| IoT | ไม่มี | Sonoff + Home Assistant |
