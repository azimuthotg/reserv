# ดัชนีเอกสารโครงการ — ระบบจองพื้นที่ Smart Creative Learning Space

ระบบจองพื้นที่บริการ — สำนักวิทยบริการ มหาวิทยาลัยนครพนม
ไฟล์นี้รวบรวม link ทุกเอกสารในโฟลเดอร์ `doc/`

---

## Timeline การพัฒนา (12 วัน)

| วันที่ | ไฟล์ | งานหลัก |
|---|---|---|
| 21 เม.ย. 69 | [progress-2026-04-21.md](progress-2026-04-21.md) | เพิ่มฟิลด์รายละเอียดห้อง, หน้า Room Detail, Room Form ใหม่ |
| 24 เม.ย. 69 | [progress-2026-04-24.md](progress-2026-04-24.md) | ระบบ Check-in / Auto-cancel, LINE Button Template, ปุ่มยกเลิกตามสถานะ |
| 26 เม.ย. 69 | [progress-2026-04-26.md](progress-2026-04-26.md) | RoomClosure, วันหยุดในปฏิทิน, Virtual Card UI, IoT Monitor |
| 28 เม.ย. 69 | [progress-2026-04-28.md](progress-2026-04-28.md) | IoT Device Control, toggle switch, Daily Schedule Gantt, th_filters พ.ศ. |
| 8 พ.ค. 69 | [progress-2026-05-08.md](progress-2026-05-08.md) | LINE Flex Messages ครบทุก event, Bug fix 6 รายการ, Code Review รอบสุดท้าย |
| 11 พ.ค. 69 | [progress-2026-05-11.md](progress-2026-05-11.md) | Poster v2 อัปเดต 2 ช่องทางจอง, สร้าง PNG ด้วย Pillow |
| 2 มิ.ย. 69 | [progress-2026-06-02.md](progress-2026-06-02.md) | Docs sync, Code Fix 1–5, Policy วันเสาร์–อาทิตย์, จองล่วงหน้า 7 วันบริการ |
| 3 มิ.ย. 69 | [progress-2026-06-03.md](progress-2026-06-03.md) | คู่มือ workflow การเจนภาพและผลิตป้ายประชาสัมพันธ์ |
| 6 มิ.ย. 69 | [progress-2026-06-06.md](progress-2026-06-06.md) | สร้าง INDEX.md, Notion Projects Hub, Global skill /update-docs |
| 7 มิ.ย. 69 | [progress-2026-06-07.md](progress-2026-06-07.md) | เพิ่ม health endpoint `/health/` สำหรับ NMS Agent monitoring |
| 31 ก.ค. 69 | [progress-2026-07-31.md](progress-2026-07-31.md) | คู่มือ 2 เล่ม (ผู้ใช้ + เจ้าหน้าที่) ภาพจาก production จริง 16:9 |
| 2 ส.ค. 69 | [progress-2026-08-02.md](progress-2026-08-02.md) | สารบัญคู่มือเป็น TOC field มีเลขหน้า + เริ่มนับหน้า 1 ที่บทที่ 1 |
| 7 ส.ค. 69 | [progress-2026-08-07.md](progress-2026-08-07.md) | ตรวจเอกสารชุดบุคคลภายนอกเทียบ code + แปลงคู่มือ external เป็นรายงานประกอบการประชุม |

---

## คู่มือการใช้งาน

| ไฟล์ | รูปแบบ | เนื้อหา |
|---|---|---|
| [user-manual.md](user-manual.md) | Markdown | คู่มือผู้ใช้ทั่วไป (ต้นฉบับแก้ไขได้) |
| [user-manual.docx](user-manual.docx) | Word | คู่มือผู้ใช้ฉบับพิมพ์/แจกทีม |
| [user-manual-v1.docx](user-manual-v1.docx) | Word | คู่มือผู้ใช้ version 1 |
| [admin-manual.md](admin-manual.md) | Markdown | คู่มือผู้ดูแลระบบ (ต้นฉบับแก้ไขได้) |
| [admin-manual.docx](admin-manual.docx) | Word | คู่มือผู้ดูแลระบบฉบับพิมพ์/แจกทีม |
| [admin-manual-v2.docx](admin-manual-v2.docx) | Word | คู่มือผู้ดูแลระบบ version 2 |
| [user-manual-reserv-2569.docx](user-manual-reserv-2569.docx) | Word | **คู่มือผู้ใช้ 2569 (ล่าสุด)** — 15 บท ครอบคลุมมือถือ+เว็บ ภาพจาก production จริง · สารบัญมีเลขหน้า เริ่มนับหน้า 1 ที่บทที่ 1 |
| [staff-manual-2569.docx](staff-manual-2569.docx) | Word | **คู่มือเจ้าหน้าที่ 2569 (ล่าสุด)** — 15 บท Staff Portal ฟีเจอร์เต็ม |

---

## รายงานและเอกสารทางการ

| ไฟล์ | เนื้อหา |
|---|---|
| [development_report.md](development_report.md) | รายงานการพัฒนาระบบ (ต้นฉบับ) |
| [report-management-2568.md](report-management-2568.md) | รายงานบริหารจัดการ ปี 2568 (ต้นฉบับ) |
| [report-management-2568.docx](report-management-2568.docx) | รายงานบริหารจัดการ ปี 2568 (Word) |
| [external-access-report.docx](external-access-report.docx) | **รายงานประกอบการประชุม (ล่าสุด)** — ระบบบุคคลภายนอกเข้าใช้บริการ + ช่องทาง `/card-login/` ของนักศึกษา-บุคลากร · 6 บท ภาพ 16:9 จาก production · ไม่มีสารบัญ |
| [door-qr-guide.docx](door-qr-guide.docx) | คู่มือช่องทางขอ QR เข้าประตู สรุป 4 ช่องทาง A–D |
| [Report Improvement Plan/improvement plan.docx](Report%20Improvement%20Plan/improvement%20plan.docx) | แผนปรับปรุงรายงาน |

---

## สื่อประชาสัมพันธ์

### โปสเตอร์และป้าย

| ไฟล์ | เนื้อหา |
|---|---|
| [poster-plan.md](poster-plan.md) | แผนงานชุดป้าย 8 แบบ + checklist วัตถุดิบ |
| [promo-signage-plan.md](promo-signage-plan.md) | แผนงานป้ายประชาสัมพันธ์รวม |
| [poster-content.md](poster-content.md) | ต้นฉบับเนื้อหาโปสเตอร์ (Markdown แก้ไขได้) |
| [poster-content.txt](poster-content.txt) | ต้นฉบับเนื้อหาโปสเตอร์ (plain text) |
| [poster-booking-guide.html](poster-booking-guide.html) | ต้นฉบับโปสเตอร์แบบ HTML preview |
| [poster-v2.png](poster-v2.png) | โปสเตอร์ v2 — A4, dark mode, LINE green |
| [poster-v2-philosophy.md](poster-v2-philosophy.md) | Visual Philosophy "Neon Meridian" |

### Infographic

| ไฟล์ | เนื้อหา |
|---|---|
| [infographic-1-system-overview.md](infographic-1-system-overview.md) | Infographic ภาพรวมระบบ (ต้นฉบับ) |
| [infographic-2-steps-rules.md](infographic-2-steps-rules.md) | Infographic ขั้นตอนและกฎการจอง (ต้นฉบับ) |
| [image-generation-workflow-infographic.png](image-generation-workflow-infographic.png) | Infographic สรุป workflow การเจนภาพ |

### คู่มือการผลิตภาพและป้าย

| ไฟล์ | เนื้อหา |
|---|---|
| [image-generation-workflow-guide.md](image-generation-workflow-guide.md) | คู่มือ workflow เจนภาพ + กติกาสั่งงาน (ต้นฉบับ) |
| [image-generation-workflow-guide.docx](image-generation-workflow-guide.docx) | คู่มือ workflow เจนภาพ (Word แจกทีม) |

---

## เอกสารเทคนิค

| ไฟล์ | เนื้อหา |
|---|---|
| [architecture-flow.md](architecture-flow.md) | สถาปัตยกรรมระบบและ flow ข้อมูล |
| [iot-flow.md](iot-flow.md) | IoT flow — Django → Home Assistant → อุปกรณ์ |
| [deploy_guide.md](deploy_guide.md) | คู่มือ deploy บน Windows Server + NSSM |
| [line-richmenu-urls.md](line-richmenu-urls.md) | URL ที่ใช้ใน LINE Rich Menu |

---

## ภาพประกอบและสื่อภาพ

### Visuals ที่สร้างด้วย Script

| โฟลเดอร์/ไฟล์ | เนื้อหา |
|---|---|
| [architecture-visuals/](architecture-visuals/) | ภาพ architecture ก่อน/หลังระบบ (PNG + HTML) |
| [iot-visuals/](iot-visuals/) | ภาพ IoT infrastructure, user flow, automation (PNG + HTML) |

### ภาพต้นฉบับและ Assets

| โฟลเดอร์/ไฟล์ | เนื้อหา |
|---|---|
| [illustrations/](illustrations/) | โลโก้ NPU, โลโก้ ARC, QR Code LINE OA, QR Code Web, ภาพบุคลากร |
| [imgIP3/](imgIP3/) | ภาพอุปกรณ์ IoT — Sonoff, IP3 block diagram |
| [screenshots/](screenshots/) | Screenshots ระบบ (ผู้ใช้ 12 ภาพ, ผู้ดูแล 19 ภาพ) |

### ไฟล์ Screenshots สำคัญ

| ไฟล์ | เนื้อหา |
|---|---|
| [screenshots/user_01_landing.png](screenshots/user_01_landing.png) | หน้าแรก — เลือกห้อง |
| [screenshots/user_03_booking_form.png](screenshots/user_03_booking_form.png) | ฟอร์มจอง |
| [screenshots/user_07_virtual_card.png](screenshots/user_07_virtual_card.png) | Virtual Card + QR |
| [screenshots/real_01_login.png](screenshots/real_01_login.png) | Staff Portal — Login |
| [screenshots/real_02_dashboard.png](screenshots/real_02_dashboard.png) | Staff Portal — Dashboard |
| [screenshots/real_16_iot_monitor.png](screenshots/real_16_iot_monitor.png) | Staff Portal — IoT Monitor |

---

## Scripts สร้างเอกสาร

Scripts เหล่านี้ใช้สร้างไฟล์เอกสาร (.docx / .png) จาก source .md

| Script | สร้างอะไร |
|---|---|
| [make_user_manual.py](make_user_manual.py) | `user-manual.docx` จาก `user-manual.md` |
| [make_admin_manual_real.py](make_admin_manual_real.py) | `admin-manual-v2.docx` จาก `admin-manual.md` |
| [make_admin_docx.py](make_admin_docx.py) | `admin-manual.docx` (version เก่า) |
| [make_report_docx.py](make_report_docx.py) | `report-management-2568.docx` |
| [make_image_generation_workflow_guide.py](make_image_generation_workflow_guide.py) | `image-generation-workflow-guide.docx` + infographic PNG |
| [capture_user_screenshots.py](capture_user_screenshots.py) | Screenshots หน้าผู้ใช้อัตโนมัติ |
| [capture_admin_screenshots.py](capture_admin_screenshots.py) | Screenshots Staff Portal อัตโนมัติ |
| [make_admin_screenshots.py](make_admin_screenshots.py) | Screenshots ผู้ดูแลระบบ (version เก่า) |
| [manual_style.py](manual_style.py) | สไตล์กลาง .docx ชุด 2569 (ตั้ง `w:cs`/`w:szCs` ให้ภาษาไทยไม่เพี้ยนใน Word · สารบัญเป็น TOC field มีเลขหน้า) |
| [make_user_manual_2569.py](make_user_manual_2569.py) | `user-manual-2569.docx` (ยังไม่ sync กับไฟล์จริงที่แก้ด้วย Word — ดู progress-2026-08-02) |
| [make_staff_manual_2569.py](make_staff_manual_2569.py) | `staff-manual-2569.docx` |
| [compose_mobile_figures.py](compose_mobile_figures.py) | รวมภาพหน้าจอมือถือ (9:16) เป็นภาพประกอบกรอบ 16:9 |
| [make_external_report_docx.py](make_external_report_docx.py) | `external-access-report.docx` รายงานประกอบการประชุมเรื่องบุคคลภายนอก + `/card-login/` |
| [capture_external_shots.py](capture_external_shots.py) | แคปหน้าจอ external จาก production 1920×1080 (ต้องมี `STAFF_USER`/`STAFF_PASS`) |
| [fix_manual_toc.py](fix_manual_toc.py) | แพตช์สารบัญ .docx ที่มีอยู่แล้วให้มีเลขหน้า + เริ่มนับหน้าที่บทที่ 1 |

---

*อัปเดตล่าสุด: 7 สิงหาคม 2569*
