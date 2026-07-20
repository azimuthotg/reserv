# MEM — reserv (ระบบจอง Smart Creative Learning Space)

คลังความรู้เฉพาะโปรเจกต์นี้ (ปัญหา/หมายเหตุ/การตัดสินใจ + changelog)
ทะเบียน "งานที่ต้องทำ" อยู่ในบล็อก `<!-- PROJECT-STATUS -->` ด้านบนของ CLAUDE.md — ไฟล์นี้ไว้เก็บ "ความรู้" เท่านั้น

## ปัญหา & วิธีแก้

### 2026-07-17 — ⚠️ `.env` ในเครื่อง dev ชี้ MySQL production จริง (กับดัก)
`.env` ชี้ `DB_HOST=202.29.55.213 / reserv_db` ซึ่งเป็น **ฐานเดียวกับที่ production ใช้**
(ยืนยันแล้ว: prod มองเห็นข้อมูลที่เขียนจากเครื่อง dev) → `python manage.py migrate` บนเครื่อง dev
**ลงฐาน production ทันที** ไม่มี DB ทดสอบแยก
**บทเรียน:** ก่อนรัน `migrate`/สคริปต์เขียนข้อมูลบนเครื่อง dev ให้เช็ค `settings.DATABASES['default']['HOST']` ก่อนเสมอ
และเช็คว่ามี migration ค้างที่ยังไม่ตั้งใจ apply หรือไม่ด้วย (`python manage.py showmigrations booking`)
**เคสจริง:** 2026-07-17 ตอน migrate ฟีเจอร์อุปกรณ์ส่วนกลาง มี `0011_update_room_hours` ค้างอยู่ก่อนแล้ว
เลยถูก apply ไปด้วย — มันสั่ง `Room.objects.all().update(open_time=08:30, close_time=16:30)` **ทุกห้อง**
ผลตรงกับเวลาบริการวันธรรมดาใน CLAUDE.md อยู่แล้วจึงไม่เสียหาย แต่**กู้ค่าเดิมไม่ได้**
**ผลพลอยได้:** ตอน deploy ฟีเจอร์ที่มี migration จากเครื่องนี้ **ไม่ต้องรัน migrate บนเซิร์ฟเวอร์**
เพราะฐานถูก migrate ไปแล้ว — แค่ `git pull` + `nssm restart reserv-booking`
**หมายเหตุ:** PROJECT-STATUS เดิมเขียน `deploy_db` เป็น `202.29.55.217` (api.npu.ac.th) ซึ่งไม่ตรงกับ `.env` จริง — แก้เป็น `.213` แล้ว 2026-07-17

### 2026-07-09 — ฟอนต์ไทยหายตอน export PDF
เวลาทำฟีเจอร์ export PDF (เช่น จากหน้า analytics) **ต้อง embed ฟอนต์ TH Sarabun New ใน PDF**
ไม่งั้นตัวอักษรไทยจะหาย/กลายเป็นกล่องว่าง

## การตัดสินใจ

### 2026-07-17 — อุปกรณ์ที่ไม่สังกัดห้อง = "อุปกรณ์ส่วนกลาง" ไม่ใช่ Room ปลอม
flip gate (ประตูทางเข้า) ไม่สังกัดห้องจองใด เลือกทำเป็น `RoomDevice` ที่ `room=None` + `group_name`
แทนการสร้าง `Room` ปลอมมารองรับ
**เหตุผล:** `Room` ลาก `open_time`/`close_time` ติดมาด้วย ซึ่งเวลาใน Room มีความหมายกับ "การจอง" เท่านั้น
แต่ flip gate มีตารางของตัวเองใน HA (เปิด 07:20 ปิด 17:00) ต่างจากห้องจอง (automation `Close ALL` ปิด 16:30
และ **ไม่แตะ gate**) ถ้าเป็น Room จะได้เวลาที่ไม่ตรงความจริงติดมา แถมโผล่ในหน้าจอง/ปฏิทิน/สถิติโดยไม่จำเป็น
**ขอบเขต:** ฝั่ง Django **ไม่มี logic เรื่องเวลาของอุปกรณ์ส่วนกลางเลย** — ปล่อยให้ HA automation คุมทั้งหมด
หน้า `/manage/iot-monitor/` ทำแค่ดูสถานะ + ให้ staff override ด้วยมือ
**ถ้าจะเพิ่มอุปกรณ์ส่วนกลางตัวใหม่:** เพิ่มผ่าน Django Admin (`/admin/`) ตั้ง `room` ว่าง + `group_name`
ไม่ต้องแก้โค้ด — หน้า monitor จับกลุ่มให้เอง (หน้า `manage_room_devices` ใช้ไม่ได้เพราะเป็นหน้าราย "ห้อง")

### 2026-07-16 — day flow (/external/): บังคับชื่อ-สกุล, เลขบัตรเป็น optional
เลือกแนวทาง B (เลขบัตร optional) แทนแนวทาง A (รวมโมเดล คีย์ด้วยเลขบัตร แบบ permanent)
**เหตุผล:** เอาสะดวกผู้ใช้ก่อน ยอมเสียความสามารถ **บล็อกคนถูกระงับ (403)** และ **จำกัดโควตารายวัน (503)**
ซึ่งทั้งสองอย่างต้องพึ่ง citizen_id เป็น key (ชื่อ-สกุลใช้เป็น key ไม่ได้ — ซ้ำ/พิมพ์ต่างได้ง่าย)
**แผนถอย:** ถ้าเจอสแปม/คนถูกแบนวนกลับมาจริง → กลับมาบังคับเลขบัตร (revert diff รอบนี้)

**✅ Dependency ฝั่ง api (แก้แล้ว 2026-07-16):** `POST /v2/external/issue/` ยอมออกรหัสเมื่อ **ไม่ส่ง**
`citizen_id` แล้ว — api gen `V`+12 หลักให้ (mirror permanent_register) reserv omit key นี้เมื่อผู้ใช้เว้นว่าง
ดู changelog apiproject 2026-07-16 · **trade-off:** anonymous ไม่ dedupe → กินสล็อต pool ทุกครั้ง
(default 100/วัน ขยายด้วย `python manage.py seed_access_codes --count N` ฝั่ง api)

## บันทึกงานที่ทำ (changelog)

### 2026-07-20
- ✅ **หน้าแก้ไขชื่อ-สกุลสมาชิกถาวร** `/manage/external/<citizen_id>/edit/` (deploy + เทส prod ผ่านแล้ว)
  - `manage_external_edit()` ใน [booking/manage_views.py](booking/manage_views.py): GET ดึงข้อมูลปัจจุบันจาก
    api มาเติมฟอร์ม, POST proxy ไป `/v2/external/permanent/<id>/update/` — reserv ไม่เก็บข้อมูลสมาชิกเอง
    (api = source of truth) เหมือน view external อื่นในไฟล์เดียวกัน
  - template ใหม่ [external_edit.html](booking/templates/booking/manage/external_edit.html) — ช่องรูป
    **ไม่บังคับ** (เว้นว่าง = ใช้รูปเดิม) ต่างจากหน้าลงทะเบียนที่บังคับ, แสดงรูปปัจจุบันให้เห็นก่อนเปลี่ยน
  - เพิ่มปุ่ม "แก้ไข" ในหน้ารายละเอียดสมาชิก + route ใน [booking/urls.py](booking/urls.py)
  - push `379d456` → origin/master · จับคู่กับ apiproject `e14897d`
  - ⚠️ ยังไม่มี test ของหน้านี้ (ผ่านแค่ `manage.py check` + เทสมือบน prod)

### 2026-07-17
- ✅ **อุปกรณ์ส่วนกลางในหน้า IoT Monitor — flip gate 1-3** (deploy + เทส prod ผ่านแล้ว)
  ดูรายละเอียดครบใน [doc/progress-2026-07-17.md](doc/progress-2026-07-17.md)
  - `RoomDevice.room` ให้ว่างได้ + เพิ่ม `group_name` (migration `0012`), รวม logic จัดกลุ่มไว้ที่
    helper กลาง `_iot_cards()` ใน [booking/manage_views.py](booking/manage_views.py) แล้วให้หน้า monitor,
    refresh, แจ้งกลุ่ม LINE และ `morning_iot_report` ใช้ร่วมกัน (เดิม 4 จุดต่างคนต่าง loop ห้องเอง)
  - ลงทะเบียน `RoomDevice` ใน Django Admin (เดิมไม่มี) เพื่อจัดการอุปกรณ์กลุ่มที่ไม่มีหน้าห้อง
  - push แล้ว: `be97232` (ฟีเจอร์) + `6fc7113` (คำบรรยายหน้า) → `origin/master`
- 📌 **entity_id ของ flip gate** (Sonoff S40TPB Lite, HA area `flip gate` บน floor `ชั้น1`):
  gate1 `switch.sonoff_10018d4dfb_1` · gate2 `switch.sonoff_10018d50d7_1` · gate3 `switch.sonoff_10018d5622_1`
  — HA automation `start flip gate` เปิด 07:20 / `stop flip gate` ปิด 17:00 (ดูโปรเจกต์ `C:\projects\ha`)
- ⚠️ **key ของการ์ดกลุ่มใช้ md5 ย่อ ไม่ใช่ slugify** — `slugify(name, allow_unicode=True)` **ตัดสระ/วรรณยุกต์ไทยทิ้ง**
  (`อุปกรณ์ส่วนกลาง` → `อปกรณสวนกลาง`) ชื่อที่ต่างกันจึงเหลือ slug เดียวกันได้ ระวังถ้าจะใช้ slugify กับข้อความไทยที่อื่น
- ⚠️ **JSON ของ `/manage/iot-monitor/refresh/` เปลี่ยน shape** — จาก `{rooms:[{room_name, room_key,…}]}`
  เป็น `{cards:[{name, key,…}]}` (ตรวจแล้วไม่มี consumer อื่นนอกจากหน้า monitor)

### 2026-07-16
- ✅ day flow `/external/` — ปลดบังคับเลขบัตร (**แก้ครบ 2 ฝั่ง reserv+apiproject**):
  - (reserv) `external_access()` ใน [booking/views.py](booking/views.py) ตรวจ citizen_id เฉพาะเมื่อกรอกมา + omit key ออกจาก payload เมื่อว่าง, template [external.html](booking/templates/booking/external.html) ปลด `required` + label "ไม่บังคับ", เทส `ExternalAccessDayTests` 4 เคส (reserv 17/17)
  - (apiproject) `/v2/external/issue/` ทำ citizen_id optional + gen `V`-id เมื่อว่าง, เทสเพิ่ม 2 เคส (api 22/22) ดู changelog apiproject 2026-07-16
  - push แล้วทั้ง 2 repo (reserv `336d4e2` → origin/master, apiproject `2ad5701` → origin/main)
  - ✅ **deploy prod + restart + เทส prod ผ่าน** (apiproject ก่อน → reserv) — รายวันกรอกแค่ชื่อ-สกุลได้ QR สมบูรณ์
- ✅ **ทีมประตูเทส QR จริงผ่านแล้วทั้ง 2 แบบ (รายวัน + ถาวร)** — QR ออกสมบูรณ์และสแกนเข้าประตูได้จริง ปิดงาน external access **ครบวงจร** (task ค้างตั้งแต่ 2026-07-12: ส่ง JSON `/v2/external/check/` ให้ทีมประตู → ทีมประตูเขียนโค้ดรับ → เทสจริงผ่าน)
- ✅ อัปเดตคู่มือแจ้งเจ้าหน้าที่ v1.0 → **v1.1** ให้ตรงพฤติกรรมใหม่ — แก้ [doc/make_external_manual_docx.py](doc/make_external_manual_docx.py) แล้ว regenerate [doc/external-access-manual.docx](doc/external-access-manual.docx): ตารางเปรียบเทียบเพิ่มแถวเลขบัตรบังคับ/ไม่บังคับ, บท 2 ขั้นตอน+info box อธิบายข้อแลกเปลี่ยน, ตาราง error, FAQ ข้อใหม่ "รายวันต้องกรอกเลขบัตรไหม"
- 📌 ทำชุดข้อมูล/prompt ให้ผู้ใช้เอาไปสร้าง infographic 2 ภาพ (รายวัน/ถาวร) ที่ ChatGPT — **ข้อควรระวัง:** image gen ของ ChatGPT เขียนภาษาไทยเพี้ยน แนะนำสร้างเลย์เอาต์เปล่าแล้วใส่ข้อความไทยเองใน Canva/PowerPoint หรือให้ทำเป็น HTML/SVG แทน

### 2026-07-13
- ✅ ส่งตัวอย่าง JSON response ของ endpoint `/v2/external/check/` ให้ทีมประตูแล้ว (รับแจ้งงาน 2026-07-12) — ทีมประตูเอาไปเขียนโค้ดรับค่าฝั่งเขาต่อ เหลืองานเดียวจากรอบนี้: ทีมประตูทดสอบ QR code เข้าจริง
- ✅ ทำคู่มือแจ้งเจ้าหน้าที่ — ระบบบุคคลภายนอกเข้าใช้บริการ (External Access): [doc/external-access-manual.docx](doc/external-access-manual.docx) — ครอบคลุมทั้ง 2 เส้นทาง (QR รายวัน /external/ + สมาชิกถาวร /external/permanent/) ฝั่งผู้ใช้และฝั่งเจ้าหน้าที่ที่ /manage/external/ สร้างด้วยสคริปต์ [doc/make_external_manual_docx.py](doc/make_external_manual_docx.py) (python-docx) แก้เนื้อหาแล้วรันซ้ำได้

### 2026-07-10
- ✅ สมาชิกถาวรไม่บังคับเลขบัตร (รองรับ VVIP เช่น นายกสภาฯ) — เว้นว่างแล้ว api gen รหัสอ้างอิง `V`+12 หลัก, แก้ 2 ฝั่ง (reserv+apiproject) ไม่มี endpoint ใหม่/ไม่มี migration, test reserv 13/13 + api 10/10 — commit แล้วทั้ง 2 repo แต่ **push ค้าง** (GitHub token ใน WSL หมดอายุ) — รอ push + deploy prod + e2e
- ✅ push ค้าง 2 repo แก้แล้ว โดย push จากฝั่ง Windows แทน WSL (token หมดอายุ) — reserv `38dc88e..369369e`, apiproject `54de5ee..8779351`
- ✅ deploy prod ทั้ง reserv+apiproject (git pull+restart) เรียบร้อย, เทส prod ผ่านหมด — ฟีเจอร์ VVIP ไม่บังคับเลขบัตรทำงานถูกต้องบน production
- เหลืองานเดียว: แจ้งทีมประตูเอา QR code ไปทดสอบว่าเข้าได้จริงหรือไม่ (route `/v2/external/check/` ฝั่ง api พร้อมรอแล้ว)

## ปัญหา & วิธีแก้ (เพิ่มเติม)

### 2026-07-10 — push GitHub จาก WSL ไม่ได้
token ใน `/root/.git-credentials` (WSL) หมดอายุ/ถูก revoke — GitHub ตอบ "Invalid username or token"
ทางแก้: สร้าง PAT ใหม่ (สิทธิ์ `repo`) แล้วอัปเดต credential store หรือ push จากฝั่ง Windows ที่ใช้ Git Credential Manager แยกกัน

### 2026-07-09
- ✅ จำกัดการจอง 1 ครั้ง/ห้อง/วัน (prod verified) — `create_booking()` + `booking/tests.py`
- ✅ หน้าวิเคราะห์การจอง `/manage/analytics/` (prod verified) — utilization, ผู้ใช้จองถี่, no-show จาก auto-cancel log, ยกเลิกโดยผู้ใช้, แนวโน้มรายวัน
- ✅ cosmetic external member (prod verified) — `approved_by` ชื่อ staff จริง (แก้ 2 ฝั่ง reserv+api) + `approved_at` เวลาไทย + ปุ่ม "ลบ" (hard delete ครบ 3 ชั้น)
- ✅ เก็บเอกสารเข้า repo — คู่มือ admin v2 (docx+pdf) + โฟลเดอร์ Report Improvement Plan
