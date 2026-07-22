# Progress 2026-07-20 — หน้า `/card-login/` ออก QR โดยไม่ต้องเป็นเพื่อน LINE OA

แก้โดย: **Claude Code edit**
สถานะ: ✅ **deploy prod + เทสจริงผ่านทั้งนักศึกษา+บุคลากร (2026-07-22)** — push ชุด `7f4f908`→`c044203`

> อัปเดต 2026-07-22: หลัง deploy พบและแก้เพิ่ม — logout ทับ POST ทำจอกระพริบ, rate-limit
> ต่อ IP ล็อกทั้งวิทยาเขต (เปลี่ยนเป็นต่อบัญชี), `@never_cache` กันแคชหน้าโชว์เลขบัตร,
> และตัดการดึงโปรไฟล์/Walai ออกตามที่ผู้ใช้ขอ (เอาแค่ QR). รายละเอียดใน MEM.md 2026-07-22

---

## โจทย์

เดิมผู้ใช้ต้องเป็นเพื่อนกับ LINE OA ของห้องสมุดก่อน แล้วกดเมนูโปรไฟล์ ถึงจะเข้าหน้า
ลงทะเบียน/บัตรได้ แต่มีผู้ใช้บางกลุ่ม**มาเพื่อใช้พื้นที่อย่างเดียว ไม่ต้องการรับข่าวสาร**
จึงไม่อยากแอด OA

ต้องการ: หน้าล็อกอิน AD แบบ public ที่ออก QR สแกนประตูได้ **โดยไม่ยุ่งกับ LIFF เลย**
จองห้องไม่ได้ (การจองยังต้องผ่าน LIFF เหมือนเดิม)

## สิ่งที่พบตอนสำรวจ (จุดตัดสินใจ)

**1. QR ในหน้า `/card/` คือ `user_ldap` เปล่าๆ** — `card.html:488`

```js
// แสดง QR ทันทีจาก userLdap — ทุกคนที่ authen ผ่านมีสิทธิ์ใช้ห้องสมุด
renderQR(userData.userLdap);
```

ไม่มี token / ไม่มีวันหมดอายุ / ไม่เกี่ยวกับ LINE → หน้าใหม่ที่รู้ `user_ldap`
สร้าง QR ที่**สแกนแล้วเหมือนกันทุกประการ**ได้ทันที ประตูไม่รู้ความต่าง

**2. `_verify_ldap()` ไม่ได้ใช้ `user_type` ตรวจอะไร** — ส่งไปเพื่อ log ฝั่ง Monitor เท่านั้น
ที่ต้องใช้จริงคือ `_fetch_npu_profile()` ที่เอาไปเลือก URL `std-info` / `staff-info`
→ เดาเองได้ ไม่ต้องให้ผู้ใช้เลือก และตัดโหมดพัง "เลือกผิด → บัตรชื่อว่าง" ทิ้ง

**3. สร้าง `LineUser` ให้คนกลุ่มนี้ไม่ได้** — `line_user_id` เป็น `unique=True` บังคับมีค่า
และ `Booking.line_user` เป็น FK บังคับ → **ตัวตนของทุก booking คือ LINE userId**
จึงเป็นเหตุผลเชิงโครงสร้างที่หน้านี้จองห้องไม่ได้ (ไม่ใช่แค่นโยบาย)

## สิ่งที่ทำ — เพิ่มล้วน ไม่แตะของเดิม

| ไฟล์ | การเปลี่ยนแปลง |
|---|---|
| `booking/templates/booking/card_login.html` | **ใหม่** — CSS คัดลอกจาก `card.html` ให้หน้าตาตรงกัน |
| `booking/views.py` | เพิ่ม `card_login()` + `_client_ip()` + `_fetch_npu_profile_auto()` + `_walai_status()` |
| `booking/urls.py` | เพิ่ม `path('card-login/', ...)` 1 บรรทัด |

**ไม่แตะ:** `card.html`, `register.html`, `landing.html`, `walai_card()`, models, migration,
LIFF setting — ศูนย์ (ยืนยันด้วย `git status`: แก้ไฟล์เดิมแค่ 2 ไฟล์)

### Flow

```
เปิด /reserv/card-login/ (ไม่ต้อง LINE)
  → ฟอร์ม: รหัสผู้ใช้ + รหัสผ่าน (ไม่มีช่องเลือกประเภท)
  → _verify_ldap()          ❌ ผิด → error + นับ rate limit
  → _fetch_npu_profile_auto()  เดาประเภทเอง
  → _walai_status()            เช็คสมาชิกฝั่ง server
  → render บัตร + QR จาก user_ldap
```

### รายละเอียดที่ควรรู้

- **QR params ตรงกับ `card.html:421` ทุกตัว** — `width/height 180`, `colorDark #0d1f3c`,
  `correctLevel M` — ผู้ใช้จะไม่สังเกตความต่าง
- **ไม่มีรูปโปรไฟล์** เพราะ `card.html:454` ใช้ `profile.pictureUrl` จาก LINE ซึ่งไม่มี
  → ตกไปใช้ `.profile-avatar-placeholder` (👤) ที่มีอยู่แล้วใน design เดิม
- **ป้าย Walai** เรียก `/walai/check_user_walai/` จากใน view โดยตรง เพราะ `walai_card():1213`
  บังคับผ่าน `_get_active_line_user()` ซึ่งคนกลุ่มนี้ไม่มี — ไม่ได้แก้ endpoint เดิม
- **Rate limit** 5 ครั้ง/IP/5 นาที ผ่าน Django cache นับเฉพาะที่ผิดจริง
  ล็อกอินสำเร็จล้างตัวนับ · อ่าน IP จาก `X-Forwarded-For` ก่อนเพราะอยู่หลัง nginx
- **Stateless** — ไม่เขียน DB อะไรเลย แสดงบัตรแล้วจบ (ผู้ใช้ยืนยันว่าไม่ต้องการเก็บสถิติ)

### การเดาประเภทผู้ใช้

ใช้จำนวนหลักเป็น**ลำดับการลอง** ไม่ใช่การฟันธง — ถ้าอันแรกไม่เจอยังยิงอีกทางเสมอ

```python
STUDENT_LDAP_LEN = 12   # 12 หลัก = นักศึกษา, นอกนั้น = บุคลากร
```

## การทดสอบ

`python manage.py check` → ผ่าน (0 issues)

**QR วาดจริงบน browser** (`javascript_tool` บน dev server):
```
{ libLoaded: true, drew: true, tag: "CANVAS", w: 180 }
```

**Rate limit** (mock `_verify_ldap` ไม่ได้ยิง AD จริง):
```
attempt 1-5: rate_limited=False  ldap_calls=1..5
attempt 6:   rate_limited=True   ldap_calls=5   ← หยุดยิง LDAP
attempt 7:   rate_limited=True   ldap_calls=5
blocked even w/ correct pw: True | ldap called while blocked: 0
```

**เดาประเภท:**

| กรณี | รหัส | ผล | ยิง API |
|---|---|---|---|
| นักศึกษา 12 หลัก | `640112345678` | นักศึกษา | 1 |
| บุคลากร 13 หลัก | `3489900017383` | บุคลากร | 1 |
| บุคลากร ตัวอักษร | `surayuth` | บุคลากร | 1 |
| นศ. 10 หลัก (นอกแพตเทิร์น) | `6401234567` | นักศึกษา | 2 |
| บุคลากร 12 หลัก (นอกแพตเทิร์น) | `123456789012` | บุคลากร | 2 |
| ไม่พบทั้งสองทาง | — | `(None, '')` → แสดง `ผู้ใช้บริการ` | 2 |

**หน้าเดิมไม่กระทบ:** `/card/` `/register/` `/` `/external/` `/card-login/` → 200 ทั้งหมด

## งานค้าง

- [ ] **ทดสอบกับ AD จริงบน prod** — ที่ผ่านมา mock `_verify_ldap()` ทั้งหมด
      ต้องลองล็อกอินด้วยบัญชีจริง **ทั้งนักศึกษาและบุคลากรอย่างละคน**
      แล้วเอา QR ไปสแกนประตูจริง
- [ ] deploy: `git pull` แล้ว **`nssm restart reserv-booking`** ก่อนทดสอบ (แก้ Python code)
- [ ] ประชาสัมพันธ์ URL `/reserv/card-login/` (ทำป้าย/QR ติดหน้าประตูได้)

## หมายเหตุ

- **ไม่เกี่ยวกับ api.npu.ac.th** — endpoint ที่ใช้ (`/auth-ldap/`, `/std-info/`, `/staff-info/`,
  `/walai/check_user_walai/`) มีอยู่แล้วและระบบเดิมเรียกอยู่แล้วทั้งหมด ไม่ต้องรอฝั่ง api
- **rate limit ผูกกับ cache backend** — ตอนนี้เป็น LocMemCache (per-process)
  production รัน `waitress --threads=4` = 1 process จึงทำงานถูกต้อง
  ถ้าวันไหนเพิ่มเป็นหลาย process/หลายเครื่อง ต้องย้ายไป Redis หรือ DB cache
- ตัดสินใจ **ไม่ใส่ปุ่มชวนแอด LINE OA** ตามที่ผู้ใช้ระบุ — กลุ่มเป้าหมายคือคนที่
  ตั้งใจไม่รับข่าวสาร การชวนแอดจะขัดเจตนา
