# URL สำหรับตั้งค่า LINE OA Rich Menu
## ระบบจองพื้นที่บริการ Smart Creative Learning Space
### สำนักวิทยบริการ มหาวิทยาลัยนครพนม

**อัปเดตล่าสุด:** 8 สิงหาคม 2569

---

## URL ทั้งหมดที่ต้องใช้

| ปุ่ม | URL | ต้อง Login LINE? | ต้องผูกบัญชี LDAP? |
|------|-----|:---:|:---:|
| หน้าแรก (จองพื้นที่) | `https://lib.npu.ac.th/reserv/` | ✅ ต้อง | ✅ ต้อง |
| Mini Theater | `https://lib.npu.ac.th/reserv/booking/?room=mini` | ✅ ต้อง | ✅ ต้อง |
| Edutainment Zone | `https://lib.npu.ac.th/reserv/booking/?room=edutainment` | ✅ ต้อง | ✅ ต้อง |
| Canva Pro 1 | `https://lib.npu.ac.th/reserv/booking/?room=canva` | ✅ ต้อง | ✅ ต้อง |
| **Canva Pro 2** 🆕 | `https://lib.npu.ac.th/reserv/booking/?room=canva2` | ✅ ต้อง | ✅ ต้อง |
| **ChatGPT** ♻️ | `https://lib.npu.ac.th/reserv/booking/?room=chat-gpt` | ✅ ต้อง | ✅ ต้อง |
| ~~Netflix Pro~~ 🚫 | ~~`?room=netflix1_vm`~~ **ปิดบริการ 9 ส.ค. 2569 — ห้ามใช้แล้ว** | — | — |
| โต๊ะประชุมชั้น 1 | `https://lib.npu.ac.th/reserv/booking/?room=meeting_f1` | ✅ ต้อง | ✅ ต้อง |
| Virtual Card (โปรไฟล์) | `https://lib.npu.ac.th/reserv/card/` | ✅ ต้อง | ✅ ต้อง |
| ปฏิทินการจอง | `https://lib.npu.ac.th/reserv/calendar/` | ❌ ไม่ต้อง | ❌ ไม่ต้อง |

---

## การทำงานของระบบเมื่อผู้ใช้กดปุ่ม

```
ผู้ใช้กดปุ่มใน Rich Menu
        │
        ▼
LIFF เปิดขึ้น → ตรวจสอบการ Login LINE
        │
        ├── ยังไม่ได้ login → LINE Login อัตโนมัติ (ไม่ต้องทำอะไร)
        │
        └── Login แล้ว → ตรวจสอบการผูกบัญชี
                │
                ├── ยังไม่ผูกบัญชี → หน้าลงทะเบียน (กรอก LDAP + รหัสผ่าน)
                │
                └── ผูกบัญชีแล้ว → เข้าใช้งานได้เลย ✅
```

---

## หมายเหตุสำคัญ

- **ปฏิทิน** (`/calendar/`) เปิดสาธารณะ — ใครก็ดูได้ ไม่ต้อง login เหมาะสำหรับแชร์ให้คนทั่วไปดูตารางการจอง
- **ทุก URL ใช้ HTTPS เท่านั้น** — ห้ามใช้ HTTP เพราะ LIFF ต้องการ HTTPS
- **LIFF Endpoint URL** ที่ตั้งใน LINE Developers Console ต้องเป็น `https://lib.npu.ac.th/reserv/`
- URL ที่เปลี่ยนแปลงจากเดิม: `?room=netflix` → **`?room=edutainment`** (อัปเดตแล้ว)

### ⚠️ สิ่งที่ต้องแก้ใน Rich Menu — ฉบับล่าสุด 9 ส.ค. 2569

> 📌 **อ่านตรงนี้ก่อน** — คำสั่งของวันที่ 8 ส.ค. ที่ให้เปลี่ยนปุ่ม ChatGPT ไปเป็น `?room=canva2`
> **ยกเลิกแล้ว** สำนักฯ เปลี่ยนบริการบนเครื่องเสมือนของ Netflix ไปเป็น ChatGPT
> ฝั่งระบบจองจึง **เปิดห้อง `chat-gpt` กลับ** และ **ปิดห้อง `netflix1_vm`** เมื่อ 9 ส.ค. 2569

| ปุ่ม | สถานะ | ต้องทำอะไร |
|---|---|---|
| "ChatGPT Room" → `?room=chat-gpt` | ✅ **ใช้ได้ตามเดิม** | **ไม่ต้องแก้** (ถ้าเมื่อวานเปลี่ยนเป็น `canva2` ไปแล้ว ให้เปลี่ยนกลับ) |
| "Canva Pro" → `?room=canva` | ✅ link เดิมใช้ได้ | แก้เฉพาะ**รูปปุ่ม**เป็น "Canva Pro 1" |
| **Canva Pro 2** | ❌ ยังไม่มีปุ่ม | **เพิ่มปุ่มใหม่** ชี้ไป `?room=canva2` |
| Netflix Pro | 🚫 ปิดบริการแล้ว | ถ้าเคยเพิ่มปุ่มไว้ **ให้ถอดออก** (ถ้ายังไม่เคยเพิ่ม ก็ไม่ต้องทำอะไร) |

**ถ้าไม่แก้จะเกิดอะไร:** ปุ่มที่ชี้ไปห้องที่ปิดอยู่จะเปิดหน้าฟอร์มจองที่ไม่มีข้อมูลห้อง
(ชื่อห้องว่าง เลือกเวลาไม่ได้ กดยืนยันจะขึ้น "ไม่พบข้อมูลห้อง") ไม่ทำให้ระบบพัง แต่ผู้ใช้จะงง

**QR code / ป้ายที่ต้องตรวจด้วย:** ป้ายหรือ QR ที่ชี้ไป `.../room/netflix1_vm/` จะกลายเป็น 404
ส่วน `.../room/chat-gpt/` กลับมาใช้ได้แล้ว

> ⚠️ **อย่าสับสนกับ `netflix` ตัวเก่า** — เอกสารรุ่นเก่า (`deploy_guide.md`, `admin-manual.md`,
> `development_report.md`) ที่พูดถึง `booking_name = netflix` หมายถึง **ห้อง Edutainment Zone**
> ซึ่งเปลี่ยน key เป็น `edutainment` ไปนานแล้ว **คนละห้องกับ `netflix1_vm`**

---

*จัดทำโดยสำนักวิทยบริการ มหาวิทยาลัยนครพนม*
