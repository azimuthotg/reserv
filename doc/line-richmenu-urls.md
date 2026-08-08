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
| ~~ChatGPT Room~~ 🚫 | ~~`?room=chat-gpt`~~ **ยกเลิก — ห้ามใช้แล้ว** | — | — |
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

### ⚠️ สิ่งที่ต้องแก้ใน Rich Menu รอบนี้ (8 ส.ค. 2569)

สำนักฯ ยกเลิกบริการ ChatGPT แล้วนำเครื่องไปทำ Canva Pro เครื่องที่ 2
ฝั่งระบบจอง**ปิดห้อง `chat-gpt` เรียบร้อยแล้ว** ปุ่มเดิมใน Rich Menu จึงใช้ไม่ได้

| ปุ่มเดิม | ต้องแก้เป็น |
|---|---|
| ปุ่ม "ChatGPT Room" → `?room=chat-gpt` | เปลี่ยน link เป็น `?room=canva2` และเปลี่ยนรูปปุ่มเป็น **"Canva Pro 2"** |
| ปุ่ม "Canva Pro" → `?room=canva` | link เดิมใช้ได้ ไม่ต้องแก้ — แก้เฉพาะ**รูปปุ่ม**เป็น "Canva Pro 1" |

**ถ้าไม่แก้จะเกิดอะไร:** กดปุ่ม ChatGPT แล้วเปิดหน้าฟอร์มจองที่ไม่มีข้อมูลห้อง
(ชื่อห้องว่าง เลือกเวลาไม่ได้ กดยืนยันจะขึ้น "ไม่พบข้อมูลห้อง") ไม่ทำให้ระบบพัง แต่ผู้ใช้จะงง

**QR code / ป้ายที่ต้องตรวจด้วย:** ป้ายหรือ QR ที่ชี้ไป `https://lib.npu.ac.th/reserv/room/chat-gpt/`
จะกลายเป็นหน้า 404 — ถ้ามีติดหน้าห้องอยู่ ให้เปลี่ยนเป็น `.../room/canva2/`

---

*จัดทำโดยสำนักวิทยบริการ มหาวิทยาลัยนครพนม*
