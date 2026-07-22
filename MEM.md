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

### 2026-07-22 — `/card-login/` กระพริบเปล่า เพราะฟอร์ม POST ทับ `?logout=1`
**อาการ:** นักศึกษากรอกรหัสถูก กด "เข้าสู่ระบบ" แล้วจอกระพริบ ไม่มี error ไม่มี QR
**สาเหตุ:** `<form method="post">` ไม่ระบุ `action` → POST กลับ URL ปัจจุบัน ถ้าผู้ใช้เพิ่งกด "ออกจากระบบ"
มา URL จะค้าง `?logout=1` view เช็ค `request.GET.get('logout')` **โดยไม่ดู method** เลยเข้า branch logout
คืนฟอร์มเปล่าก่อนถึงขั้นตรวจรหัส
**แก้:** (1) logout เช็คเฉพาะ `method=='GET'` (2) form ระบุ `action={% url 'card_login' %}` ให้ POST ไป URL สะอาดเสมอ
**บทเรียน:** ระวัง handler ที่อ่าน GET param บน POST request + ฟอร์มที่ไม่ระบุ action จะพา query string เก่าติดไปด้วย

### 2026-07-22 — rate limit ต่อ IP ล็อกทั้งวิทยาเขต (ผู้ใช้แชร์ IP ผ่าน NAT)
เวอร์ชันแรกนับ fail ต่อ IP → เพราะนักศึกษาทั้งมหาลัย/คนใช้ 4G ออกเน็ตผ่าน IP สาธารณะเดียวกัน
คนเดียวพิมพ์ผิดครบโควตา = ล็อกทุกคนหลัง IP นั้น **แก้:** นับต่อ "บัญชี" (`card_login_fail:u:<ldap>`) เท่านั้น
5 ครั้ง/5 นาที · **บทเรียน:** อย่า rate-limit ต่อ IP กับผู้ใช้ที่อยู่หลัง NAT องค์กร
(เคยเข้าใจผิดว่านักศึกษาล็อกอิน AD ไม่ได้ — จริง ๆ LDAP ปกติ ตรวจ DB พบนักศึกษาผูก LINE สำเร็จ 76 คนใน 7 วัน)

### 2026-07-22 — ⚠️ (ฝั่ง api) `/std-info/`,`/staff-info/` เปิด public + leak `apassword`
ยิง `GET https://api.npu.ac.th/std-info/{รหัสนักศึกษา}/` **โดยไม่ต้องมี auth header** ได้ HTTP 200
พร้อมชื่อ-นามสกุล-คณะ-สาขา และมี field **`apassword`** (ค่า 4 หลัก plaintext ไม่ใช่ hash)
ใครรู้รหัสนักศึกษา 12 หลักก็ดูข้อมูลคนนั้นได้ **เป็นงานฝั่ง api (ไม่ใช่ reserv)** — ควรถอด field `apassword`
และ/หรือใส่ auth · reserv ใช้ endpoint นี้ผ่าน `_fetch_npu_profile()` (แต่ `/card-login/` ตัวใหม่ไม่เรียกแล้ว)

## การตัดสินใจ

### 2026-07-22 — QR เข้าประตูของ "คนใน" คือ user_ldap เปล่า ๆ (ทำให้ทำหน้า login นอก LINE ได้)
หน้า `/card/` (LIFF) วาด QR จาก `userData.userLdap` ตรง ๆ ([card.html:488](booking/templates/booking/card.html))
— **ไม่มี token/วันหมดอายุ/อะไรที่ผูกกับ LINE** เลข `user_ldap` = รหัสนักศึกษา (12 หลัก) หรือเลขบัตร ปชช. บุคลากร (13 หลัก)
**นัยสำคัญ:** ประตูสแกนแค่ "สตริง user_ldap" ดังนั้นทำหน้าไหนก็ได้ที่ยืนยันตัวตนแล้ววาด QR จากสตริงเดียวกัน
ก็เข้าประตูได้เท่ากัน — นี่คือรากฐานของ `/card-login/` (login AD บนเว็บ ไม่ต้องมี LINE)
**ผลข้างเคียงเชิงความปลอดภัย:** QR ปลอมง่ายอยู่แล้ว (รู้ user_ldap เพื่อน → สร้าง QR เองในแอปฟรี = เข้าได้)
password ที่หน้า card-login จึงกันได้แค่คนที่ไม่รู้ว่าทำแบบนั้นได้ ถ้าประตูเช็คแค่ "รหัสมีในระบบ" ก็อ่อนอยู่แล้ว
(ยังไม่รู้ว่าประตูตรวจอะไรตอนสแกน — อยู่นอก codebase reserv)

### 2026-07-22 — "จดจำฉันไว้" ใช้ signed cookie แยก ห้ามใช้ Django session
`SESSION_COOKIE_AGE=86400` (24 ชม.) และ session ก้อนนี้ **Staff Portal `/manage/` ใช้อยู่**
ถ้าไป `request.session.set_expiry(90 วัน)` ในหน้า card-login → **ยืดอายุ session ของ staff** ที่ล็อกอินในเครื่องเดียวกันไปด้วย = ลดความปลอดภัย Staff Portal โดยไม่ตั้งใจ
**ทางเลือกที่ใช้:** `set_signed_cookie('card_ldap', user_ldap, ...)` แยกก้อน เก็บแค่ user_ldap (ไม่เก็บ password)
httponly + samesite=Lax + secure ตาม `request.is_secure()` — sign ด้วย SECRET_KEY แก้ไขแล้วระบบปฏิเสธ

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

### 2026-07-22
- ✅ **หน้า `/card-login/` — ล็อกอิน AD บนเว็บ ออก QR เข้าประตู ไม่ต้องเป็นเพื่อน LINE OA** (deploy + เทส prod ผ่านทั้งนักศึกษา+บุคลากร)
  - โครงเลียนแบบ `external_access()` — server-rendered ล้วน **ไม่ยุ่ง LIFF เลย** (ตรวจ AD คนละเรื่องกับ LINE)
  - `card_login()` + template [card_login.html](booking/templates/booking/card_login.html) + route ใน [booking/urls.py](booking/urls.py) — **เพิ่มล้วน ไม่แตะไฟล์เดิม / ไม่มี migration / ไม่แตะ api**
  - ทำงานแค่ 2 ขั้น: `_verify_ldap()` → ออก QR (เดิมเคยดึงโปรไฟล์+เช็ค Walai แต่ผู้ใช้ขอตัดออก เอาแค่ QR เข้าประตู)
  - QR = `user_ldap` ตัวเดียวกับหน้า `/card/` (params เดียวกันเป๊ะ: 180px, colorDark `#0d1f3c`, correctLevel M) → ประตูสแกนได้เหมือนกัน ผู้ใช้ไม่สังเกตความต่าง
  - "จดจำ 90 วัน" = **signed cookie แยก** (`card_ldap`) เก็บแค่ user_ldap ไม่เก็บ password · เปิดครั้งต่อไปได้ QR เลยไม่ยิง api
  - `@never_cache` กัน proxy/CDN cache หน้าที่โชว์เลขบัตร ปชช. · rate limit ต่อบัญชี 5/5นาที ผ่าน Django cache
  - push ชุด `7f4f908`→`c044203` → origin/master · unittest reserv 17/17 ผ่าน · เทส prod ผ่าน (นักศึกษา+บุคลากร)
  - ⚠️ ยังไม่มี test ของหน้านี้ใน tests.py (เทสผ่าน test-client สคริปต์ชั่วคราวตอนพัฒนาเท่านั้น)
  - ✅ **สรุป: งานฝั่ง reserv สมบูรณ์ ณ 2026-07-22** — login AD → ออก QR ทำงานถูกต้องครบ deploy prod แล้ว
- ✅ คู่มือช่องทางขอ QR เข้าประตู (4 ช่องทาง A-D) [doc/door-qr-guide.docx](doc/door-qr-guide.docx) — สร้างด้วย docx-js + แคปหน้าจอ headless Chrome 16:9
- 📌 **เคส "ประตูสแกน QR คนในแล้วไม่เปิด" = เรื่องฝั่งประตู ไม่ใช่ reserv** (แก้/จบฝั่งประตูแล้ว)
  - ตรวจแล้ว: QR ของ `/card-login/` = `/card/` ทุกตัวอักษร (= user_ldap), reserv ไม่มี logic ตรวจประตูเลย (แค่วาด QR)
  - `/v2/external/check/` ([apiproject apiapp/views_v2.py:432](../apiproject/apiapp/views_v2.py)) เป็น endpoint เดียวที่ตอบ `{allow}` ให้ประตู — ตรวจแค่รหัส pool รายวัน + permanent_code (คนนอก) **ไม่มีกรณีตรวจ user_ldap คนใน**
  - บทเรียน: "reserv วาด QR ได้" ≠ "ประตูรับ QR นั้น" — การ verify อยู่ฝั่งประตู/api คนละส่วนกัน ถ้าจะรองรับ QR คนในต้องเพิ่มกรณีใน check_external ฝั่ง apiproject (ผู้ใช้สั่งไม่ต้องแก้ 2026-07-22)

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
