# คู่มือ Deploy — ระบบจองพื้นที่บริการ Library@NPU

**Stack:** Django 4.2 + MySQL + Waitress + IIS ARR + WhiteNoise
**Production URL:** https://lib.npu.ac.th/reserv/
**Server:** Windows Server + IIS
**Service Manager:** NSSM

---

## ขั้นตอน Deploy (ครั้งแรก)

### 1. Clone และติดตั้ง

```powershell
cd C:\project
git clone https://github.com/azimuthotg/reserv.git reserv
cd reserv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. ตั้งค่า .env

```powershell
copy deploy\.env.production .env
notepad .env   # แก้ค่าให้ครบ
```

ค่าสำคัญใน `.env`:

```env
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,lib.npu.ac.th
FORCE_SCRIPT_NAME=/reserv
STATIC_URL=/reserv/static/
CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th
WAITRESS_HOST=127.0.0.1
WAITRESS_PORT=8003
WAITRESS_THREADS=8
DB_NAME=reserv_db
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=3306
LINE_LIFF_ID=1653777241-BP070q31
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

### 3. Database และ Static

```powershell
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. เพิ่มข้อมูลห้องผ่าน Admin

เปิด https://lib.npu.ac.th/reserv/admin/ → Rooms → Add Room

| Field | ตัวอย่าง |
|---|---|
| Name | Netflix Zone |
| **Booking name** | `netflix` ← ต้องตรงกับ URL param |
| Location | ชั้น 3 สำนักวิทยบริการ |
| Capacity | 12 |
| Open time | 08:30 |
| Close time | 16:30 |

booking_name ที่ใช้ใน Flex Message: `netflix`, `mini`, `canva`, `chat-gpt`, `meeting_f1`

### 5. NSSM Service

```powershell
c:\nssm\nssm.exe install reserv "C:\project\reserv\venv\Scripts\python.exe" "C:\project\reserv\deploy\waitress_serve.py"
c:\nssm\nssm.exe set reserv AppDirectory "C:\project\reserv"
c:\nssm\nssm.exe start reserv
```

### 6. IIS web.config

เพิ่ม rules ใน `C:\iis_root\web.config` ภายใน `<rules>`:

```xml
<!-- Reserv App — ส่งทุก /reserv/* ไป Waitress :8003 (รวม static ผ่าน WhiteNoise) -->
<rule name="Reserv Root Redirect" stopProcessing="true">
    <match url="^reserv$" />
    <action type="Redirect" url="/reserv/" redirectType="Permanent" />
</rule>
<rule name="Reserv App" stopProcessing="true">
    <match url="^reserv/(.*)" />
    <serverVariables>
        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
    </serverVariables>
    <action type="Rewrite" url="http://127.0.0.1:8003/{R:1}" />
</rule>
```

> ⚠️ **อย่า** เพิ่ม rule แยกสำหรับ `/reserv/static/` — ดูหัวข้อปัญหาด้านล่าง

```powershell
iisreset /restart
```

### 7. LINE Developers Console

- LIFF → Endpoint URL: `https://lib.npu.ac.th/reserv/booking/`

---

## อัปเดต (ครั้งถัดไป)

```powershell
cd C:\project\reserv
venv\Scripts\activate
git pull origin master
pip install -r requirements.txt   # ถ้ามี package ใหม่
python manage.py migrate           # ถ้ามี migration ใหม่
python manage.py collectstatic --noinput
c:\nssm\nssm.exe restart reserv
```

---

## ปัญหาที่พบและวิธีแก้

### ❌ Service ค้างอยู่ใน SERVICE_PAUSED

**อาการ:** `nssm restart` ขึ้น "Unexpected status SERVICE_PAUSED"

**สาเหตุ:** NSSM throttle service เพราะ app crash หลายครั้งติดกัน

**วิธีแก้:**
```powershell
sc.exe queryex reserv          # ดู PID
taskkill /F /PID <PID>         # kill process
c:\nssm\nssm.exe start reserv
```

> ⚠️ PowerShell: ใช้ `sc.exe` ไม่ใช่ `sc` (sc ใน PowerShell = Set-Content)

---

### ❌ ImportError: Couldn't import Django

**อาการ:** รัน `python manage.py` แล้วได้ error นี้

**สาเหตุ:** ยังไม่ได้ activate venv

**วิธีแก้:**
```powershell
venv\Scripts\activate
python manage.py <command>
```

---

### ❌ Static files 404 (Admin ไม่มี CSS)

**อาการ:** เข้า `/reserv/admin/` ได้ แต่ CSS/JS หาย หน้าดูแปลก

**สาเหตุ:** IIS web.config มี rule `Reserv Static` ที่ทำ `action type="None"` ทำให้ request หยุดอยู่ที่ IIS และไม่ถึง Waitress ทำให้ WhiteNoise serve ไม่ได้

**วิธีแก้:** ลบ rule เหล่านี้ออกจาก `C:\iis_root\web.config`:
```xml
<!-- ลบออก -->
<rule name="Reserv Static" stopProcessing="true">
    <match url="^reserv/static/(.*)" />
    <action type="None" />
</rule>
<rule name="Reserv Media" stopProcessing="true">
    <match url="^reserv/media/(.*)" />
    <action type="None" />
</rule>
```

ให้ `Reserv App` rule จัดการทุก path รวมถึง `/reserv/static/*` โดย **WhiteNoise** จะ serve static files ผ่าน Waitress แทน IIS

```powershell
iisreset /restart
```

---

### ❌ LIFF init error: channel not found

**อาการ:** เปิดหน้า booking ใน LINE แล้วขึ้น error นี้

**สาเหตุ:** `LINE_LIFF_ID` ไม่ได้ตั้งใน `.env`

**วิธีแก้:** เพิ่มใน `.env`:
```
LINE_LIFF_ID=1653777241-BP070q31
```
แล้ว restart service

---

### ❌ 400 Bad Request หลัง LIFF login

**อาการ:** LIFF init OK แต่หลัง `liff.login()` redirect กลับมาแล้วได้ 400

**สาเหตุ:** LIFF Endpoint URL ใน LINE Developers Console ไม่ตรงกับ URL จริง

**วิธีแก้:** LINE Developers Console → LIFF → แก้ Endpoint URL เป็น:
```
https://lib.npu.ac.th/reserv/booking/
```

---

### ❌ NSSM ใช้ Python ผิดตัว (system Python แทน venv)

**อาการ:** Service start แต่ crash ทันที, `waitress` หรือ package อื่นหาไม่เจอ

**วิธีตรวจ:**
```powershell
c:\nssm\nssm.exe get reserv Application      # ควรเป็น ...venv\Scripts\python.exe
c:\nssm\nssm.exe get reserv AppParameters    # ควรเป็น deploy\waitress_serve.py
c:\nssm\nssm.exe get reserv AppDirectory     # ควรเป็น C:\project\reserv
```

**วิธีแก้:**
```powershell
c:\nssm\nssm.exe set reserv Application "C:\project\reserv\venv\Scripts\python.exe"
c:\nssm\nssm.exe set reserv AppParameters "C:\project\reserv\deploy\waitress_serve.py"
c:\nssm\nssm.exe set reserv AppDirectory "C:\project\reserv"
c:\nssm\nssm.exe restart reserv
```

---

## Architecture

```
LINE OA (Flex Message)
  → ลิงก์ https://lib.npu.ac.th/reserv/booking/?booking_name=netflix
      ↓
    IIS ARR (lib.npu.ac.th)
      → web.config rewrite ^reserv/(.*) → 127.0.0.1:8003
      ↓
    Waitress :8003
      ├── /reserv/static/* → WhiteNoise (serve staticfiles/)
      └── /reserv/*        → Django
          ↓
        booking/views.py
          ├── booking_page()    — render form
          ├── check_user()      — proxy → api.npu.ac.th + cache LineUser
          ├── create_booking()  — conflict check + save Booking
          └── booking_success() — หน้าสำเร็จ
```

---

## URL สำคัญ

| URL | หน้าที่ |
|---|---|
| `/reserv/booking/?booking_name=<room>` | LIFF booking form |
| `/reserv/booking/success/?id=<id>` | หน้าจองสำเร็จ |
| `/reserv/api/check-user/` | ตรวจ LINE userId กับ NPU API |
| `/reserv/api/booking/` | สร้างการจอง |
| `/reserv/admin/` | Django Admin |
