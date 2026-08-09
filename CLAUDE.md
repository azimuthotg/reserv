<!-- PROJECT-STATUS
name: reserv
status: active
deployment: production
deploy_url: https://lib.npu.ac.th/reserv/
deploy_server: 110.78.83.102 (lib.npu.ac.th)
deploy_os: Windows Server 2019
deploy_method: NSSM + Waitress (deploy/waitress_serve.py พอร์ต 8003) ผ่าน gateway IIS+ARR · static ผ่าน WhiteNoise
deploy_path: C:\project\reserv (ไม่ใช่ C:\projects\)
deploy_db: MySQL `reserv_db` ที่ 202.29.55.213
deploy_notes:
  - ⚠️ production มี venv — คำสั่ง python/pip ทุกตัวต้องเรียก `.\venv\Scripts\python.exe` / `.\venv\Scripts\pip.exe` ห้ามเรียก `python` เปล่า ๆ
  - deploy ที่ยืนยันว่าใช้ได้จริง (2026-08-08): `cd C:\project\reserv` → `git pull origin master` → `.\venv\Scripts\python.exe manage.py migrate` → `.\venv\Scripts\python.exe manage.py collectstatic --noinput` → `c:\nssm\nssm.exe restart Reserv`
  - restart: c:\nssm\nssm.exe restart Reserv   (ชื่อ service ยืนยันจากเซิร์ฟเวอร์แล้ว 2026-08-08)
  - ⚠️ .env เครื่อง dev ชี้ DB production ตัวเดียวกัน — migrate จากเครื่อง dev ลงฐานจริงทันที (ดู MEM.md)
progress: 98
phase: ระบบใช้งานจริง (production) ครบ 4 phase แล้ว — external access ปิดครบวงจร · บริการ VM 3 ห้อง (Canva Pro 1/2, ChatGPT) เปิดจอง 24 ชม. · เหลือปุ่มเข้าใช้งาน VM (รอ URL จริงจากทีม DNS) + งาน enhancement
done_2026-07-10:
  - ✅ push ค้างทั้ง 2 repo (reserv+apiproject) ขึ้น GitHub สำเร็จ (แก้จากฝั่ง Windows แทน WSL token ที่หมดอายุ)
  - ✅ deploy prod ทั้ง reserv+apiproject (git pull+restart, ไม่มี migration) เรียบร้อย เทส prod ผ่าน
  - ✅ สมาชิกถาวรไม่บังคับเลขบัตร (รองรับ VVIP เช่น นายกสภาฯ) — เว้นว่างได้ api gen รหัสอ้างอิง `V`+12 หลัก, แก้ 2 ฝั่ง (reserv form/redirect/แสดงผล + api permanent_register/regex), test ผ่าน reserv 13/13 + api 10/10
done_2026-07-13:
  - ✅ ส่งตัวอย่าง JSON response ของ `/v2/external/check/` ให้ทีมประตูแล้ว
  - ✅ ทำคู่มือแจ้งเจ้าหน้าที่ — ระบบบุคคลภายนอกเข้าใช้บริการ: [doc/external-access-report.docx](doc/external-access-report.docx)
done_2026-07-16:
  - ✅ บุคคลภายนอกรายวัน (`/external/`) ไม่บังคับเลขบัตร — บังคับแค่ชื่อ-สกุล, แก้ 2 ฝั่ง (reserv `external_access()`+template / api `/v2/external/issue/` gen ref-id `V` เมื่อไม่ส่งเลขบัตร), test reserv 17/17 + api 22/22 — push แล้วทั้ง 2 repo (reserv `336d4e2`, apiproject `2ad5701`)
  - ✅ อัปเดตคู่มือแจ้งเจ้าหน้าที่เป็น v1.1 ให้ตรงพฤติกรรมใหม่ [doc/external-access-report.docx](doc/external-access-report.docx)
  - ✅ deploy prod ทั้ง 2 repo (apiproject → reserv + restart) + เทส prod ผ่าน — รายวันกรอกแค่ชื่อ-สกุลได้ QR สมบูรณ์
  - ✅ **ทีมประตูเทส QR จริงผ่านแล้วทั้ง 2 แบบ (รายวัน + ถาวร)** — ปิดงาน external access ครบวงจร (task ค้างตั้งแต่ 2026-07-12)
done_2026-07-17:
  - ✅ **อุปกรณ์ส่วนกลางในหน้า IoT Monitor — flip gate 1-3** (deploy + เทส prod ผ่านแล้ว) — `RoomDevice.room` ว่างได้ + `group_name` (migration `0012`), รวม logic ไว้ที่ helper กลาง `_iot_cards()`, ลงทะเบียน RoomDevice ใน Django Admin — push `be97232` + `6fc7113` → origin/master (ดู doc/progress-2026-07-17.md)
done_2026-07-20:
  - ✅ **หน้าแก้ไขชื่อ-สกุลสมาชิกถาวร** `/manage/external/<id>/edit/` — proxy ไป `/v2/external/permanent/<id>/update/` ของ api (ใหม่), เปลี่ยนรูปได้ (เว้นว่าง = ใช้รูปเดิม), เพิ่มปุ่ม "แก้ไข" ในหน้ารายละเอียด — push `379d456` จับคู่ apiproject `e14897d` · deploy prod ทั้ง 2 repo + เทสจริงผ่าน
done_2026-07-22:
  - ✅ **หน้า `/card-login/` — ล็อกอิน AD บนเว็บ → ออก QR เข้าประตู โดยไม่ต้องเป็นเพื่อน LINE OA** (deploy + เทส prod ผ่านทั้งนักศึกษา+บุคลากร) — สำหรับผู้มาใช้พื้นที่อย่างเดียว ไม่รับข่าวสาร · QR = user_ldap ตัวเดียวกับ /card/ ประตูสแกนเหมือนกัน · จองห้องไม่ได้ (ต้องผ่าน LIFF) · "จดจำ 90 วัน" ผ่าน signed cookie แยกจาก session · rate limit ต่อบัญชี · ไม่มี migration/ไม่แตะ api · push ชุด `7f4f908`→`c044203` → origin/master (ดู MEM.md 2026-07-22)
  - ✅ คู่มือช่องทางขอ QR เข้าประตู (สรุป 4 ช่องทาง A-D) [doc/door-qr-guide.docx](doc/door-qr-guide.docx)
done_2026-07-31:
  - ✅ **คู่มือการใช้งาน 2 เล่ม** — [doc/user-manual-reserv-2569.docx](doc/user-manual-reserv-2569.docx) (ผู้ใช้ 15 บท ครอบคลุมมือถือ+เว็บ) และ [doc/staff-manual-2569.docx](doc/staff-manual-2569.docx) (เจ้าหน้าที่ 15 บท ฟีเจอร์เต็ม) · ภาพหน้าจอจาก production จริง 55 ภาพ 16:9 · สร้างซ้ำได้ด้วย `doc/make_*_2569.py` (ดู doc/progress-2026-07-31.md)
  - ✅ แคปหน้าจอมือถือได้โดยไม่ต้องมีเครื่องจริง — Playwright emulate iPhone 390×844 บนเว็บ production · หน้า LIFF ใช้ headed browser ผ่าน WSLg ให้ผู้ใช้ login LINE เอง
  - ✅ สร้าง booking ทดสอบ `#445`/`#446` เพื่อเก็บภาพหน้าจองสำเร็จ/Check-in **แล้วยกเลิกทั้ง 2 รายการ** (ยืนยันสถานะที่ /manage/bookings/ แล้ว)
done_2026-08-02:
  - ✅ **สารบัญคู่มือมีเลขหน้าแล้ว** — `manual_style.py` เปลี่ยนสารบัญจากข้อความธรรมดาเป็น TOC field ของ Word (`\o "1-3" \h \z \u` + style `toc 1–3` ฟอนต์ไทย + จุดไข่ปลา) และแบ่ง section ให้ปก+สารบัญไม่มีเลขหน้า ส่วนบทที่ 1 เริ่มนับหน้า 1 · เพิ่ม `doc/fix_manual_toc.py` แพตช์ไฟล์ .docx ที่แก้ด้วย Word ไปแล้วโดยไม่ต้องสร้างใหม่ · [doc/user-manual-reserv-2569.docx](doc/user-manual-reserv-2569.docx) แพตช์+ตรึงเลขหน้าด้วย Word แล้ว 24 หน้า (ดู doc/progress-2026-08-02.md)
done_2026-08-07:
  - ✅ **ตรวจเอกสารชุดบุคคลภายนอกทั้งหมดเทียบ code** — พบ 4 กลุ่มปัญหา: (1) คู่มือบอกผู้ใช้เว้นเลขบัตรได้ที่หน้า public แต่ `external_permanent()` บังคับ 13 หลัก (2) สถานะ "รอทีมประตูทดสอบ" ค้าง (3) ไม่มีหัวข้อหน้าแก้ไขสมาชิก (4) คู่มือ 2569 กับคู่มือ external ตอบไม่ตรงกันเรื่องใครลงทะเบียนสมาชิกถาวร
  - ✅ **แก้เนื้อหาคู่มือ external ให้ตรง code** — QR ประตูใช้งานได้ปกติ (ทีมประตูเทสผ่าน 16 ก.ค. แจ้งเรียบร้อยแล้ว) · VIP เว้นเลขบัตรได้เฉพาะหน้าเจ้าหน้าที่ (หน้า public บังคับ 13 หลัก) · เพิ่มหัวข้อแก้ไขข้อมูลสมาชิก · FAQ ใหม่
  - ✅ **แปลงเป็นรายงานประกอบการประชุม** — `doc/external-access-manual.docx` → [doc/external-access-report.docx](doc/external-access-report.docx) (สคริปต์ `make_external_manual_docx.py` → `make_external_report_docx.py`) · ตัดสารบัญออก ปกเป็นชื่อรายงาน · เพิ่ม **บทที่ 5 ช่องทาง `/card-login/` ของนักศึกษา-บุคลากร** (ขั้นตอน + ข้อมูลเก็บที่ไหน + ขอบเขต/ความเสี่ยง) และตารางสรุป 4 ช่องทางขอ QR ในบทที่ 1
  - ✅ **เปลี่ยนรูปแบบตามที่ผู้ใช้กำหนด** — ย้ายไปใช้ `manual_style.py` ชุดเดียวกับคู่มือ 2569: ดำล้วน · body 16 pt · หัวตารางเทาจัดกลาง · ไม่มีกล่องคำแนะนำ/คำเตือน · ภาพ 16:9 จาก production 6 ภาพ (ขาดหน้าแก้ไขสมาชิก รอแคป)
  - ✅ เพิ่ม `doc/capture_external_shots.py` — แคปหน้าจอ external 1920×1080 จาก prod (อ่านอย่างเดียว) ใช้ `STAFF_USER`/`STAFF_PASS`
done_2026-08-08:
  - ✅ **ตามใบแจ้งทีม LRS ARC VM Gateway** — เพิ่มห้อง `canva2` "Canva Pro 2" (clone จาก `canva`) · ปิดห้อง `chat-gpt` (`is_active=0` ไม่ลบ เก็บประวัติ 16 รายการ) · เปลี่ยนชื่อ `canva` → "Canva Pro 1" · copy รูป `canva2.png` — แก้ข้อมูลอย่างเดียว ไม่แตะ code (ดู doc/progress-2026-08-08.md)
  - ✅ อัปเดต [doc/line-richmenu-urls.md](doc/line-richmenu-urls.md) ระบุปุ่ม Rich Menu ที่ต้องแก้ + sync room keys ใน CLAUDE.md/AGENTS.md
  - ✅ **เคลียร์เอกสารทั้งโฟลเดอร์ `doc/` ให้เหลือเฉพาะที่ตรงกับสถานะปัจจุบัน** — ย้ายคู่มือ/รายงาน/สื่อ/handoff รุ่นเก่า 37 ไฟล์ไป `doc/archive/{manuals-old,reports-old,promo,handoff}` พร้อม [doc/archive/README.md](doc/archive/README.md) ที่ list "กับดัก" ของเอกสารเก่าไว้ · เขียน [doc/INDEX.md](doc/INDEX.md) ใหม่ทั้งไฟล์ · ปิด task handoff/INDEX ที่ค้าง
  - ✅ **แก้เอกสาร deploy ให้ตรงของจริง** — CLAUDE.md/AGENTS.md เคยเขียน Nginx + พอร์ต 8000 + `nssm install reserv-booking "python -m waitress..."` + `load_rooms` ซึ่ง**ผิดทั้งหมด** · ของจริงคือ IIS+ARR → WhiteNoise, `deploy/waitress_serve.py` พอร์ต 8003, path `C:\project\reserv`, ไม่มี command `load_rooms` แล้ว · **ชื่อ NSSM service จริง = `Reserv`** (ผู้ใช้ยืนยันจากเซิร์ฟเวอร์) แก้ครบทั้ง 4 ไฟล์
  - ✅ **deploy prod + เทสจริงผ่าน** — `git pull` + `collectstatic` (1 ไฟล์: canva2.png) ไม่ต้อง restart · ตรวจบน production: `/room/canva2/` 200 พร้อมรูป · `/room/chat-gpt/` 404 · ปฏิทินสาธารณะแสดง 6 ห้องชื่อใหม่ครบ · static `canva2.png` 200 (803 KB)
  - ✅ **จัดระเบียบห้อง `netflix1_vm` → ชื่อแสดง "Netflix Pro"** — ห้องนี้เปิดใช้จริง 20 การจอง (ล่าสุด 1 ส.ค. 2569) แต่ไม่เคยมีในเอกสารเลย · แก้ `name`/`location`/`facilities`/`rules`/`how_to_use`/`eligible_users` ให้เข้าชุดกับห้องอื่น · เพิ่มลง line-richmenu-urls.md พร้อมเตือนว่า `netflix` ในเอกสารเก่า = Edutainment Zone คนละห้อง (ดู MEM.md)
  - ✅ **กติกาห้ามจองทับเวลาข้ามห้อง (ตามใบแจ้งทีม VM รอบ 2)** — เพิ่มฟิลด์ `Room.allow_overlap` (migration `0013`) + guard ใน `create_booking()` ภายใน transaction เดียวกับ conflict check · ติ๊กยกเว้นเฉพาะ `meeting_f1` · ไม่ hardcode booking_name · test 23/23 ผ่าน (เพิ่มใหม่ 6 เคส) — deploy prod + restart Reserv เรียบร้อยในวันเดียวกัน
  - ✅ **เปิดจองนอกเวลาให้บริการออนไลน์ 3 ห้อง** (`canva`, `canva2`, `netflix1_vm` = RDP เข้าเครื่องแม่ที่เปิด 24 ชม. ไม่ต้องเข้าอาคาร) — เพิ่ม `Room.is_online` (migration `0014`) · จองได้ `00:00–23:59` ทุกวันรวมวันหยุด · แบ่ง 3 รอบ เช้ามืด/กลางวัน/กลางคืน จองได้รอบละ 1 ครั้ง · ห้ามจองคร่อมรอบ · ห้องจริงพฤติกรรมไม่เปลี่ยน · test 30/30 ผ่าน (เพิ่มใหม่ 7 เคส)
  - ✅ **Netflix เปิดจองเฉพาะนอกเวลาราชการ** — สำนักฯ มีบัญชี Netflix บัญชีเดียว กลางวันให้บริการที่ Edutainment Zone (ชั้น 3) · เพิ่ม `Room.day_round_enabled` (migration `0015`) ปิดรอบกลางวันรายห้อง ตั้ง `netflix1_vm=False` ห้องเดียว · หน้าจองไม่แสดงเวลาช่วงกลางวันให้เลือก + ตัดเวลาสิ้นสุดที่ขอบรอบ · แก้ location/description/rules/how_to_use ของ 3 บริการ VM ให้ตรงข้อเท็จจริง (Canva = VM แยกตัว แยก account ไม่มีเครื่องจริงชั้น 1) · test 31/31 ผ่าน
  - ✅ **เทสฟอร์มจองจริงบน production ด้วย Playwright** (headed ใน WSL ผู้ใช้ล็อกอิน LINE เอง · อ่านอย่างเดียว) — Netflix slot กลางวัน = 0 · Canva Pro 2 ครบ 3 รอบ 143 slot · เลือกเริ่ม 16:00 สิ้นสุดได้สูงสุด 17:00 · MINI THEATER เหมือนเดิม · เก็บสคริปต์ไว้ที่ [doc/check_booking_form.py](doc/check_booking_form.py)
  - ✅ **ยุบหนังสือถึงทีม VM 3 ฉบับเหลือฉบับเดียว** [doc/reply-vm-summary-2026-08-08.md](doc/reply-vm-summary-2026-08-08.md) — ร่างเดิมย้ายไป `doc/archive/vm-letters-drafts/` (บางส่วนถูกแก้ทีหลัง · ฉบับรวมส่งให้ทีม VM แล้ว 2026-08-09)
done_2026-08-09:
  - ✅ **ส่งหนังสือให้ทีม VM Gateway แล้ว และทีม VM ดำเนินการครบตามเอกสาร** — `room_key='canva2'` · ถอด mapping `chat-gpt` · กรอง `is_active=1` · Gateway รองรับ session 24 ชม. → **ช่องว่าง "จองได้แต่เข้าเครื่องไม่ได้" ปิดแล้ว**
  - ✅ **ยืนยัน location: Canva Pro 1 / Canva Pro 2 / Netflix Pro เป็น VM ทั้งหมด** — ไม่มีเครื่องจริงให้นั่ง (ปิดข้อค้างเรื่อง location)
  - ✅ **ได้ URL เว็บ VM Gateway (ชั่วคราว)** `http://202.29.55.180:8888/vm/login` — รอทีม DNS ทำ https + domain ก่อนนำไปใช้จริง
  - ✅ **`/card-login/` ยืนยันทำงานสมบูรณ์** (ผู้ใช้เทสเอง) — ปิด task เรื่องเทสหน้านี้
  - ✅ **เคาะกติกาโควตา: คงไว้ 3 สิทธิ์/ห้อง/วัน (รอบละ 1)** สำหรับช่วงแรก รอข้อมูลการใช้งานมากพอค่อยวิเคราะห์ปรับ — ปิดข้อค้าง "คุยกติกานอกเวลาทำการ"
  - ✅ ล้างรายการ `next:` ที่ล้าสมัย (deploy overlap / แจ้ง overlap แยกฉบับ / ขอ URL Gateway / แจ้ง booking_name — ทำไปแล้วทั้งหมด)
  - ✅ **เพิ่ม test หน้าแก้ไขสมาชิกถาวร `ManageExternalEditTests` 7 เคส** — คลุมจุดที่พังเงียบได้คือ **ไม่เลือกรูป = ต้องไม่ส่ง `files` ไป api** (ไม่งั้นทับรูปเดิมของสมาชิก) + เลือกรูป=ส่ง bytes · GET เติมชื่อเดิม · 404 ทั้ง GET/POST redirect ไปหน้ารายการ · api ล่มแล้วไม่ล้างสิ่งที่ staff พิมพ์ · ต้องล็อกอิน staff — **test 38/38 ผ่าน** (เดิม 31)
  - ✅ **เติมตาราง URL ใน CLAUDE.md + AGENTS.md** — เพิ่ม `/external/permanent/`, `/card-login/`, `/manage/external/*` (เดิมมีแค่ `/external/` ทั้งที่โค้ดมี 70 routes) · แก้ข้อความ auth flow ที่เขียนว่า "ไม่มี session login แยกสำหรับผู้ใช้ทั่วไป" ซึ่งไม่จริงตั้งแต่มี `/card-login/` (22 ก.ค.)
  - ✅ **deploy ครบทุกอย่างของวันนี้ขึ้น prod + ตรวจผ่าน** — `/room/chat-gpt/` แสดง "จองสูงสุด 3.5 ชม./ครั้ง" ถูกต้อง · hero image เป็น 16:9 พอดี (375×211) ไม่ครอบตัด · QR ขนาดใหม่ทำงานจริง
  - ✅ **ส่งหนังสือตอบกลับทีม VM Gateway แล้ว** — [doc/reply-vm-chatgpt-2026-08-09.md](doc/reply-vm-chatgpt-2026-08-09.md)
  - ✅ **สลับบริการเครื่องเสมือน: ปิด Netflix Pro → เปิด ChatGPT** (ตามใบแจ้งทีม VM 9 ส.ค.) — ตรวจก่อนปิดว่า `netflix1_vm` ไม่มี booking confirmed ตั้งแต่วันนี้ (0 รายการ ตรงกับที่ทีม VM แจ้ง) · `chat-gpt` เปิดกลับพร้อมตั้ง `is_online=1`, `00:00–23:59` · **เขียนเนื้อหาห้องใหม่ทั้งชุด** (เดิมยังเป็นเครื่องจริงชั้น 1 — location/description/facilities/rules/how_to_use + เติม `eligible_users` ที่ว่างอยู่) · เพิ่มกฎเตือนเรื่องบัญชีใช้ร่วมกัน (อย่าพิมพ์ข้อมูลส่วนตัว ลบประวัติก่อนเลิกใช้) · แก้ข้อมูลล้วนไม่แตะ code · สคริปต์ [doc/prep_chatgpt_room.py](doc/prep_chatgpt_room.py) + [doc/switch_netflix_to_chatgpt.py](doc/switch_netflix_to_chatgpt.py) · **ตรวจ prod ผ่าน** (`/room/chat-gpt/` 200 · `/room/netflix1_vm/` 404 · ปฏิทิน 6 ห้องถูกต้อง) · ร่างหนังสือตอบกลับ [doc/reply-vm-chatgpt-2026-08-09.md](doc/reply-vm-chatgpt-2026-08-09.md)
  - ✅ **แก้เพดานเวลาจองที่แสดงผลไม่ตรงกับของจริงทุกห้อง** — หน้ารายละเอียดเคยแสดง `Room.max_booking_hours` (2 ชม. เกือบทุกห้อง · Netflix 3 ชม.) **ทั้งที่ระบบ hardcode 210 นาที = 3.5 ชม. เท่ากันหมด** และไม่เคยบังคับตามฟิลด์นั้นเลย · ผู้ใช้เคาะว่า **3.5 ชม. ถูกแล้ว แก้การแสดงผลให้ตรง** · รวมเป็นค่ากลาง `MAX_BOOKING_MINUTES`/`MAX_BOOKING_HOURS_TEXT` ใน `service_hours.py` ใช้ร่วมกันทั้ง backend guard, ฟอร์มจอง, หน้ารายละเอียด และหน้าแก้ไขห้อง · ถอด `max_booking_hours` ออกจาก `RoomForm` (แสดงเป็นค่าคงที่แบบ disabled แทน) กันเจ้าหน้าที่ตั้งค่าแล้วเข้าใจผิดว่ามีผล — **ไม่มี migration** (คงฟิลด์ใน model ไว้พร้อมคอมเมนต์ว่าเลิกใช้)
  - ✅ **Canva Pro 1/2 ความจุ 2 → 1 คน** (ผู้ใช้ยืนยัน — เป็น VM ส่วนตัวเครื่องละคน)
  - ✅ **รูปห้อง 3 บริการ VM ครบแล้ว** — ผู้ใช้ generate ด้วย AI (มีชื่อบริการพาดบนรูป) · แปลงเป็น 1920×1080 crop 16:9 + quantize 256 สี เหลือ 625–752 KB เท่ารูปห้องเดิม (เต็มสี 1.9 MB หนักเกินไปสำหรับ LIFF บนมือถือ) · `netflix1_vm.png` เพิ่มใหม่ · `canva.png`/`canva2.png` ทับรูปเครื่องจริงเดิมที่ไม่ตรงข้อเท็จจริงแล้ว
  - ✅ **แก้กล่องรูปห้องให้เป็น 16:9** (`landing.html` `.room-img` · `room_detail.html` `.room-hero`) — เดิมสูงคงที่ 150px/220px ทำให้ **บนเดสก์ท็อปเห็นภาพแค่ 48% และ 40% ตามลำดับ** ชื่อบริการที่พาดอยู่ส่วนบนของรูปถูกตัดหายทั้งบรรทัด · hero จำกัดกว้าง 560px เท่าคอลัมน์เนื้อหา (พร้อม accent-bar) · รูปห้องเดิมทั้ง 3 ใบก็ได้แสดงเต็มภาพด้วย
  - ✅ **ขยายขนาด QR code ทุกช่องทาง** (งานค้างจาก inbox 2026-07-23) — เดิมแต่ละหน้า hardcode คนละค่า (160/180/200 px) · รวมมาที่ helper กลาง [booking/static/booking/js/qr.js](booking/static/booking/js/qr.js) (`NPUQr.render`) คิดขนาดจากความกว้างจอจริง 200–320 px และวาดที่ความละเอียด 2 เท่าเพื่อความคมบนจอ retina · ใช้ครบทั้ง 5 หน้า: `/card/`, `/card-login/`, `/external/`, `/external/permanent/`, `/manage/external/<id>/` · **บนจอ 375px: 180→279 px (+55%)** · ตรวจบนเบราว์เซอร์จริงที่ 320/375/1280 px ไม่ล้นแนวนอน และทำงานถูกทั้ง 2 เส้นทางของ qrcodejs (Android โชว์ canvas · เบราว์เซอร์อื่นสลับเป็น img) — **deploy prod + ตรวจบนของจริงผ่านแล้ว** (`qr.js` 200/2877 bytes · วาดบนหน้า production ได้ 279 px ที่จอ 375 และ 320 px ที่ desktop · ไม่มี console error)
  - ✅ **แก้ `doc/capture_external_shots.py` ให้รันได้จริง** — playwright 1.58 ใน WSL มองหา chromium revision 1208 แต่ที่ติดตั้งคือ 1217 → `launch()` ล้มทุกครั้ง · เพิ่ม `chromium_path()` หา binary เองจาก `~/.cache/ms-playwright` + `--no-sandbox` · แก้ข้อความท้ายสคริปต์ที่ยังอ้างชื่อไฟล์เก่า `make_external_manual_docx.py` · ทดสอบเปิดเบราว์เซอร์ + เข้าหน้า login ผ่านแล้ว
next:
  - **[รอ URL สุดท้าย — ผู้ใช้สั่งยังไม่ลงมือ] เปลี่ยนปุ่มของห้อง VM 3 ห้อง (`canva`, `canva2`, `chat-gpt`) จาก "ควบคุมอุปกรณ์ไฟฟ้า" เป็นปุ่ม "เข้าใช้งาน" ที่เปิดแท็บใหม่ไปหน้า login ของ VM Gateway** — URL ทดสอบ `http://202.29.55.180:8888/vm/login` · **รอทีม DNS ทำ https + domain ก่อนค่อยแก้จริง** · แก้ `how_to_use` ของ 3 ห้องให้ตรงวิธีเข้าใช้จริงในรอบเดียวกัน (ตอนนี้ Canva ยังเขียนว่า "เปิดเครื่องคอมพิวเตอร์ที่ให้บริการ")
  - **ทำรูปห้อง `chat-gpt.png` ใหม่** — ตอนนี้ยังเป็นรูปเครื่องจริงเก่า ไม่มีชื่อพาด ไม่เข้าชุดกับ Canva Pro 1/2 · ส่งพรอมป์ให้ผู้ใช้แล้ว 2026-08-09 (โทนเขียวมรกตบนพื้นเข้ม แยกจาก Canva ทั้งสองใบ) รอไฟล์กลับมาแปลง 1920×1080 + quantize แล้ว `git add -f`
  - **แก้ LINE Rich Menu** — ปุ่ม ChatGPT → `?room=canva2` + เปลี่ยนรูปปุ่มเป็น "Canva Pro 2" และรูปปุ่ม Canva เป็น "Canva Pro 1" (ผู้ใช้ทำเอง — รายละเอียดใน doc/line-richmenu-urls.md)
  - **[รอผู้ใช้รัน — ต้องใช้รหัส staff] แคปภาพหน้าแก้ไขสมาชิกถาวรให้รายงาน external ครบ 7 ภาพ** — สคริปต์พร้อมและทดสอบเปิดเบราว์เซอร์ผ่านแล้ว เหลือแค่ใส่รหัส: `wsl -d Ubuntu -u admin_e -- env STAFF_USER=xxx STAFF_PASS=yyy python3 /mnt/c/projects/reserv/doc/capture_external_shots.py` แล้วรัน `python doc/make_external_report_docx.py`
  - export PDF/Excel จากหน้า analytics — ค้างเป็น task (spawn แล้ว 2026-07-09) รอทำเมื่อมีความต้องการจริง (ดู MEM.md: embed ฟอนต์ TH Sarabun New กันตัวอักษรหาย)
  - ทำฟีเจอร์เพิ่มวันหยุดอัตโนมัติในตารางวันหยุด (ตอนนี้ต้องเพิ่มเองทีละวัน) — รับแจ้ง 2026-07-12
risks:
  - `/std-info/`,`/staff-info/` (v1) ฝั่ง api ยังไม่ต้อง auth — ใครรู้รหัสนักศึกษายิงดูชื่อ-คณะได้ (leak `apassword` + ดึงทั้งตาราง + สิทธิ์เขียน ปิดแล้ว 2026-07-23 ดู MEM.md — เป็นงานฝั่ง api)
  - รายวันไม่บังคับเลขบัตร → ระงับสิทธิ์/โควตารายคนใช้ไม่ได้ + pool 100 รหัส/วันอาจหมดเร็ว (ดู MEM.md — มีแผนถอย)
  - `booking_name` ของห้องที่ผูก VM Gateway (`canva`, `canva2`, `chat-gpt`) เป็นสัญญาข้ามระบบ — แก้โดยไม่แจ้งทีม VM = นักศึกษาเข้าเครื่องไม่ได้ทันที (ดู MEM.md)
  - .env เครื่อง dev ชี้ DB production ตัวเดียวกัน ไม่มีฐานทดสอบแยก → migrate/สคริปต์เขียนข้อมูลลงฐานจริงทันที (ดู MEM.md)
updated: 2026-08-09
-->

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

**การจองห้องทุกช่องทาง** ยืนยันตัวตนผ่าน LINE LIFF และ `api.npu.ac.th` — จองผ่านทางอื่นไม่ได้
Django session login ใช้กับ Staff Portal (`/manage/`) เท่านั้น
**ข้อยกเว้นที่ไม่ใช่การจอง:** `/card-login/` ให้นักศึกษา/บุคลากรล็อกอิน **AD บนเว็บโดยไม่ต้องผ่าน LINE**
เพื่อขอ QR เข้าประตูอย่างเดียว (จองห้องไม่ได้) — ใช้ signed cookie ของตัวเอง ไม่ใช่ Django session

**เวลาให้บริการสำหรับประชาสัมพันธ์:**
- จันทร์ – ศุกร์: `08:30 – 16:30 น.`
- เสาร์ – อาทิตย์: `09:00 – 17:00 น.`
- ปิดเฉพาะวันหยุดนักขัตฤกษ์ โดยแจ้งล่วงหน้า

**บริการเครื่องเสมือน (VM) — ไม่ต้องเข้าอาคาร:** ปัจจุบัน 3 บริการ ทุกตัวจองได้ `00:00 – 23:59`
ทุกวันรวมวันหยุด ใช้ผ่านเว็บล้วน **ไม่มีเครื่องจริงให้นั่งที่ชั้น 1 แล้ว**
- **Canva Pro 1 / Canva Pro 2** = VM คนละตัว **บัญชี Canva แยกกัน**
- **ChatGPT** = VM 1 ตัว บัญชี ChatGPT 1 บัญชี (เปิดกลับ 2026-08-09 บนเครื่องเดิมของ Netflix)

> **`netflix1_vm` (Netflix Pro) ปิดแล้ว `is_active=0` ตั้งแต่ 2026-08-09** — สำนักฯ เปลี่ยนบริการ
> บนเครื่องเสมือนตัวนั้นไปเป็น ChatGPT (ใบแจ้งทีม VM 9 ส.ค.) เก็บห้องและประวัติ 20 รายการไว้
> **Netflix ที่ Edutainment Zone ชั้น 3 ยังให้บริการตามปกติ — คนละเรื่องกับ VM ตัวนี้**

แบ่งเป็น 3 รอบ (เช้ามืด/กลางวัน/กลางคืน) จองได้รอบละ 1 ครั้ง — ดู Overlap / รอบบริการ ด้านล่าง

---

## Tech Stack

| ส่วน | เทคโนโลยี |
|---|---|
| Backend | Django 4.2 + Python 3.12 |
| Database | MySQL 8.0 (host: ดูใน .env, db: reserv_db) |
| Frontend | Django Template + Bootstrap 5.3 + FullCalendar v6 |
| LIFF | LINE Front-end Framework v2 (SDK 2.15+) |
| Process Manager | NSSM + Waitress (Windows Server) |
| Reverse Proxy | IIS + ARR → https://lib.npu.ac.th/reserv/ (static ผ่าน WhiteNoise) |

---

## Commands

```bash
# Development
python3 manage.py runserver 0.0.0.0:8001

# Database
python3 manage.py migrate
python3 manage.py createsuperuser

# Checks
python3 manage.py check
python3 manage.py makemigrations booking

# Production (Windows)
python deploy/waitress_serve.py      # อ่าน WAITRESS_HOST/PORT/THREADS จาก .env
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
| `/external/` | `/reserv/external/` | บุคคลภายนอกขอ QR **รายวัน** (public) — เรียก `/v2/external/issue/` ผ่าน JWT · บังคับแค่ชื่อ-สกุล เลขบัตรไม่บังคับ |
| `/external/permanent/` | `/reserv/external/permanent/` | บุคคลภายนอกสมัคร **สมาชิกถาวร** (public) — **บังคับเลขบัตร 13 หลัก** ต่างจากหน้ารายวัน · รอ staff อนุมัติที่ `/manage/external/` |
| `/room/<booking_name>/` | `/reserv/room/<booking_name>/` | รายละเอียดห้องแบบ public |
| `/card/` | `/reserv/card/` | Virtual Card + Walai status (LIFF) |
| `/card-login/` | `/reserv/card-login/` | **นักศึกษา/บุคลากรล็อกอิน AD บนเว็บ → QR เข้าประตู โดยไม่ต้องผ่าน LINE** (public) · จองห้องไม่ได้ · "จดจำ 90 วัน" ใช้ signed cookie แยกจาก Django session · rate limit ต่อบัญชี (ห้ามต่อ IP — ผู้ใช้อยู่หลัง NAT) |
| `/room-control/` | `/reserv/room-control/` | ควบคุมอุปกรณ์ IoT ระหว่างเวลาจอง (LIFF) |
| `/api/access-status/` | `/reserv/api/access-status/` | ตรวจสถานะ local user ก่อนใช้ frontend cache |
| `/api/check-user/` | `/reserv/api/check-user/` | ตรวจการผูก LINE userId |
| `/api/my-bookings/` | `/reserv/api/my-bookings/` | รายการจองของผู้ใช้ |
| `/api/checkin/` | `/reserv/api/checkin/` | Check-in ก่อน/หลังเวลาเริ่มไม่เกิน 15 นาที |
| `/api/calendar-events/` | `/reserv/api/calendar-events/` | JSON events |
| `/manage/` | `/reserv/manage/` | Staff Portal ใช้ Django session login |
| `/manage/external/` | `/reserv/manage/external/` | staff จัดการสมาชิกถาวร — `register/` · `<citizen_id>/` · `/edit/` · `/approve/` · `/revoke/` · `/delete/` · `/photo/` · **ทุกเส้นทาง proxy ไป api v2 — reserv ไม่เก็บข้อมูลสมาชิกเอง** (หน้า staff เว้นเลขบัตรได้ รองรับ VVIP api gen `V`+12 หลักให้) |
| `/admin/` | `/reserv/admin/` | Django Admin |
| `/health/` | `/reserv/health/` | Health check (NMS monitoring) — public, JSON `{status, db, db_ms}`, 200/503 |

room keys: `mini`, `edutainment`, `canva`, `canva2`, `meeting_f1`, `chat-gpt`
(`netflix1_vm` ปิดแล้ว `is_active=0` ตั้งแต่ 2026-08-09 — เก็บประวัติ 20 รายการ ·
`chat-gpt` เคยปิด 2026-08-08 แล้ว **เปิดกลับ 2026-08-09** เป็นบริการ VM 24 ชม.)

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

**บริการออนไลน์ (`Room.is_online`):** ห้องที่เป็นเครื่องเสมือน (`canva`, `canva2`, `chat-gpt`)
เข้าใช้แบบ RDP ไปที่เครื่องแม่ที่เปิด 24 ชม. **ไม่ต้องเข้าอาคาร ไม่มีอุปกรณ์ IoT ผูกอยู่**
- ใช้ `open_time`/`close_time` ของห้องเองทุกวัน **ไม่ถูกตัดด้วยเวลาเปิดอาคารหรือเวลาเสาร์-อาทิตย์**
  ปัจจุบันตั้งไว้ `00:00–23:59`
- **จองวันหยุดนักขัตฤกษ์ได้** (`HolidayDate` ไม่บล็อก) และ date picker ไม่ปิดวันหยุดให้ห้องกลุ่มนี้

**`Room.day_round_enabled`:** ปิดรอบกลางวันของห้องนั้นได้ ใช้เมื่อทรัพยากรถูกใช้ที่จุดบริการอื่น
ในเวลาราชการ — **ตอนนี้ไม่มีห้องไหนตั้งเป็น `False` แล้ว** (เคยใช้กับ `netflix1_vm` เพราะบัญชี Netflix
บัญชีเดียวถูกใช้ที่ Edutainment Zone ช่วงกลางวัน · ห้องนั้นปิดไปแล้ว 2026-08-09)
ฟีเจอร์ยังอยู่ในระบบพร้อมใช้ ติ๊กผ่าน `/manage/rooms/` (ห้าม hardcode booking_name ใน code)

**รอบบริการ (booking rounds):** แบ่ง 3 รอบต่อวันใน `service_hours.py` — **1 สิทธิ์ต่อห้อง ต่อรอบ**
| รอบ | เวลา |
|---|---|
| `early` เช้ามืด | `00:00–08:30` |
| `day` กลางวัน | `08:30–17:00` |
| `night` กลางคืน | `17:00–23:59` |
- **ห้องจริงพฤติกรรมไม่เปลี่ยน** เพราะเปิดเฉพาะช่วงกลางวัน การจองจึงตกอยู่ในรอบ `day` เสมอ
- **จองคร่อมรอบไม่ได้** (เช่น 16:00–18:30) เพราะนับสิทธิ์ไม่ได้ — ตรวจด้วย `round_of_range()`
- ขอบรอบเป็นของรอบก่อนหน้า: `06:00–08:30` = เช้ามืด · `08:30–10:00` = กลางวัน
- โควตานับด้วย `round_start_filter()` (กรองจาก `start_time`) แทน guard เดิมที่นับทั้งวัน
- นโยบายจากผู้ใช้ 2026-08-08: นอกเวลาถือเป็นสิทธิ์คนละรอบกับกลางวัน (ดู MEM.md)

**Overlap policy:** ผู้ใช้คนเดียว **ห้ามมีการจองที่ช่วงเวลาทับซ้อนกันข้ามห้อง ในวันเดียวกัน**
(คนเดียวอยู่สองที่ไม่ได้ ห้องที่เหลือจะถูกล็อกทิ้ง) ตรวจใน `create_booking()`
ภายใน `transaction.atomic()` เดียวกับ conflict check โดยใช้ `select_for_update()`
- ใช้เงื่อนไข "ทับจริง" (`start < other_end AND other_start < end`) — ต่อกันพอดีเช่น 10:00-11:00 กับ 11:00-12:00 **จองได้**
- ห้องที่ `Room.allow_overlap=True` ยกเว้น **ทั้งขาใหม่และขาเดิม** (พื้นที่กลุ่ม/พื้นที่เปิด)
  ปัจจุบันติ๊กไว้เฉพาะ `meeting_f1` — **ห้าม hardcode booking_name ใน code** เปลี่ยนผ่าน `/manage/rooms/`
- กติกา "จองได้ห้องละ 1 ครั้งต่อวัน" เดิมยังอยู่ — 2 กติกานี้ทำงานคนละหน้าที่
- ขอตามใบแจ้งทีม LRS ARC VM Gateway 2026-08-08 (ดู MEM.md)

**Advance booking policy:** จองล่วงหน้าได้ไม่เกิน `7` วันเปิดบริการ โดยข้าม `HolidayDate`
ที่ active รวมถึงเสาร์-อาทิตย์ที่สำนักประกาศปิดผ่านรายการวันหยุด
backend ใช้ `MAX_ADVANCE_DAYS` และ `max_advance_service_date()` เป็นค่ากลาง
แล้วส่ง `max_booking_date` ให้ date picker โดยตรง ส่วน `RoomClosure` ไม่หักจากโควตาของทั้งสำนัก

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

- **Room** — ห้องบริการ, `booking_name` เป็น unique key ใช้ใน URL · `allow_overlap` = ยอมให้คนเดียวจองทับเวลากับห้องอื่นได้ (ดู Overlap policy)
- **LineUser** — cache ผู้ใช้ที่ผูก LINE กับ LDAP แล้ว (source of truth อยู่ที่ api.npu.ac.th)
- **Booking** — การจอง, status: `confirmed` / `cancelled`
- **RoomDevice** — อุปกรณ์ Home Assistant `room` ว่างได้ = อุปกรณ์ส่วนกลางที่ไม่สังกัดห้องจอง (จับกลุ่มด้วย `group_name`)
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

**อุปกรณ์ส่วนกลาง (RoomDevice ที่ `room=None`):** อุปกรณ์ที่ไม่สังกัดห้องจอง เช่น flip gate ทางเข้า
จับกลุ่มด้วย `group_name` แสดงเป็นการ์ดแยกบนหน้า `/manage/iot-monitor/` ให้ staff กดเปิด-ปิดได้
**ไม่ปรากฏในระบบจองใด ๆ** เพราะ `room_status()`, `device_toggle()` และ auto-off ใน `send_reminders`
filter ด้วย `room=booking.room` ที่เป็นห้องจริงเสมอ อุปกรณ์กลุ่มจึงไม่เข้าเงื่อนไข
ตารางเวลาของอุปกรณ์กลุ่ม**ให้ Home Assistant automation คุมทั้งหมด** ฝั่ง Django ไม่มี logic เรื่องเวลา
(flip gate: HA เปิด 07:20 ปิด 17:00 ต่างจากห้องจองที่ automation `Close ALL` ปิด 16:30)
หน้า monitor + refresh + แจ้งกลุ่ม LINE + `morning_iot_report` ใช้ helper กลางตัวเดียวคือ
`_iot_cards()` ใน `booking/manage_views.py` — เพิ่ม/แก้การจัดกลุ่มให้แก้ที่นี่ที่เดียว
เพิ่ม-ลบอุปกรณ์กลุ่มผ่าน Django Admin (`/admin/`) เพราะไม่มีหน้าห้องให้จัดการ

**หมายเหตุ:** ตาราง Phase ด้านบนสรุปจาก codebase ณ วันที่ sync เอกสาร ควรตรวจ production deployment แยกต่างหากก่อนประกาศฟีเจอร์ใหม่

---

## Deploy (Windows Server)

```bash
# ⚠️ production มี venv — ห้ามเรียก `python` / `pip` เปล่า ๆ (จะได้ ImportError: Couldn't import Django)

# 1. ติดตั้ง dependencies
.\venv\Scripts\pip.exe install -r requirements.txt

# 2. Database
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser

# 3. Static files
.\venv\Scripts\python.exe manage.py collectstatic --noinput

# 4. NSSM service (production จริงอยู่ที่ C:\project\reserv — ไม่ใช่ C:\projects\)
c:\nssm\nssm.exe install Reserv "C:\project\reserv\venv\Scripts\python.exe" "C:\project\reserv\deploy\waitress_serve.py"
c:\nssm\nssm.exe set Reserv AppDirectory "C:\project\reserv"
c:\nssm\nssm.exe start Reserv
```

**เมื่อ pull code ใหม่ขึ้น production:** หากมีการแก้ Python code ต้อง restart service
ก่อนทดสอบ เพื่อให้ Waitress โหลด code ชุดใหม่ — ถ้าแก้แต่ข้อมูล/static ไม่ต้อง restart

```powershell
cd C:\project\reserv
git pull origin master
.\venv\Scripts\python.exe manage.py collectstatic --noinput
c:\nssm\nssm.exe restart Reserv
```

> **ชื่อ NSSM service คือ `Reserv`** (ยืนยันบนเซิร์ฟเวอร์ 2026-08-08 — เอกสารเก่าที่เขียน `reserv-booking` ผิด)

**Reverse proxy คือ IIS + ARR ไม่ใช่ Nginx** — `web.config` rewrite `^reserv/(.*)` → `127.0.0.1:8003`
static ทั้งหมด serve ด้วย **WhiteNoise** ผ่าน Waitress **ห้ามตั้ง rule แยกให้ `/reserv/static/`**
(เคยทำแล้ว admin CSS หาย — ดู [doc/deploy_guide.md](doc/deploy_guide.md))

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

## กติกาการปิด session
ก่อนจบงานทุกครั้ง ให้อัปเดตบล็อก <!-- PROJECT-STATUS --> ด้านบนของไฟล์นี้:
ปรับ progress, phase, รายการ next ให้ตรงกับงานจริง และแก้ updated เป็นวันที่ปัจจุบัน
จากนั้นรัน `python C:\projects\project_status.py` เพื่ออัปเดต dashboard รวม

## กติกาการเปิด session (เตือนงานค้าง — อย่าให้ผู้ใช้ต้องเตือนเอง)
ตอนเริ่มงานกับโปรเจกต์นี้ **ให้อ่านบล็อก `next:` และ `risks:` ใน PROJECT-STATUS ก่อน**
แล้ว**เอ่ยเตือนงานค้างที่ค้างมานาน โดยเฉพาะเรื่อง security/risks** ให้ผู้ใช้รับรู้เอง — ไม่ต้องรอให้ผู้ใช้นึกออก
(เทียบวันใน `updated` กับวันนี้ ถ้าเป็นสัปดาห์+ ให้หยิบมาย้ำ) ผู้ใช้ขอไว้ชัด (2026-07-22): "ลืมนานฉันจะต้องเตือนเธอ" = หน้าที่เตือนเป็นของ Claude/Codex
ตัวอย่างงานค้างที่ต้องคอยเตือน ณ ตอนตั้งกติกา: **แจ้งทีม api เรื่อง `/std-info/` เปิด public + leak `apassword`**
(งานตัวอย่างนี้ปิดแล้ว 2026-07-23 — ฝั่ง api ถอด `apassword` + ปิดสิทธิ์เขียน + ปิด list เรียบร้อย เก็บไว้เป็นตัวอย่างของกติกา)
