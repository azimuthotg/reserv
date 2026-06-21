# คู่มือ/แจ้งทุกทีม: ระบบบุคคลภายนอกเข้าห้องสมุด (รายวัน + ถาวร)

**วันที่:** 2026-06-21
**สถานะ:** รายวัน = ใช้งานจริงบน prod แล้ว · ถาวร = โค้ดเสร็จ push แล้ว **รอ deploy + ทดสอบ**
**ทีมที่เกี่ยวข้อง:** api (backend) · reserv (เว็บ/Staff Portal) · ประตู (เครื่องอ่าน)

---

## 0. ภาพรวม

บุคคลภายนอก (ไม่ใช่ นศ./บุคลากร ไม่มีใน AD) เข้าใช้ห้องสมุดผ่าน **QR/รหัส 10 หลัก** สแกนที่ประตู
มี 2 ประเภท:

| | รายวัน (daily) | ถาวร (permanent) |
|---|---|---|
| กลุ่มเป้าหมาย | คนทั่วไป มาครั้งคราว | คนเข้าประจำ เช่น พนักงานส่งเอกสาร |
| ลงทะเบียน | ผู้ใช้ทำเองที่หน้าเว็บ | **ผู้ใช้ทำเอง** (แนบรูป) — เจ้าหน้าที่แค่อนุมัติ |
| อนุมัติ | อัตโนมัติ | เจ้าหน้าที่ reserv อนุมัติก่อน |
| รหัส | 10 หลัก ใช้ได้เฉพาะวันนั้น | 10 หลัก คงที่ ใช้ได้ทุกวันจนกว่าจะระงับ |
| รูปถ่าย | ไม่มี | มี (บัตรบนจอมีรูป บอกว่าเป็นคนภายนอกถาวร) |
| สถานะ | ✅ prod แล้ว | ⏳ รอ deploy |

```
รายวัน:   [ผู้ใช้] เว็บ /external/           → reserv backend(JWT) → api /v2/external/issue/ → QR (วันนี้)
ถาวร:     [ผู้ใช้] เว็บ /external/permanent/  → reserv backend(JWT) → api .../permanent/register → pending
          [เจ้าหน้าที่] /manage/external/ กด "อนุมัติ" → ออก permanent_code
          [ผู้ใช้] กรอกเลขบัตรซ้ำที่ /external/permanent/ → เห็นบัตร (รูป+QR)
ประตู:    [traceon] สแกน QR ได้รหัส 10 หลัก → api /v2/external/check/<code>/ (JWT ประตู) → 200=เปิด
```

ทุกการเรียก api เป็น **v2 ต้องแนบ JWT** (`Authorization: Bearer <access_token>`) แต่ละระบบใช้บัญชี/token ของตัวเอง

---

## 1. ทีม API ต้องรับทราบ / ทำอะไร

### 1.1 สิ่งที่เพิ่มเข้ามา (commit `14b6a31`, migration `0010`)
- `ExternalMember` เพิ่ม field: `member_type` (daily/permanent), สถานะ `pending`, `permanent_code` (10 หลักคงที่), `photo`, `approved_at`, `approved_by`
- endpoint ใหม่ใต้ `/v2/external/permanent/...` (register/list/detail/approve/revoke/photo)
- แก้ `check_external` ให้รับ `permanent_code` ด้วย (แบบ additive — ของเดิมไม่กระทบ)
- `settings.py` เพิ่ม `MEDIA_ROOT`/`MEDIA_URL` (เก็บไฟล์รูป)

### 1.2 ขั้น deploy (prod)
```bash
git pull origin main
python manage.py migrate apiapp          # apply 0010
# ตรวจว่าโฟลเดอร์ media/ มีและเขียนได้ (รูปอัปโหลดไปไว้ที่ media/external_member_photos/)
restart api service (ตาม deploy.ps1 / app pool ปกติ)
```
> **รูปไม่ต้องเปิด nginx /media/ สาธารณะ** — reserv ดึงรูปผ่าน endpoint ที่ต้องใช้ JWT แล้ว proxy ให้ผู้ใช้เอง (กัน PII หลุด)

### 1.3 Monitor — ดูการใช้งานยังไง
ทุก endpoint ของ external ติด `ApiAccessLogMixin` → โผล่ในหน้า **`https://api.npu.ac.th/monitor/api-usage/`**
ดูได้ว่า:
- **ระบบไหนเรียก** (`client_user` = จาก token เช่น reserv / door)
- **endpoint อะไร**: `ExternalAccessViewSetV2.issue` (ออกรหัสรายวัน), `.check_external` (ประตูเช็ค), `.permanent_register/.permanent_approve/...` (จัดการสมาชิกถาวร)
- **ผล**: http_status + result (success/fail) + reason_code (เช่น invalid_citizen_id, revoked, pool_full, not_valid_today)

ใช้สืบย้อนได้ว่า "ใครออก/อนุมัติ/เช็ครหัสให้ใคร เมื่อไร ผลเป็นยังไง"

### 1.4 ที่ api อาจต้องปรับเพิ่ม (ถ้าทีมอื่นร้องขอ)
- รูปแบบ response ของ `check` (ถ้าประตูอยากได้ 200 เสมอแล้วดู `allow` — ดูข้อ 3.3)
- ขยาย pool รายวันถ้าคนเกิน ~50/วัน (`seed_access_codes --count`)

---

## 2. ทีม reserv ต้องทำอะไร

### 2.1 สิ่งที่เพิ่มเข้ามา (commit `1d0ad51`)
- หน้าสาธารณะรายวัน `/reserv/external/` (มีบน prod แล้ว)
- หน้า Staff Portal สมาชิกถาวร `/reserv/manage/external/` (list / register+photo / detail-บัตร / approve / revoke / photo-proxy)
- token layer เรียก api v2 (helper `_npu_v2_*` ใน `booking/views.py`)

### 2.2 env ที่ต้องมี (ตั้งแล้วบน prod)
```
NPU_API_USERNAME=<บัญชี reserv>     # reserv ขอ/ต่ออายุ JWT เองอัตโนมัติ
NPU_API_PASSWORD=<รหัส>
# (NPU_API_V2_TOKEN เว้นว่าง)
```

### 2.3 ขั้น deploy (prod)
```bash
git pull origin master
nssm restart reserv-booking
python manage.py check_npu_v2            # ยืนยัน token ใช้ได้ (obtain ✅ + HTTP 404)
```

### 2.4 หน้าที่เจ้าหน้าที่ (สมาชิกถาวร) — เน้น "อนุมัติ"
**ผู้ใช้ลงทะเบียนเอง**ที่หน้าสาธารณะ `/reserv/external/permanent/` (กรอกชื่อ-สกุล+เลขบัตร+แนบรูป → pending)
เจ้าหน้าที่ที่ `https://lib.npu.ac.th/reserv/manage/external/` (login Staff Portal):
1. ดูรายการ "รออนุมัติ" → เปิดหน้าบัตร → กด **อนุมัติ** → ระบบออกรหัสถาวร
2. ผู้ใช้กลับไปกรอกเลขบัตรซ้ำที่ `/external/permanent/` เพื่อรับบัตร (รูป+QR) บนจอ
3. **ระงับ** เมื่อไม่ให้เข้าแล้ว → รหัสใช้ไม่ได้ทันที
4. (ตัวเลือก) เจ้าหน้าที่ **ลงทะเบียนแทน**ได้ที่ `/manage/external/register/` บางเคส
> รายวัน: เจ้าหน้าที่ไม่ต้องทำอะไร ผู้ใช้ทำเองที่ `/reserv/external/`

---

## 3. ทีมประตู (ระบบ `traceon`) ต้องทำอะไร  ⚠️ (ยังไม่ได้แจ้ง — ต้องเคลียร์ก่อนปิดงาน)

### 3.1 หลักการ
ประตูคือระบบ **`traceon`** (มี JWT v2 ของตัวเองอยู่แล้ว) — สแกน QR → ได้สตริงรหัส แล้ว route ตามความยาว:
- **10 หลัก → external (อันนี้)** `GET /v2/external/check/<code>/`  ← **traceon ต้องเพิ่ม route นี้**
- 12 หลัก → นักศึกษา `/v2/student/<id>/` (ทำอยู่แล้ว)
- 13 หลัก → บุคลากร `/v2/personnel/<id>/` (ทำอยู่แล้ว)

**convention = ดู HTTP status: 200 = เปิดประตู** (ยืนยันจาก Monitor: traceon เปิดเมื่อ retrieve คืน 200)
→ `check_external` ของเราคืน **200 เฉพาะตอน allow:true** อยู่แล้ว → **เข้ากันได้ทันที ไม่ต้องแก้ api และไม่ต้องเปลี่ยน logic ฝั่ง traceon** (แค่ชี้ 10 หลักมา endpoint นี้)

### 3.2 endpoint ที่ต้องเรียก
```
GET  https://api.npu.ac.th/v2/external/check/<code>/
Header: Authorization: Bearer <JWT ของทีมประตู>
```
ตัวอย่าง:
```bash
curl -H "Authorization: Bearer <door_token>" \
     https://api.npu.ac.th/v2/external/check/1084281961/
```
Response:
```
200  {"allow": true,  "member": {"citizen_id":"...","first_name":"...","last_name":"..."}, "api_version":"v2"}
        (สมาชิกถาวรจะมี "member_type":"permanent" เพิ่มมาด้วย)
404  {"allow": false, "detail": "Code not valid today"}        ← รหัสไม่ถูกใช้วันนี้ / มั่ว
403  {"allow": false, "detail": "Member revoked or not found"} ← ถูกระงับ
403  {"allow": false, "detail": "Permanent member not active"} ← สมาชิกถาวรถูกระงับ/ยังไม่อนุมัติ
```
> **endpoint เดียวรองรับทั้งรหัสรายวันและถาวร** — ถ้าประตูต่อระบบรายวันไว้แล้ว ถาวรทำงานทันทีไม่ต้องแก้โค้ด

### 3.3 สิ่งที่ traceon ต้องทำ/ยืนยัน
- [ ] **เพิ่ม route: รหัส 10 หลัก → `GET /v2/external/check/<code>/`** (ใช้ JWT เดิมของ traceon, อ่าน 200=เปิด เหมือน นศ./บุคลากร)
- [x] convention = HTTP 200 = เปิด (ยืนยันแล้วจาก Monitor — ไม่ต้องเปลี่ยน)
- [ ] ทดสอบ: รหัสจริง→200 เปิด, รหัสมั่ว→404 ไม่เปิด, รหัสที่ถูกระงับ→403 ไม่เปิด

---

## 4. URL อ้างอิงรวม

| ใคร | URL | auth |
|---|---|---|
| ผู้ใช้ภายนอก (รายวัน) | `https://lib.npu.ac.th/reserv/external/` | ไม่ต้อง (public) |
| ผู้ใช้ภายนอก (ถาวร ขอ/ดูบัตร) | `https://lib.npu.ac.th/reserv/external/permanent/` | ไม่ต้อง (public) |
| เจ้าหน้าที่ (อนุมัติถาวร) | `https://lib.npu.ac.th/reserv/manage/external/` | Staff login |
| ประตู traceon (เช็ครหัส) | `https://api.npu.ac.th/v2/external/check/<code>/` | JWT traceon |
| reserv backend ออกรหัสรายวัน | `https://api.npu.ac.th/v2/external/issue/` | JWT reserv |
| reserv backend จัดการถาวร | `https://api.npu.ac.th/v2/external/permanent/...` | JWT reserv |
| ขอ JWT | `https://api.npu.ac.th/v2/token/` | username/password |
| Monitor การใช้งาน | `https://api.npu.ac.th/monitor/api-usage/` | รหัสผ่านร่วม |

---

## 5. Checklist ทดสอบ end-to-end (หลัง deploy ทั้ง 2 repo)

**รายวัน (มีบน prod แล้ว — ทวนซ้ำได้):**
1. `/reserv/external/` กรอกเลขบัตรจริง → ได้ QR + valid_date = วันนี้
2. ประตูเช็ครหัสนั้น → `allow:true`
3. รหัสมั่ว → `allow:false` (404) · รหัสเมื่อวาน → `allow:false`

**ถาวร (ทดสอบหลัง deploy):**
4. `/reserv/external/permanent/` กรอกชื่อ-สกุล+เลขบัตร+รูป → สถานะ pending
5. `/reserv/manage/external/` เจ้าหน้าที่กด **อนุมัติ** → ได้ permanent_code
6. ผู้ใช้กรอกเลขบัตรซ้ำที่ `/external/permanent/` → เห็นบัตร (รูป+QR)
7. ประตู (traceon) เช็ค permanent_code → 200 เปิด **ทดสอบข้ามวันด้วย** (พรุ่งนี้ต้องยัง 200)
8. กดระงับ → ประตูเช็คอีกครั้ง → 403 ไม่เปิด ทันที
9. ดู `/monitor/api-usage/` ว่าทุก call ขึ้น log พร้อมระบบ=reserv/traceon

---

## 6. เรื่องที่ยังเปิด / ความเสี่ยงที่ต้องรู้

- **ต้องแจ้ง traceon** (ข้อ 3) — เร่งสุด: ให้เพิ่ม route 10 หลัก → `/v2/external/check/` (convention 200=เปิด ตรงกับที่ traceon ทำอยู่แล้ว ไม่ต้องแก้ logic)
- **บัตรถาวร = เสมือนบนจอ** (รูป+QR ที่ `/external/permanent/`) ตามที่ตกลง — ยังไม่มีวันหมดอายุ (ถาวรจนกว่าจะระงับ)
- **ความจุ pool รายวัน** 100/วัน (รับ ≤ ~50 คน/วันสบาย) — เกินกว่านี้ขยายที่ api (`seed_access_codes --count`)
- **ความเสี่ยงยอมรับได้:** QR รายวันแคปหน้าจอแชร์กันในวันเดียวกันได้ (กันแค่ข้ามวัน); บัตรถาวรดูได้โดยกรอกเลขบัตรของตน (รูปฝังเป็น data URI ไม่มี URL รูปสาธารณะ)
