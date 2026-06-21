# Handoff (ย้อนกลับ): สมาชิกภายนอก "ถาวร" → ทีม api

**จาก:** โปรเจกต์ reserv  **ถึง:** โปรเจกต์ api (backend)
**วันที่:** 2026-06-21  **สถานะ:** ขอให้ api เพิ่ม logic ก่อน reserv จึงทำหน้าจัดการต่อได้

---

## 1. ที่มา

ตอนนี้ external member รองรับเฉพาะ **รหัสหมุนเวียนรายวัน** (`ExternalAccessViewSetV2.issue` + pool `ExternalAccessCode`)
ทำเสร็จ + ทดสอบ prod ผ่านแล้ว (หน้า reserv `/external/` 2026-06-21)

มีความต้องการเพิ่ม: **"สมาชิกภายนอกถาวร"** — เช่น พนักงานส่งเอกสาร/ผู้รับเหมา ที่ต้องเข้าใช้ประจำ
ลงทะเบียนครั้งเดียว → admin อนุมัติ → ได้รหัส/บัตร **ถาวร** ใช้ได้ทุกวันจนกว่า admin จะระงับ

**การตัดสินใจฝั่ง reserv (สรุปกับผู้ใช้แล้ว):**
- รหัสเป็น **ถาวรคงที่** (ไม่หมุน pool รายวัน)
- ต้อง **admin approve ก่อน** ถึงใช้ได้
- admin จัดการที่ **หน้า `/manage/` ของ reserv** (reserv เป็นคนทำ UI)
- ระบุตัวตนด้วย **ชื่อ + นามสกุล + เลขบัตร 13 หลัก + รูปถ่าย** (จะออกเป็น "บัตร")

---

## 2. สิ่งที่ขอให้ api เพิ่ม

### 2.1 ขยาย model `ExternalMember`
ปัจจุบัน: `citizen_id (PK)`, `first_name`, `last_name`, `status (active/revoked)`, `registered_at`

ขอเพิ่ม:
| field | ชนิด | ใช้ทำอะไร |
|---|---|---|
| `member_type` | `daily` (default) / `permanent` | แยกสมาชิกรายวัน vs ถาวร — ของเดิมเป็น `daily` ทั้งหมด |
| `status` (เพิ่มค่า) | เพิ่ม `pending` → `pending`/`active`/`revoked` | สมาชิกถาวรเริ่มที่ `pending` รออนุมัติ (รายวันยังเป็น `active` ทันทีเหมือนเดิม) |
| `permanent_code` | char(10) unique, null | รหัสถาวรคงที่ ออกตอน approve (สมาชิกถาวรเท่านั้น) |
| `photo` | ImageField / path | รูปถ่ายสำหรับทำบัตร (ดูข้อ 4 เรื่องที่เก็บ) |
| `approved_at`, `approved_by` | datetime, char | audit การอนุมัติ (optional แต่แนะนำ) |

> **กันรหัสชน:** `permanent_code` ต้องไม่ซ้ำกับรหัสใน pool `ExternalAccessCode` — ตอน generate ให้เช็ค unique ข้ามทั้งสองตาราง

### 2.2 endpoint ใหม่ให้ reserv `/manage/` เรียก (v2, JWT, token ของ reserv)
| endpoint | method | ใช้ทำอะไร |
|---|---|---|
| `/v2/external/permanent/register/` | POST (multipart) | ลงทะเบียนสมาชิกถาวร: citizen_id + first/last_name + photo → สร้าง `member_type=permanent, status=pending` |
| `/v2/external/permanent/` | GET | list สมาชิกถาวร (filter ตาม status) สำหรับตารางใน `/manage/` |
| `/v2/external/permanent/<citizen_id>/` | GET | รายละเอียดรายคน (รวม photo URL + permanent_code) |
| `/v2/external/permanent/<citizen_id>/approve/` | POST | admin อนุมัติ → generate `permanent_code` + `status=active` |
| `/v2/external/permanent/<citizen_id>/revoke/` | POST | ระงับ → `status=revoked` (รหัสใช้ไม่ได้ทันที) |

### 2.3 แก้ `check_external` ให้รองรับรหัสถาวร
`GET /v2/external/check/<code>/` ปัจจุบันเช็คเฉพาะ pool รายวัน (`assigned_date == วันนี้`)

ขอเพิ่ม logic: ถ้าไม่เจอใน pool รายวัน → เช็คต่อว่าเป็น `ExternalMember.permanent_code == code`
และ `member_type=permanent` และ `status=active` หรือไม่ → ถ้าใช่ **allow (ไม่จำกัดวัน)**

> ข้อดี: ฝั่งประตูไม่ต้องแก้อะไร — ยังสแกน QR ได้รหัส 10 หลัก ยิง endpoint เดิมตัวเดียว

---

## 3. ส่วนที่ reserv จะทำ (หลัง api เสร็จ)
- หน้า `/manage/external/` — ฟอร์มลงทะเบียนสมาชิกถาวร (อัปโหลดรูป) + ตาราง pending/active + ปุ่ม approve/revoke
- เรนเดอร์ "บัตร" — รูปถ่าย + ชื่อ + QR จาก `permanent_code`
- ทั้งหมดเรียกผ่าน token v2 ของ reserv (มี token layer พร้อมแล้ว)

---

## 4. เรื่องที่ต้องตัดสินใจร่วมกัน
- [ ] **รูปถ่ายเก็บที่ไหน:** (ก) api เก็บ (ImageField + media URL) reserv อัปโหลดผ่าน multipart — *แนะนำ เพราะ api เป็น source of truth ของ ExternalMember อยู่แล้ว* หรือ (ข) reserv เก็บเอง api เก็บแค่ตัวตน
- [ ] **รูปแบบบัตร:** บัตรพิมพ์จริง (staff พิมพ์ออก) หรือบัตรเสมือนบนจอ — กระทบว่า QR/รหัสต้องฝังในบัตรอย่างไร
- [ ] **ฟอร์แมต permanent_code:** 10 หลักเหมือน pool (ให้ door reader ทำงานแบบเดียวกัน) ใช่ไหม
- [ ] **ขอบเขตข้อมูล:** เก็บเพิ่มไหม เช่น หน่วยงานต้นสังกัด/เหตุผลที่เข้า/วันหมดอายุบัตร (ถ้าต้องการให้บัตรมีวันหมดอายุ ไม่ใช่ถาวรล้วน)

---

## 5. ทดสอบ (หลังทั้งสองฝั่งเสร็จ)
1. reserv ลงทะเบียนถาวร → api สร้าง `pending` (ยัง check ไม่ผ่าน)
2. admin approve ที่ reserv → api ออก `permanent_code` + `active`
3. check ด้วย permanent_code → `allow:true` **ทุกวัน** (ทดสอบข้ามวันด้วย)
4. revoke → check ต้อง `allow:false` ทันที
5. ดู `/monitor/api-usage/` ว่าทุก call ขึ้น log พร้อมระบบ=reserv
