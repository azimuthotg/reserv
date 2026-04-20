# URL สำหรับตั้งค่า LINE OA Rich Menu
## ระบบจองพื้นที่บริการ Smart Creative Learning Space
### สำนักวิทยบริการ มหาวิทยาลัยนครพนม

**อัปเดตล่าสุด:** เมษายน 2569

---

## URL ทั้งหมดที่ต้องใช้

| ปุ่ม | URL | ต้อง Login LINE? | ต้องผูกบัญชี LDAP? |
|------|-----|:---:|:---:|
| หน้าแรก (จองพื้นที่) | `https://lib.npu.ac.th/reserv/` | ✅ ต้อง | ✅ ต้อง |
| Mini Theater | `https://lib.npu.ac.th/reserv/booking/?room=mini` | ✅ ต้อง | ✅ ต้อง |
| Edutainment Zone | `https://lib.npu.ac.th/reserv/booking/?room=edutainment` | ✅ ต้อง | ✅ ต้อง |
| Canva Pro | `https://lib.npu.ac.th/reserv/booking/?room=canva` | ✅ ต้อง | ✅ ต้อง |
| ChatGPT Room | `https://lib.npu.ac.th/reserv/booking/?room=chat-gpt` | ✅ ต้อง | ✅ ต้อง |
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

---

*จัดทำโดยสำนักวิทยบริการ มหาวิทยาลัยนครพนม*
