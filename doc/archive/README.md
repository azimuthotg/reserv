# doc/archive — เอกสารที่เลิกใช้แล้ว

> ⚠️ **ห้ามใช้ไฟล์ในโฟลเดอร์นี้อ้างอิงสถานะระบบปัจจุบัน**
> เก็บไว้เพื่อดูประวัติ/นำ layout ไปใช้ซ้ำเท่านั้น เนื้อหาข้างในล้าสมัยและหลายจุด **ผิดจากระบบจริง**
> เอกสารที่ตรงกับสถานะปัจจุบันอยู่ใน `doc/` ชั้นนอก — ดู [../INDEX.md](../INDEX.md)

จัดเก็บเมื่อ **8 ส.ค. 2569** ตอนเคลียร์เอกสารหลายเวอร์ชันที่ทับซ้อนกัน

---

## กับดักที่ทำให้หลงทาง (อ่านก่อนเปิดไฟล์ในนี้)

| สิ่งที่เอกสารเก่าเขียน | ความจริงปัจจุบัน |
|---|---|
| `booking_name = netflix` (Netflix Room / Netflix Zone) | คือห้อง **Edutainment Zone** เปลี่ยน key เป็น `edutainment` แล้ว · **คนละห้องกับ `netflix1_vm` (Netflix Pro)** ที่เป็นเครื่องเสมือนของ VM Gateway |
| ห้องอยู่ "ชั้น 2 อาคารบรรณสาร" เวลา 08:00–18:00 / 08:00–20:00 | ห้องจริงอยู่ชั้น 1 และชั้น 3 สำนักวิทยบริการ · เวลา จ.-ศ. 08:30–16:30 · ส.-อา. 09:00–17:00 |
| ความจุ 6–12 คนต่อห้อง Canva/ChatGPT | Canva Pro 1/2 = 2 คน · Netflix Pro = 1 คน |
| ห้อง ChatGPT (`chat-gpt`) เปิดให้บริการ | ปิดแล้วตั้งแต่ 8 ส.ค. 2569 (`is_active=0`) เครื่องถูกนำไปทำ Canva Pro 2 |
| ระบบใช้ `netflix.html` บน arc.npu.ac.th + Google Apps Script + Google Sheets | ระบบเดิมก่อน migration — ปัจจุบันเป็น Django + MySQL ทั้งหมด |
| สถานะ "สมาชิกถาวร รอ deploy" / "รอทีมประตูทดสอบ" | ปิดงานครบแล้วตั้งแต่ 16 ก.ค. 2569 (ทีมประตูเทส QR ผ่านทั้งรายวันและถาวร) |

---

## ผังโฟลเดอร์

### `manuals-old/` — คู่มือรุ่นก่อน (เม.ย. – มิ.ย. 2569)

ถูกแทนที่ด้วย `user-manual-reserv-2569.docx` และ `staff-manual-2569.docx`

- `user-manual.md` / `.docx`, `user-manual-v1.docx` — คู่มือผู้ใช้รุ่น 1–2
- `admin-manual.md` / `.docx`, `admin-manual-v2.docx` / `.pdf` — คู่มือผู้ดูแลรุ่น 1–2
  (ตารางห้องในไฟล์เหล่านี้เป็น**ข้อมูลสมมติ** ไม่ตรงกับ DB จริง)
- `make_user_manual.py`, `make_admin_docx.py`, `make_admin_manual_real.py`,
  `make_admin_screenshots.py`, `capture_user_screenshots.py`, `capture_admin_screenshots.py`
  — สคริปต์ที่สร้างไฟล์ข้างบน ใช้ภาพชุด `screenshots/user_*`, `screenshots/real_*`, `screenshots/admin_*`
- `user-manual-reserv-2569.before-toc.docx` — สำเนาสำรองก่อนแพตช์สารบัญ (2 ส.ค. 2569)
- `external-access-manual.pdf` — คู่มือ external ก่อนแปลงเป็นรายงานประกอบการประชุม

### `reports-old/` — รายงานและเอกสารสถาปัตยกรรมรุ่นเก่า (พ.ค. 2569)

- `development_report.md` — รายงานการพัฒนาระบบ (ตารางห้องเป็นชุดเก่า)
- `architecture-flow.md` + `architecture-visuals/` — เปรียบเทียบระบบเดิม (Google Apps Script) กับระบบใหม่
- `report-management-2568.md` / `.docx` — รายงานบริหารจัดการปี 2568 (เอกสารที่ส่งมอบไปแล้ว)
- `make_report_docx.py` — สคริปต์สร้าง `report-management-2568.docx`

### `promo/` — สื่อประชาสัมพันธ์ชุดปี 2569 ต้นปี

เนื้อหายังใช้รายชื่อ **5 ห้องเดิมที่มี ChatGPT** จึงไม่ตรงกับบริการปัจจุบันแล้ว
ถ้าจะทำป้ายใหม่ ให้ใช้ layout เดิมได้แต่ต้องอัปเดตรายชื่อห้องเป็น
MINI THEATER · Edutainment Zone · Canva Pro 1 · Canva Pro 2 · Netflix Pro · โต๊ะประชุมชั้น 1

- `poster-plan.md`, `promo-signage-plan.md` — แผนงานชุดป้าย
- `poster-content.md` / `.txt`, `poster-booking-guide.html`, `poster-v2.png`, `poster-v2-philosophy.md`
- `infographic-1-system-overview.md`, `infographic-2-steps-rules.md`
- `image-generation-workflow-guide.md` / `.docx` + `make_image_generation_workflow_guide.py`
  — คู่มือ workflow การเจนภาพ (วิธีทำยังใช้ได้ ตัวอย่างเนื้อหาล้าสมัย)

### `handoff/` — เอกสารส่งต่องานที่ปิดแล้ว

ทั้ง 3 ไฟล์เขียนสถานะไว้ ณ มิ.ย.–ก.ค. 2569 ซึ่ง**ปิดงานครบหมดแล้ว** — สถานะข้างในจึงค้างและทำให้เข้าใจผิด

- `handoff-external-member-reserv.md` — api → reserv (ทำเสร็จ)
- `handoff-external-permanent-member-to-api.md` — reserv → api (ทำเสร็จ)
- `external-member-operations-handoff.md` — แจ้งทุกทีม (สถานะ "ถาวร = รอ deploy" ค้าง — จริง ๆ prod แล้ว)

ภาพรวมระบบบุคคลภายนอกฉบับปัจจุบันอยู่ที่ [../external-access-report.docx](../external-access-report.docx)
