# อินโฟกราฟิกภาพที่ 2 — "ขั้นตอน + ข้อกำหนด"

> ระบบจองพื้นที่บริการออนไลน์ Smart Creative Learning Space
> สำนักวิทยบริการ มหาวิทยาลัยนครพนม
---

## House Style

| รายการ | ค่า |
|---|---|
| สีน้ำเงินหลัก | `#1A3A8F` |
| สีน้ำเงินไล่ (อ่อน) | `#2E6BD6` |
| ทอง/ส้ม accent | `#F5A623` |
| เหลืองสว่าง | `#FFD24C` |
| เขียว LINE | `#06C755` |
| ขาว | `#FFFFFF` |
| ฟอนต์หัวเรื่อง | Kanit / Prompt **Bold** |
| ฟอนต์เนื้อความ | Sarabun / Prompt Regular |

**องค์ประกอบประจำ**
- มุมบนซ้าย: โลโก้ `logo_ARC.png` (ทอง) + "สำนักวิทยบริการ มหาวิทยาลัยนครพนม"
- พื้นหลัง: ใช้รูปอาคารหอสมุด **NPU Library**  เป็นเลเยอร์พื้นหลัง เคลือบ overlay น้ำเงินเข้ม `#1A3A8F` ~60% ไล่เฉดเข้มลงด้านล่างเพื่อให้ตัวอักษรขาวอ่านชัด + เสริม sparkle ขาว + จุดทอง
- การ์ด/badge: ขาวขอบมน เงานุ่ม เลขในวงกลมทอง แถวล่าง (contact bar): `☎ 042-587285   ✉ arcnpu@npu.ac.th   🌐 arcnpu.ac.th   |   เริ่มจอง: lib.npu.ac.th/reserv` ไม่ชิดขอบเกินไป

## รายละเอียดภาพ

**เป้าหมาย:** บอกวิธีจองทีละสเต็ป + กติกาที่ต้องรู้ (เน้นกันคนพลาด เช่น เช็กอิน 15 นาที)
**ขนาด:** แนวตั้ง `1080 × 1350 px` 

### โครงเลย์เอาต์ (2 ส่วน: ขั้นตอน → ข้อกำหนด)

```
┌─────────────────────────────────────────┐
│ [โลโก้ ARC•NPU]  สำนักวิทยบริการ ม.นครพนม   │
│        จองห้องง่าย ๆ ใน 3 ขั้นตอน           │  ← หัวเรื่อง
│                                          │
│  ┌1┐ แอดไลน์ Official Account             │  ← ขั้นตอน (timeline)
│  └─┘ + กด "จองห้อง"                       │
│   │                                      │
│  ┌2┐ ผูกบัญชี (เฉพาะครั้งแรก)              │
│  └─┘ ยืนยันตัวตนผ่าน LINE + รหัส LDAP       │
│   │                                      │
│  ┌3┐ เลือกห้อง · เลือกวันเวลา · จอง         │
│  └─┘ รับ QR/บัตรเข้าใช้ห้อง                 │
│                                          │
│   ── ข้อกำหนดที่ต้องรู้ ──                   │  ← ข้อกำหนด (badge grid)
│  📅 จองล่วงหน้าได้ไม่เกิน 7 วันเปิดบริการ      │
│  ⏰ จองล่วงหน้าอย่างน้อย 15 นาที             │
│  ⏱ จองได้สูงสุด 2 ชม./ครั้ง                 │
│  ✅ Check-in ภายใน ±15 นาที จากเวลาเริ่ม     │
│     ไม่เช็กอิน = ยกเลิกอัตโนมัติ              │
│  🎛️ ถึงเวลา = ได้รีโมทคุมอุปกรณ์ผ่าน LINE     │
│  🔌 หมดเวลา = ระบบตัดไฟอัตโนมัติ             │
│  👤 ต้องผูกบัญชีและบัญชีไม่ถูกระงับ           │
│                                          │
│ ☎ 042-587285  ✉ arcnpu@npu.ac.th  🌐 ... │  ← contact bar
└─────────────────────────────────────────┘
```

### ข้อความเป๊ะ (คัดลอกไปวาง)

**หัวเรื่อง:** `จองห้องง่าย ๆ ใน 3 ขั้นตอน`

**ส่วนขั้นตอน (timeline 3 สเต็ป)**
| # | หัวข้อ | รายละเอียด |
|---|---|---|
| 1 | `แอดไลน์ Official Account` | `กด "จองห้อง" ใน Rich Menu (หรือเปิด lib.npu.ac.th/reserv)` |
| 2 | `ผูกบัญชี (เฉพาะครั้งแรก)` | `ยืนยันตัวตนผ่าน LINE แล้วกรอกรหัส LDAP มหาวิทยาลัย` |
| 3 | `เลือกห้อง · เลือกวันเวลา · กดจอง` | `จองสำเร็จ รับ QR สำหรับเช็กอินเข้าใช้ห้อง` |

**ส่วนข้อกำหนด (badge 7 ข้อ)**
```
📅 จองล่วงหน้าได้ไม่เกิน 7 วันเปิดบริการ (ข้ามวันหยุด/วันปิด)
⏰ ต้องจองล่วงหน้าอย่างน้อย 15 นาที
⏱ จองได้สูงสุด 3.5 ชั่วโมงต่อครั้ง
✅ Check-in ในระบบได้ตั้งแต่ 15 นาทีก่อน เวลาจองและช้าได้ 15 นาทีหลังเวลาจอง
   ⚠️ ไม่เช็กอินภายในเวลา = ระบบยกเลิกการจองอัตโนมัติ
🎛️ เมื่อถึงเวลาจอง ระบบส่ง "รีโมท" ให้ควบคุมอุปกรณ์ในพื้นที่จอง (ไฟ / แอร์ / อุปกรณ์) ผ่าน LINE
🔌 เมื่อหมดเวลาจอง ระบบตัดไฟ / ปิดอุปกรณ์ในห้องให้อัตโนมัติ
👤 ต้องผูกบัญชีก่อน และบัญชีต้องไม่ถูกระงับ
```
**ข้อระวัง**
การวาง layout ให้สม่ำเสมอ สมดุล ไม่หนักด้านใดด้านหนึ่ง ดูระยะ ไม่ควรวาง element ชิดขอบ มากเกินไป

### Prompt เจนพื้นหลัง/เลย์เอาต์ (พิมพ์ไทยทับทีหลัง)

> **วิธีพื้นหลัง (แนะนำ):** วางรูปจริง `doc/illustrations/npu-library-building.jpg` เป็นเลเยอร์ล่างสุดใน Canva → ใส่กล่องสีน้ำเงิน `#1A3A8F` opacity ~60% ทับ (ไล่เฉดเข้มลงล่าง) → วางการ์ด/ข้อความบนนั้น
> ถ้าจะ gen พื้นหลังด้วย AI แทน ใช้ prompt ด้านล่าง

```
Vertical infographic 1080x1350, Thai how-to + rules layout.
Background: a real photo of a cream/beige colonial-style university library building
labeled "NPU Library", with blue sky, palm trees and green lawn, placed faint behind
a dark royal-blue overlay (#1A3A8F ~60%) that fades darker toward the bottom for text
contrast; add subtle white sparkles and gold dots.
Top-left gold emblem logo. Upper half: a vertical 3-step timeline with large gold
numbered circles (1,2,3) connected by a dotted line, each with a rounded white card
and a small icon (chat bubble, ID link, calendar-check).
Lower half: a grid of rounded badge cards with icons (calendar, clock, hourglass,
check-in, remote/light-bulb, power-off, user) for rules/requirements.
Bottom: thin gold contact bar.
Modern, rounded, friendly official Thai university branding.
Colors: royal blue, gold #F5A623, white. Leave clear empty space for Thai text.
```

---

