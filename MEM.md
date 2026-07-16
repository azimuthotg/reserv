# MEM — reserv (ระบบจอง Smart Creative Learning Space)

คลังความรู้เฉพาะโปรเจกต์นี้ (ปัญหา/หมายเหตุ/การตัดสินใจ + changelog)
ทะเบียน "งานที่ต้องทำ" อยู่ในบล็อก `<!-- PROJECT-STATUS -->` ด้านบนของ CLAUDE.md — ไฟล์นี้ไว้เก็บ "ความรู้" เท่านั้น

## ปัญหา & วิธีแก้

### 2026-07-09 — ฟอนต์ไทยหายตอน export PDF
เวลาทำฟีเจอร์ export PDF (เช่น จากหน้า analytics) **ต้อง embed ฟอนต์ TH Sarabun New ใน PDF**
ไม่งั้นตัวอักษรไทยจะหาย/กลายเป็นกล่องว่าง

## การตัดสินใจ

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

### 2026-07-16
- ✅ day flow `/external/` — ปลดบังคับเลขบัตร (**แก้ครบ 2 ฝั่ง reserv+apiproject**):
  - (reserv) `external_access()` ใน [booking/views.py](booking/views.py) ตรวจ citizen_id เฉพาะเมื่อกรอกมา + omit key ออกจาก payload เมื่อว่าง, template [external.html](booking/templates/booking/external.html) ปลด `required` + label "ไม่บังคับ", เทส `ExternalAccessDayTests` 4 เคส (reserv 17/17)
  - (apiproject) `/v2/external/issue/` ทำ citizen_id optional + gen `V`-id เมื่อว่าง, เทสเพิ่ม 2 เคส (api 22/22) ดู changelog apiproject 2026-07-16
  - **ยังไม่ push/deploy ทั้ง 2 repo** — deploy: reserv `nssm restart reserv-booking`, apiproject `deploy.ps1` (recycle app pool)

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
