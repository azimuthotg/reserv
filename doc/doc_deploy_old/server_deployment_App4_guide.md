# คู่มือ Deploy ระบบที่ 4 บน lib.npu.ac.th
## Windows Server 2019 + IIS + ARR + NSSM + Waitress

**เวอร์ชัน:** 1.0
**วันที่:** กุมภาพันธ์ 2569
**ผู้จัดทำ:** งานเทคนิคสารสนเทศและการจัดการทรัพยากร
**อ้างอิงจาก:** `doc/server_deployment_guide.md`

---

## ข้อมูลระบบที่ 4

> แทนที่ค่าในวงเล็บเหลี่ยมด้วยข้อมูลจริงก่อนเริ่ม deploy

| รายการ | ค่า |
|--------|-----|
| **ชื่อระบบ** | [ชื่อระบบ] |
| **Django Package** | [package] |
| **WSGI Module** | [package].wsgi.application |
| **Settings Module** | [package].settings |
| **Database** | [ประเภท database — SQLite3 / MySQL] |
| **Path บน Server** | `/[app4_path]/` |
| **Port** | `8003` |
| **NSSM Service Name** | `[App4Service]` |
| **Folder บน Server** | `C:\project\[app4_folder]` |

### สถานะ Server ปัจจุบัน

| App | ระบบ | Path | Port | Service |
|-----|------|------|------|---------|
| 1 | Project Tracker | `/projects/` | 8000 | `ProjectTracker` |
| 2 | AIMS | `/aims/` | 8001 | `AIMS` |
| 3 | LibLogin | `/liblogin/` | 8002 | `LibLogin` |
| **4** | **[ระบบนี้]** | **`/[app4_path]/`** | **8003** | **`[App4Service]`** |

---

## ข้อควรระวัง

> อ่านให้ครบก่อนเริ่ม deploy — รวบรวมจากประสบการณ์ติดตั้งระบบก่อนหน้า

---

### ⚠️ 1. LOGIN_URL ต้องใช้ชื่อ URL ห้ามใช้ path ตรง

**ปัญหา:** ถ้าตั้ง `LOGIN_URL = '/login/'` เมื่อ `FORCE_SCRIPT_NAME` มีค่า Django จะ redirect ไป `/login/` โดยไม่มี prefix → IIS หา rule ไม่เจอ → **404**

**วิธีถูก:** ใช้ชื่อ URL เสมอ เพื่อให้ Django ใช้ `reverse()` ซึ่งเติม `FORCE_SCRIPT_NAME` ให้อัตโนมัติ

```python
# settings.py — ถูกต้อง
LOGIN_URL          = 'login'
LOGIN_REDIRECT_URL = 'dashboard'   # หรือ URL name ของหน้าหลักในระบบนั้น
LOGOUT_REDIRECT_URL = 'login'
```

---

### ⚠️ 2. สร้างโฟลเดอร์ media/ ก่อนสร้าง IIS Virtual Directory

**ปัญหา:** `New-WebVirtualDirectory` จะ error ถ้า PhysicalPath ยังไม่มีอยู่จริง

```
New-WebVirtualDirectory : Parameter 'PhysicalPath' should point to existing path.
```

**วิธีถูก:** สร้างโฟลเดอร์ก่อนเสมอ (ขั้นตอนที่ 11)

```powershell
New-Item -ItemType Directory -Path "C:\project\[app4_folder]\media" -Force
```

---

### ⚠️ 3. ทดสอบ Waitress โดยตรง — ห้ามใส่ prefix path

**ปัญหา:** Waitress รับ request หลังจาก IIS ตัด prefix ออกแล้ว ถ้าทดสอบตรงโดยใส่ `/[app4_path]/login/` จะได้ 404

```
# ผิด — ทดสอบตรงกับ Waitress
http://localhost:8003/[app4_path]/login/   ← 404

# ถูก — Waitress รับ path หลัง IIS ตัด prefix แล้ว
http://localhost:8003/login/               ← 200
```

---

### ⚠️ 4. deploy/waitress_serve.py ต้อง commit ไว้ใน repo

**วิธีถูก:** สร้างไฟล์ในเครื่อง dev แล้ว commit+push ก่อน deploy เสมอ
บน server ใช้แค่ `git pull` ไม่ต้องสร้างมือ

---

### ⚠️ 5. python-dotenv ต้องอยู่ใน requirements.txt

**ปัญหา:** ถ้าไม่มี `python-dotenv` ใน requirements.txt บน server จะ `ModuleNotFoundError` ทันทีที่ start service

```
# requirements.txt ต้องมี
python-dotenv
```

---

### ⚠️ 6. settings.py ต้องแก้ให้ครบก่อน commit

ต้องมีทุกรายการนี้ก่อน deploy:

```python
import os
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', ...)
DEBUG      = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost').split(',')]

FORCE_SCRIPT_NAME       = os.getenv('FORCE_SCRIPT_NAME', '')
USE_X_FORWARDED_HOST    = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE   = not DEBUG
CSRF_COOKIE_SECURE      = not DEBUG
CSRF_TRUSTED_ORIGINS    = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

STATIC_URL = os.getenv('STATIC_URL', 'static/')
MEDIA_URL  = os.getenv('MEDIA_URL', '/media/')

LOGIN_URL           = 'login'       # ← ชื่อ URL ห้ามใช้ path ตรง
LOGIN_REDIRECT_URL  = 'dashboard'   # ← ชื่อ URL ห้ามใช้ path ตรง
LOGOUT_REDIRECT_URL = 'login'       # ← ชื่อ URL ห้ามใช้ path ตรง
```

---

### ⚠️ 7. ตั้ง DJANGO_SETTINGS_MODULE ทุกครั้งที่เปิด PowerShell ใหม่

**ปัญหา:** server มีหลายระบบ env var อาจค้างจากระบบอื่น เช่น `backend.settings` ของ LibLogin

```powershell
# ตั้งก่อนรัน manage.py ทุกครั้ง
$env:DJANGO_SETTINGS_MODULE = "[package].settings"
```

---

### ⚠️ 8. Backup web.config ก่อนแก้ไขเสมอ

**เหตุผล:** `web.config` ใช้ร่วมกันทุก App ถ้า syntax ผิดจะกระทบทุกระบบบน server พร้อมกัน

```powershell
Copy-Item "C:\iis_root\web.config" `
    "C:\iis_root\web.config.bak$(Get-Date -Format 'yyyyMMdd_HHmm')" -Force
```

---

## สารบัญ

1. [ก่อน Deploy — แก้ไข settings.py](#1-กอน-deploy--แกไข-settingspy)
2. [ตรวจสอบ Port ว่าง](#2-ตรวจสอบ-port-วาง)
3. [Clone โค้ดขึ้น Server](#3-clone-โคดขึน-server)
4. [สร้าง Virtual Environment และติดตั้ง Package](#4-สราง-virtual-environment-และติดตัง-package)
5. [สร้างไฟล์ .env](#5-สรางไฟล-env)
6. [Generate SECRET_KEY](#6-generate-secret_key)
7. [Migrate Database และ Collect Static](#7-migrate-database-และ-collect-static)
8. [ตรวจสอบ deploy/waitress_serve.py](#8-ตรวจสอบ-deploywaitress_servepy)
9. [ติดตั้ง NSSM Service](#9-ติดตัง-nssm-service)
10. [ทดสอบ Waitress โดยตรง](#10-ทดสอบ-waitress-โดยตรง)
11. [IIS Virtual Directories (Static + Media)](#11-iis-virtual-directories-static--media)
12. [แก้ไข web.config](#12-แกไข-webconfig)
13. [ทดสอบผ่าน HTTPS](#13-ทดสอบผาน-https)
14. [การบำรุงรักษา](#14-การบารุงรักษา)
15. [ข้อผิดพลาดที่พบบ่อย](#15-ขอผิดพลาดที่พบบอย)

---

## 1. ก่อน Deploy — แก้ไข settings.py

ตรวจสอบ `[package]/settings.py` ให้มีครบตามนี้ก่อน commit (ดูรายละเอียดใน **ข้อควรระวังข้อ 6**)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-...')
DEBUG      = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost').split(',')]

FORCE_SCRIPT_NAME       = os.getenv('FORCE_SCRIPT_NAME', '')
USE_X_FORWARDED_HOST    = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE   = not DEBUG
CSRF_COOKIE_SECURE      = not DEBUG
CSRF_TRUSTED_ORIGINS    = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

STATIC_URL = os.getenv('STATIC_URL', 'static/')
MEDIA_URL  = os.getenv('MEDIA_URL', '/media/')

LOGIN_URL           = 'login'
LOGIN_REDIRECT_URL  = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

เพิ่ม `python-dotenv` ใน `requirements.txt` (ข้อควรระวังข้อ 5)

สร้าง `deploy/waitress_serve.py` แล้ว commit+push ขึ้น repo ก่อน (ข้อควรระวังข้อ 4)

---

## 2. ตรวจสอบ Port ว่าง

```powershell
netstat -ano | findstr ":8003"
# ถ้าไม่มี output = port ว่าง พร้อมใช้
```

---

## 3. Clone โค้ดขึ้น Server

```powershell
cd C:\project
git clone https://github.com/[org]/[repo].git [app4_folder]
cd C:\project\[app4_folder]
```

---

## 4. สร้าง Virtual Environment และติดตั้ง Package

```powershell
cd C:\project\[app4_folder]
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

ตรวจสอบ packages สำคัญ:

```powershell
.\venv\Scripts\pip.exe list | findstr -i "django waitress dotenv"
```

---

## 5. สร้างไฟล์ .env

```powershell
notepad C:\project\[app4_folder]\.env
```

```env
# ---- Django Core ----
SECRET_KEY=REPLACE_WITH_GENERATED_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,110.78.83.102,lib.npu.ac.th

# ---- Path-based Routing ----
FORCE_SCRIPT_NAME=/[app4_path]
STATIC_URL=/[app4_path]/static/
MEDIA_URL=/[app4_path]/media/

# ---- CSRF ----
CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th

# ---- Waitress ----
WAITRESS_HOST=127.0.0.1
WAITRESS_PORT=8003
WAITRESS_THREADS=8

# ---- Database ----
# SQLite3: ไม่ต้องตั้งค่าเพิ่ม
# MySQL: เพิ่ม DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
```

---

## 6. Generate SECRET_KEY

```powershell
$env:DJANGO_SETTINGS_MODULE = "[package].settings"
.\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

คัดลอกค่าที่ได้ไปใส่ใน `.env` บรรทัด `SECRET_KEY=`

---

## 7. Migrate Database และ Collect Static

```powershell
# ตั้งก่อนทุกครั้ง (ข้อควรระวังข้อ 7)
$env:DJANGO_SETTINGS_MODULE = "[package].settings"

.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py collectstatic --noinput

# ถ้าเป็น db ใหม่ (ไม่มี db เดิม)
.\venv\Scripts\python.exe manage.py createsuperuser
```

> ถ้ามี db เดิม: copy ไฟล์มาก่อน แล้วรัน `migrate` เพื่อ apply migration ใหม่ ข้อมูลเดิมไม่หาย

---

## 8. ตรวจสอบ deploy/waitress_serve.py

ไฟล์นี้ควร **มีอยู่ใน repo แล้ว** (ไม่ต้องสร้างมือ — ดูข้อควรระวังข้อ 4)

```powershell
Test-Path "C:\project\[app4_folder]\deploy\waitress_serve.py"
# ต้องได้: True
```

ถ้าไม่มี ให้สร้างในเครื่อง dev แล้ว commit+push ก่อน (**ห้ามมี emoji** ใน print):

```python
import os, sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '[package].settings')

host    = os.getenv('WAITRESS_HOST', '127.0.0.1')
port    = int(os.getenv('WAITRESS_PORT', '8003'))
threads = int(os.getenv('WAITRESS_THREADS', '8'))

print(f"[START] [AppName] {host}:{port} ({threads} threads)")

from waitress import serve
from [package].wsgi import application

serve(application, host=host, port=port, threads=threads, url_scheme='https')
```

ทดสอบรันก่อนติดตั้ง NSSM:

```powershell
.\venv\Scripts\python.exe deploy\waitress_serve.py
# ต้องเห็น: [START] [AppName] 127.0.0.1:8003 (8 threads)
# กด Ctrl+C เพื่อหยุด
```

---

## 9. ติดตั้ง NSSM Service

```powershell
C:\nssm\nssm.exe install [App4Service] `
    "C:\project\[app4_folder]\venv\Scripts\python.exe" `
    "C:\project\[app4_folder]\deploy\waitress_serve.py"

C:\nssm\nssm.exe set [App4Service] AppDirectory "C:\project\[app4_folder]"
C:\nssm\nssm.exe set [App4Service] Start SERVICE_AUTO_START

New-Item -ItemType Directory -Path "C:\project\[app4_folder]\logs" -Force
C:\nssm\nssm.exe set [App4Service] AppStdout "C:\project\[app4_folder]\logs\waitress.log"
C:\nssm\nssm.exe set [App4Service] AppStderr "C:\project\[app4_folder]\logs\waitress_error.log"
C:\nssm\nssm.exe set [App4Service] AppRotateFiles 1
C:\nssm\nssm.exe set [App4Service] AppRotateBytes 10485760

C:\nssm\nssm.exe start [App4Service]
C:\nssm\nssm.exe status [App4Service]
# ต้องได้: SERVICE_RUNNING
```

---

## 10. ทดสอบ Waitress โดยตรง

> **ห้ามใส่ prefix `/[app4_path]/`** — ดูข้อควรระวังข้อ 3

```powershell
# ถูกต้อง
Invoke-WebRequest -Uri "http://localhost:8003/login/" -UseBasicParsing
# ต้องได้ StatusCode: 200
```

---

## 11. IIS Virtual Directories (Static + Media)

> **สร้างโฟลเดอร์ก่อนเสมอ** — ดูข้อควรระวังข้อ 2

```powershell
# สร้างโฟลเดอร์ media ก่อน
New-Item -ItemType Directory -Path "C:\project\[app4_folder]\media" -Force

Import-Module WebAdministration

# Static files
New-WebVirtualDirectory -Site "Default Web Site" -Application "/" `
    -Name "[app4_path]/static" `
    -PhysicalPath "C:\project\[app4_folder]\staticfiles"

# Media files
New-WebVirtualDirectory -Site "Default Web Site" -Application "/" `
    -Name "[app4_path]/media" `
    -PhysicalPath "C:\project\[app4_folder]\media"
```

ตรวจสอบ:

```powershell
Get-WebVirtualDirectory -Site "Default Web Site" | Select-Object Name, PhysicalPath
```

---

## 12. แก้ไข web.config

**Backup ก่อนเสมอ (ข้อควรระวังข้อ 8):**

```powershell
Copy-Item "C:\iis_root\web.config" `
    "C:\iis_root\web.config.bak$(Get-Date -Format 'yyyyMMdd_HHmm')" -Force
```

เพิ่ม rules ใน `<rules>` block ต่อจาก LibLogin (App 3):

```xml
<!-- App 4: [AppName] /[app4_path] → :8003 -->
<rule name="[AppName] Static" stopProcessing="true">
    <match url="^[app4_path]/static/(.*)" />
    <action type="None" />
</rule>
<rule name="[AppName] Media" stopProcessing="true">
    <match url="^[app4_path]/media/(.*)" />
    <action type="None" />
</rule>
<rule name="[AppName] Root Redirect" stopProcessing="true">
    <match url="^[app4_path]$" />
    <action type="Redirect" url="/[app4_path]/" redirectType="Permanent" />
</rule>
<rule name="[AppName] App" stopProcessing="true">
    <match url="^[app4_path]/(.*)" />
    <serverVariables>
        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
    </serverVariables>
    <action type="Rewrite" url="http://127.0.0.1:8003/{R:1}" />
</rule>
```

Restart IIS:

```powershell
iisreset /restart
```

---

## 13. ทดสอบผ่าน HTTPS

```powershell
# ทดสอบระบบใหม่
$r = Invoke-WebRequest "https://lib.npu.ac.th/[app4_path]/login/" -UseBasicParsing
Write-Host "Status: $($r.StatusCode)"    # ต้องได้ 200

# ทดสอบ root URL (ต้องได้ 200 ไม่ใช่ 404)
Invoke-WebRequest "https://lib.npu.ac.th/[app4_path]/" -UseBasicParsing

# ทดสอบทุก App พร้อมกัน
"projects","aims","liblogin","[app4_path]" | ForEach-Object {
    $r = try { Invoke-WebRequest "https://lib.npu.ac.th/$_/" -UseBasicParsing } catch { $_.Exception.Response }
    Write-Host "$_ : $($r.StatusCode)"
}
```

---

## 14. การบำรุงรักษา

### คำสั่ง NSSM ที่ใช้บ่อย

```powershell
C:\nssm\nssm.exe status [App4Service]
C:\nssm\nssm.exe restart [App4Service]
C:\nssm\nssm.exe stop [App4Service]
C:\nssm\nssm.exe start [App4Service]

Get-Content "C:\project\[app4_folder]\logs\waitress_error.log" -Tail 50 -Wait
```

### อัปเดตโค้ด

```powershell
cd C:\project\[app4_folder]
git pull origin main

$env:DJANGO_SETTINGS_MODULE = "[package].settings"
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py collectstatic --noinput

C:\nssm\nssm.exe restart [App4Service]
C:\nssm\nssm.exe status [App4Service]
```

### Backup Database

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmm'
New-Item -ItemType Directory -Path "C:\project\[app4_folder]\backups" -Force
Copy-Item "C:\project\[app4_folder]\db.sqlite3" `
    "C:\project\[app4_folder]\backups\db_$ts.sqlite3"
xcopy "C:\project\[app4_folder]\media" `
    "C:\project\[app4_folder]\backups\media_$ts\" /E /I /Y
```

---

## 15. ข้อผิดพลาดที่พบบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| `SERVICE_PAUSED` | Process crash → NSSM pause | ดู error log: `Get-Content logs\waitress_error.log -Tail 30` |
| `ModuleNotFoundError: No module named '[package]'` | `DJANGO_SETTINGS_MODULE` ค้างจากระบบอื่น | ตั้ง `$env:DJANGO_SETTINGS_MODULE = "[package].settings"` |
| `ModuleNotFoundError: No module named 'dotenv'` | ลืมเพิ่ม `python-dotenv` ใน requirements.txt | `.\venv\Scripts\pip.exe install python-dotenv` แล้วแก้ requirements.txt |
| `UnicodeEncodeError: 'charmap' codec` | มี emoji ใน print() ของ waitress_serve.py | ลบ emoji + ตรวจสอบ `sys.stdout.reconfigure` อยู่บนสุด |
| `400 Bad Request` | IP/hostname ไม่อยู่ใน `ALLOWED_HOSTS` | เพิ่มใน `.env` บรรทัด `ALLOWED_HOSTS` |
| `404` ที่ root `/[app4_path]/` | `LOGIN_URL` ใช้ path ตรง ไม่ได้ใช้ชื่อ URL | แก้ `LOGIN_URL = 'login'` ใน settings.py (ข้อควรระวังข้อ 1) |
| Static files ไม่โหลด | ยังไม่ได้ทำ IIS Virtual Directory | ตรวจ IIS Manager: `[app4_path]/static` ชี้ถูกต้องหรือไม่ |
| `PhysicalPath should point to existing path` | โฟลเดอร์ media ยังไม่มี | `New-Item -ItemType Directory -Path "...\media" -Force` ก่อน |
| `502 Bad Gateway` | Waitress service ไม่รัน | `C:\nssm\nssm.exe start [App4Service]` |
| CSRF Error login ไม่ได้ | `CSRF_TRUSTED_ORIGINS` ไม่ถูกต้อง | ตรวจ `.env`: `CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th` |

---

## ภาคผนวก — โครงสร้างโฟลเดอร์บน Server

```
C:\project\[app4_folder]\
├── .env                     ← Production env vars (อย่า commit!)
├── db.sqlite3               ← SQLite database (ถ้าใช้ SQLite)
├── manage.py
├── requirements.txt         ← ต้องมี python-dotenv
│
├── [package]\               ← Django project package
│   ├── settings.py          ← ต้องแก้ไขก่อน deploy (ดูส่วนที่ 1)
│   ├── urls.py
│   └── wsgi.py
│
├── staticfiles\             ← สร้างโดย collectstatic
├── media\                   ← สร้างมือก่อนทำ IIS Virtual Directory
├── logs\
│   ├── waitress.log
│   └── waitress_error.log
├── backups\
├── venv\
└── deploy\
    └── waitress_serve.py    ← ต้อง commit ไว้ใน repo ก่อน
```

---

## ภาคผนวก — web.config สมบูรณ์ (4 Apps)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>

        <defaultDocument enabled="false" />
        <directoryBrowse enabled="false" />

        <httpProtocol>
            <customHeaders>
                <remove name="X-Powered-By" />
            </customHeaders>
        </httpProtocol>

        <rewrite>
            <rules>

                <!-- Rule 0: Redirect HTTP → HTTPS -->
                <rule name="Force HTTPS" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions>
                        <add input="{HTTPS}" pattern="^OFF$" />
                    </conditions>
                    <action type="Redirect"
                            url="https://{HTTP_HOST}/{R:1}"
                            redirectType="Permanent" />
                </rule>

                <!-- App 1: Project Tracker /projects → :8000 -->
                <rule name="App1 Root Redirect" stopProcessing="true">
                    <match url="^projects$" />
                    <action type="Redirect" url="/projects/" redirectType="Permanent" />
                </rule>
                <rule name="App1 Project Tracker" stopProcessing="true">
                    <match url="^projects/(.*)" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
                    </serverVariables>
                    <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}" />
                </rule>

                <!-- App 2: AIMS /aims → :8001 -->
                <rule name="AIMS Static" stopProcessing="true">
                    <match url="^aims/static/(.*)" />
                    <action type="None" />
                </rule>
                <rule name="AIMS Root Redirect" stopProcessing="true">
                    <match url="^aims$" />
                    <action type="Redirect" url="/aims/" redirectType="Permanent" />
                </rule>
                <rule name="AIMS App" stopProcessing="true">
                    <match url="^aims/(.*)" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
                    </serverVariables>
                    <action type="Rewrite" url="http://127.0.0.1:8001/{R:1}" />
                </rule>

                <!-- App 3: LibLogin /liblogin → :8002 -->
                <rule name="LibLogin Static" stopProcessing="true">
                    <match url="^liblogin/static/(.*)" />
                    <action type="None" />
                </rule>
                <rule name="LibLogin Media" stopProcessing="true">
                    <match url="^liblogin/media/(.*)" />
                    <action type="None" />
                </rule>
                <rule name="LibLogin Root Redirect" stopProcessing="true">
                    <match url="^liblogin$" />
                    <action type="Redirect" url="/liblogin/" redirectType="Permanent" />
                </rule>
                <rule name="LibLogin App" stopProcessing="true">
                    <match url="^liblogin/(.*)" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
                    </serverVariables>
                    <action type="Rewrite" url="http://127.0.0.1:8002/{R:1}" />
                </rule>

                <!-- App 4: [AppName] /[app4_path] → :8003 -->
                <rule name="[AppName] Static" stopProcessing="true">
                    <match url="^[app4_path]/static/(.*)" />
                    <action type="None" />
                </rule>
                <rule name="[AppName] Media" stopProcessing="true">
                    <match url="^[app4_path]/media/(.*)" />
                    <action type="None" />
                </rule>
                <rule name="[AppName] Root Redirect" stopProcessing="true">
                    <match url="^[app4_path]$" />
                    <action type="Redirect" url="/[app4_path]/" redirectType="Permanent" />
                </rule>
                <rule name="[AppName] App" stopProcessing="true">
                    <match url="^[app4_path]/(.*)" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
                    </serverVariables>
                    <action type="Rewrite" url="http://127.0.0.1:8003/{R:1}" />
                </rule>

            </rules>
        </rewrite>

        <security>
            <requestFiltering>
                <requestLimits maxAllowedContentLength="10485760" />
            </requestFiltering>
        </security>

    </system.webServer>
</configuration>
```

---

*เอกสารนี้จัดทำสำหรับการ Deploy ระบบที่ 4 บน lib.npu.ac.th
งานเทคนิคสารสนเทศและการจัดการทรัพยากร สำนักวิทยบริการ มหาวิทยาลัยนครพนม*
