# ดัชนีเอกสาร — ระบบจองพื้นที่บริการ Smart Creative Learning Space

สำนักวิทยบริการ มหาวิทยาลัยนครพนม · production: https://lib.npu.ac.th/reserv/

> **กติกาของโฟลเดอร์นี้:** `doc/` ชั้นนอกเก็บเฉพาะเอกสารที่**ตรงกับระบบปัจจุบัน**
> ของเก่าที่ถูกแทนที่แล้วย้ายไป [`archive/`](archive/) ทั้งหมด — [อ่านคำเตือนใน archive/README.md ก่อนหยิบไปใช้](archive/README.md)

**อัปเดตล่าสุด: 8 สิงหาคม 2569**

---

## 1. เอกสารอ้างอิงสถานะระบบ (source of truth)

| ไฟล์ | ใช้ตอนไหน |
|---|---|
| [../CLAUDE.md](../CLAUDE.md) / [../AGENTS.md](../AGENTS.md) | ภาพรวมระบบ, URL, auth flow, models, policy — **อ่านก่อนเริ่มงานเสมอ** (บล็อก PROJECT-STATUS ด้านบน = ทะเบียนงานค้าง) |
| [../MEM.md](../MEM.md) | คลังความรู้: ปัญหา & วิธีแก้ · การตัดสินใจ · changelog |
| [deploy_guide.md](deploy_guide.md) | **คู่มือ deploy ฉบับจริง** — IIS + ARR, NSSM, WhiteNoise, พอร์ต 8003, ปัญหาที่เคยเจอ |
| [iot-flow.md](iot-flow.md) | flow ควบคุมอุปกรณ์: Django → Home Assistant → Sonoff รวมอุปกรณ์ส่วนกลาง (flip gate) |
| [line-richmenu-urls.md](line-richmenu-urls.md) | URL ทุกปุ่มใน LINE Rich Menu + สิ่งที่ต้องแก้เมื่อห้องเปลี่ยน |

### ห้องที่ให้บริการ ณ ปัจจุบัน

| `booking_name` | ชื่อแสดง | หมายเหตุ |
|---|---|---|
| `mini` | MINI THEATER | ชั้น 3 · มีอุปกรณ์ IoT 5 ตัว |
| `edutainment` | Edutainment Zone | ชั้น 3 · เดิมชื่อ key `netflix` |
| `canva` | Canva Pro 1 | ชั้น 1 · 🔗 VM Gateway |
| `canva2` | Canva Pro 2 | ชั้น 1 · 🔗 VM Gateway (เพิ่ม 8 ส.ค. 2569) |
| `netflix1_vm` | Netflix Pro | ออนไลน์ · 🔗 VM Gateway |
| `meeting_f1` | โต๊ะประชุมชั้น 1 | ชั้น 1 |
| ~~`chat-gpt`~~ | ~~ChatGPT~~ | 🚫 ปิดแล้ว 8 ส.ค. 2569 (`is_active=0` เก็บประวัติไว้) |

🔗 = `booking_name` เป็นกุญแจเชื่อมกับระบบ LRS ARC VM Gateway **ห้ามแก้โดยไม่แจ้งทีมพัฒนา**

---

## 2. คู่มือและรายงานฉบับใช้งาน

| ไฟล์ | เนื้อหา |
|---|---|
| [user-manual-reserv-2569.docx](user-manual-reserv-2569.docx) · [.pdf](user-manual-reserv-2569.pdf) | **คู่มือผู้ใช้ 2569** — 15 บท มือถือ+เว็บ ภาพจาก production สารบัญมีเลขหน้า |
| [staff-manual-2569.docx](staff-manual-2569.docx) | **คู่มือเจ้าหน้าที่ 2569** — 15 บท Staff Portal ฟีเจอร์เต็ม |
| [external-access-report.docx](external-access-report.docx) · [.pdf](external-access-report.pdf) | **รายงานประกอบการประชุม** — ระบบบุคคลภายนอก + ช่องทาง `/card-login/` (6 บท) |
| [door-qr-guide.docx](door-qr-guide.docx) · [.pdf](door-qr-guide.pdf) | คู่มือช่องทางขอ QR เข้าประตู สรุป 4 ช่องทาง A–D |
| [reply-vm-gateway-2026-08-08.md](reply-vm-gateway-2026-08-08.md) | หนังสือตอบกลับทีม VM Gateway — ยืนยัน `booking_name = canva2` |

> ⚠️ คู่มือทั้ง 2 เล่ม **ยังไม่มี Canva Pro 2 และ Netflix Pro** — เป็นงานค้างใน PROJECT-STATUS

---

## 3. Scripts ที่ยังใช้อยู่

| Script | สร้าง/ทำอะไร |
|---|---|
| [manual_style.py](manual_style.py) | สไตล์กลางของ .docx ชุด 2569 (ฟอนต์ไทย `w:cs`, TOC field มีเลขหน้า) |
| [make_user_manual_2569.py](make_user_manual_2569.py) | คู่มือผู้ใช้ 2569 — ⚠️ **ยังไม่ sync กับ .docx ที่แก้ด้วย Word รันทับแล้วงานหาย** |
| [make_staff_manual_2569.py](make_staff_manual_2569.py) | คู่มือเจ้าหน้าที่ 2569 (ใช้ภาพจาก `screenshots/manual2026/`) |
| [make_external_report_docx.py](make_external_report_docx.py) | รายงานประกอบการประชุมเรื่องบุคคลภายนอก |
| [fix_manual_toc.py](fix_manual_toc.py) | แพตช์สารบัญ .docx ที่มีอยู่แล้วให้มีเลขหน้า โดยไม่ต้องสร้างใหม่ |
| [compose_mobile_figures.py](compose_mobile_figures.py) | รวมภาพมือถือ 9:16 เป็นภาพประกอบกรอบ 16:9 |
| [capture_external_shots.py](capture_external_shots.py) | แคปหน้าจอ external จาก production 1920×1080 (ต้องมี `STAFF_USER`/`STAFF_PASS`) |
| [check_booking_form.py](check_booking_form.py) | ตรวจกติกาเวลาในฟอร์มจอง LIFF บน production (Playwright headed — ล็อกอิน LINE เองครั้งแรก · อ่านอย่างเดียว) |

---

## 4. Progress log (บันทึกรายวัน — เรียงใหม่ไปเก่า)

ไฟล์เหล่านี้เป็น**บันทึกประวัติ** ไม่ใช่คำอธิบายสถานะปัจจุบัน อ่านเพื่อสืบว่า "ทำไมถึงเป็นแบบนี้"

| วันที่ | ไฟล์ | งานหลัก |
|---|---|---|
| 8 ส.ค. 69 | [progress-2026-08-08.md](progress-2026-08-08.md) | เพิ่ม Canva Pro 2 · ปิด ChatGPT · จัดระเบียบห้อง Netflix Pro |
| 7 ส.ค. 69 | [progress-2026-08-07.md](progress-2026-08-07.md) | ตรวจเอกสารชุดบุคคลภายนอกเทียบ code + แปลงเป็นรายงานประกอบการประชุม |
| 2 ส.ค. 69 | [progress-2026-08-02.md](progress-2026-08-02.md) | สารบัญคู่มือเป็น TOC field มีเลขหน้า |
| 31 ก.ค. 69 | [progress-2026-07-31.md](progress-2026-07-31.md) | คู่มือ 2 เล่ม ภาพจาก production จริง 16:9 |
| 20–22 ก.ค. 69 | [progress-2026-07-20-card-login.md](progress-2026-07-20-card-login.md) | หน้า `/card-login/` ออก QR เข้าประตูโดยไม่ต้องมี LINE |
| 17 ก.ค. 69 | [progress-2026-07-17.md](progress-2026-07-17.md) | อุปกรณ์ส่วนกลาง (flip gate) ในหน้า IoT Monitor |
| 10 ก.ค. 69 | [progress-2026-07-10.md](progress-2026-07-10.md) | สมาชิกถาวรไม่บังคับเลขบัตร (รองรับ VVIP) |
| 9 ก.ค. 69 | [progress-2026-07-09.md](progress-2026-07-09.md) | Staff Portal analytics + งานชุดใหญ่ |
| 21 มิ.ย. 69 | [progress-2026-06-21.md](progress-2026-06-21.md) | ระบบบุคคลภายนอกรายวัน `/external/` ขึ้น prod |
| 18 มิ.ย. 69 | [progress-2026-06-18.md](progress-2026-06-18.md) | งานแก้ไขระหว่างทาง |
| 7 มิ.ย. 69 | [progress-2026-06-07.md](progress-2026-06-07.md) | health endpoint `/health/` สำหรับ NMS |
| 6 มิ.ย. 69 | [progress-2026-06-06.md](progress-2026-06-06.md) | สร้าง INDEX.md ครั้งแรก |
| 3 มิ.ย. 69 | [progress-2026-06-03.md](progress-2026-06-03.md) | คู่มือ workflow การเจนภาพ |
| 2 มิ.ย. 69 | [progress-2026-06-02.md](progress-2026-06-02.md) | Docs sync, policy เสาร์-อาทิตย์, จองล่วงหน้า 7 วันบริการ |
| 11 พ.ค. 69 | [progress-2026-05-11.md](progress-2026-05-11.md) | Poster v2 |
| 8 พ.ค. 69 | [progress-2026-05-08.md](progress-2026-05-08.md) | LINE Flex Messages ครบทุก event |
| 28 เม.ย. 69 | [progress-2026-04-28.md](progress-2026-04-28.md) | IoT Device Control, Daily Schedule |
| 26 เม.ย. 69 | [progress-2026-04-26.md](progress-2026-04-26.md) | RoomClosure, Virtual Card UI, IoT Monitor |
| 24 เม.ย. 69 | [progress-2026-04-24.md](progress-2026-04-24.md) | Check-in / Auto-cancel |
| 21 เม.ย. 69 | [progress-2026-04-21.md](progress-2026-04-21.md) | ฟิลด์รายละเอียดห้อง, หน้า Room Detail |

---

## 5. Assets

| โฟลเดอร์ | เนื้อหา |
|---|---|
| [screenshots/manual2026/](screenshots/) | ภาพหน้าจอชุดที่คู่มือ 2569 ใช้จริง |
| `screenshots/` (ไฟล์ `user_*`, `real_*`, `admin_*`, `01_*`–`08_*`) | ภาพชุดเก่าของคู่มือรุ่นก่อน — เก็บไว้เผื่ออ้างอิง |
| [illustrations/](illustrations/) | โลโก้ NPU / ARC, QR Code LINE OA, QR Code เว็บ |
| [imgIP3/](imgIP3/) | ภาพอุปกรณ์ IoT — Sonoff, IP3 block diagram |
| [iot-visuals/](iot-visuals/) | ภาพ IoT infrastructure / user flow / automation |

---

## 6. เอกสารที่ไม่เกี่ยวกับสถานะระบบ

| โฟลเดอร์ | เนื้อหา |
|---|---|
| [Report Improvement Plan/](Report%20Improvement%20Plan/) | งานเขียนเชิงวิชาการ/แผนปรับปรุงรายงาน — ไม่ใช่เอกสารระบบ |
| [archive/](archive/) | เอกสารเวอร์ชันเก่าทั้งหมด — **ห้ามใช้อ้างอิงสถานะปัจจุบัน** |
