# คู่มือ Deploy ระบบ LibLogin บน lib.npu.ac.th
## Windows Server 2019 + IIS + ARR + NSSM + Waitress

**เวอร์ชัน:** 1.0
**วันที่:** กุมภาพันธ์ 2569
**ผู้จัดทำ:** งานเทคนิคสารสนเทศและการจัดการทรัพยากร
**อ้างอิงจาก:** `doc/server_deployment_guide.md`

---

## ข้อมูลระบบ LibLogin

| รายการ | ค่า |
|--------|-----|
| **ชื่อระบบ** | LibLogin - Library WiFi Login Management System |
| **Django Package** | `backend` |
| **WSGI Module** | `backend.wsgi.application` |
| **Settings Module** | `backend.settings` |
| **Database** | SQLite3 (`db.sqlite3`) — ไม่ต้องติดตั้ง DB Server |
| **Path บน Server** | `/liblogin/` |
| **Port** | `8002` |
| **NSSM Service Name** | `LibLogin` |
| **Folder บน Server** | `C:\project\liblogin` |

---

## สารบัญ

1. [ก่อน Deploy — แก้ไข settings.py](#1-กอน-deploy--แกไข-settingspy)
2. [ตรวจสอบ Port ว่าง](#2-ตรวจสอบ-port-วาง)
3. [Clone โค้ดขึ้น Server](#3-clone-โคดขึน-server)
4. [สร้าง Virtual Environment และติดตั้ง Package](#4-สราง-virtual-environment-และติดตัง-package)
5. [สร้างไฟล์ .env](#5-สรางไฟล-env)
6. [Generate SECRET_KEY](#6-generate-secret_key)
7. [Migrate Database และ Collect Static](#7-migrate-database-และ-collect-static)
8. [สร้าง deploy/waitress_serve.py](#8-สราง-deploywaitress_servepy)
9. [ติดตั้ง NSSM Service](#9-ติดตัง-nssm-service)
10. [ทดสอบ Waitress โดยตรง](#10-ทดสอบ-waitress-โดยตรง)
11. [IIS Virtual Directories (Static + Media)](#11-iis-virtual-directories-static--media)
12. [แก้ไข web.config](#12-แกไข-webconfig)
13. [ทดสอบผ่าน HTTPS](#13-ทดสอบผาน-https)
14. [การบำรุงรักษา](#14-การบารุงรักษา)
15. [ข้อผิดพลาดที่พบบ่อย](#15-ขอผิดพลาดที่พบบอย)

---

## 1. ก่อน Deploy — แก้ไข settings.py

`settings.py` ปัจจุบันใช้ค่า hardcode (development only) ต้องแก้ก่อน commit ขึ้น server

แก้ไขไฟล์ `backend/settings.py` โดยเพิ่มและแก้บรรทัดเหล่านี้:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / '.env')

# ---- Security ----
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-changeme')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost').split(',')]

# ---- Proxy / Path-based Routing (IIS ARR) ----
FORCE_SCRIPT_NAME    = os.getenv('FORCE_SCRIPT_NAME', '')        # เช่น /liblogin
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE   = not DEBUG
CSRF_COOKIE_SECURE      = not DEBUG
CSRF_TRUSTED_ORIGINS    = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# ---- Static & Media ----
STATIC_URL  = os.getenv('STATIC_URL', '/static/')          # เช่น /liblogin/static/
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = os.getenv('MEDIA_URL', '/media/')             # เช่น /liblogin/media/
MEDIA_ROOT  = BASE_DIR / 'media'
```

> **หมายเหตุ:** ติดตั้ง python-dotenv ด้วย: `pip install python-dotenv`
> หรือเพิ่มใน `requirements.txt`:
> ```
> python-dotenv
> ```

---

## 2. ตรวจสอบ Port ว่าง

```powershell
netstat -ano | findstr ":8002"
# ถ้าไม่มี output = port ว่าง พร้อมใช้
```

---

## 3. Clone โค้ดขึ้น Server

```powershell
cd C:\project
git clone https://github.com/[org]/LibLogin.git liblogin
cd C:\project\liblogin
```

> แทน `[org]` ด้วย GitHub organization/username จริง

---

## 4. สร้าง Virtual Environment และติดตั้ง Package

```powershell
cd C:\project\liblogin

# สร้าง venv
python -m venv venv

# ติดตั้ง dependencies
.\venv\Scripts\pip.exe install -r requirements.txt
.\venv\Scripts\pip.exe install waitress python-dotenv
```

ตรวจสอบ packages สำคัญ:

```powershell
.\venv\Scripts\pip.exe list | findstr -i "django waitress pillow dotenv reportlab"
```

---

## 5. สร้างไฟล์ .env

```powershell
notepad C:\project\liblogin\.env
```

วางเนื้อหาด้านล่าง (แก้ค่าก่อนบันทึก):

```env
# ---- Django Core ----
SECRET_KEY=REPLACE_WITH_GENERATED_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,110.78.83.102,lib.npu.ac.th

# ---- Path-based Routing ----
FORCE_SCRIPT_NAME=/liblogin
STATIC_URL=/liblogin/static/
MEDIA_URL=/liblogin/media/

# ---- CSRF ----
CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th

# ---- Waitress ----
WAITRESS_HOST=127.0.0.1
WAITRESS_PORT=8002
WAITRESS_THREADS=8

# ---- Database ----
# ใช้ SQLite3 (default) ไม่ต้องตั้งค่าเพิ่ม
# db.sqlite3 จะอยู่ที่ C:\project\liblogin\db.sqlite3
```

> **ความปลอดภัย:** ไฟล์ `.env` ต้องไม่ถูก commit ขึ้น git
> ตรวจสอบ `.gitignore` มีบรรทัด `.env` อยู่แล้วหรือไม่

---

## 6. Generate SECRET_KEY

```powershell
cd C:\project\liblogin
.\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

คัดลอกค่าที่ได้ไปใส่ใน `.env` บรรทัด `SECRET_KEY=...`

---

## 7. Migrate Database และ Collect Static

```powershell
cd C:\project\liblogin

# ต้องตั้ง DJANGO_SETTINGS_MODULE ก่อนเสมอ (ป้องกัน env ค้างจากระบบอื่น)
$env:DJANGO_SETTINGS_MODULE = "backend.settings"

# Migrate (สร้าง db.sqlite3 + tables)
.\venv\Scripts\python.exe manage.py migrate

# Collect static files ไปยัง staticfiles/
.\venv\Scripts\python.exe manage.py collectstatic --noinput

# สร้าง superuser (ครั้งแรกเท่านั้น)
.\venv\Scripts\python.exe manage.py createsuperuser
```

ตรวจสอบว่าสร้างสำเร็จ:

```powershell
# ต้องมีไฟล์เหล่านี้
Test-Path "C:\project\liblogin\db.sqlite3"          # True
Test-Path "C:\project\liblogin\staticfiles"          # True
Get-ChildItem "C:\project\liblogin\staticfiles" -Recurse | Measure-Object | Select-Object Count
```

---

## 8. สร้าง deploy/waitress_serve.py

```powershell
New-Item -ItemType Directory -Path "C:\project\liblogin\deploy" -Force
notepad C:\project\liblogin\deploy\waitress_serve.py
```

วางเนื้อหานี้ (**ห้ามมี emoji** ใน print เพราะ NSSM log ใช้ encoding cp1252):

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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

host    = os.getenv('WAITRESS_HOST', '127.0.0.1')
port    = int(os.getenv('WAITRESS_PORT', '8002'))
threads = int(os.getenv('WAITRESS_THREADS', '8'))

print(f"[START] LibLogin {host}:{port} ({threads} threads)")

from waitress import serve
from backend.wsgi import application

serve(application, host=host, port=port, threads=threads, url_scheme='https')
```

ทดสอบรันก่อนติดตั้ง service:

```powershell
cd C:\project\liblogin
.\venv\Scripts\python.exe deploy\waitress_serve.py
# ต้องเห็น: [START] LibLogin 127.0.0.1:8002 (8 threads)
# กด Ctrl+C เพื่อหยุด
```

---

## 9. ติดตั้ง NSSM Service

```powershell
# สร้าง Service
C:\nssm\nssm.exe install LibLogin `
    "C:\project\liblogin\venv\Scripts\python.exe" `
    "C:\project\liblogin\deploy\waitress_serve.py"

# ตั้งค่า working directory
C:\nssm\nssm.exe set LibLogin AppDirectory "C:\project\liblogin"

# ตั้งค่า Auto Start
C:\nssm\nssm.exe set LibLogin Start SERVICE_AUTO_START

# สร้างโฟลเดอร์ logs
New-Item -ItemType Directory -Path "C:\project\liblogin\logs" -Force

# ตั้งค่า Log
C:\nssm\nssm.exe set LibLogin AppStdout "C:\project\liblogin\logs\waitress.log"
C:\nssm\nssm.exe set LibLogin AppStderr "C:\project\liblogin\logs\waitress_error.log"
C:\nssm\nssm.exe set LibLogin AppRotateFiles 1
C:\nssm\nssm.exe set LibLogin AppRotateBytes 10485760

# Start Service
C:\nssm\nssm.exe start LibLogin
C:\nssm\nssm.exe status LibLogin
# ต้องได้: SERVICE_RUNNING
```

ดู log แบบ real-time:

```powershell
Get-Content "C:\project\liblogin\logs\waitress.log" -Tail 20 -Wait
```

---

## 10. ทดสอบ Waitress โดยตรง

```powershell
# ทดสอบ login page (ต้องได้ StatusCode: 200)
Invoke-WebRequest -Uri "http://localhost:8002/login/" -UseBasicParsing

# ทดสอบ hotspot page
Invoke-WebRequest -Uri "http://localhost:8002/hotspot/login/" -UseBasicParsing

# ทดสอบ API
Invoke-WebRequest -Uri "http://localhost:8002/api/" -UseBasicParsing
```

---

## 11. IIS Virtual Directories (Static + Media)

LibLogin มีไฟล์ 2 ประเภทที่ต้อง serve ผ่าน IIS โดยตรง:

### 11.1 Static Files (`/liblogin/static/`)

```powershell
Import-Module WebAdministration
New-WebVirtualDirectory -Site "Default Web Site" -Application "/" `
    -Name "liblogin/static" `
    -PhysicalPath "C:\project\liblogin\staticfiles"
```

หรือทำผ่าน IIS Manager:
```
Default Web Site → Add Virtual Directory
  Alias:         liblogin/static
  Physical path: C:\project\liblogin\staticfiles
```

### 11.2 Media Files (`/liblogin/media/`)

Media files คือรูปพื้นหลัง hotspot ที่บรรณารักษ์อัปโหลด ต้อง serve แยกต่างหาก:

```powershell
New-WebVirtualDirectory -Site "Default Web Site" -Application "/" `
    -Name "liblogin/media" `
    -PhysicalPath "C:\project\liblogin\media"
```

หรือทำผ่าน IIS Manager:
```
Default Web Site → Add Virtual Directory
  Alias:         liblogin/media
  Physical path: C:\project\liblogin\media
```

> **หมายเหตุ:** สร้างโฟลเดอร์ media ก่อนถ้ายังไม่มี:
> `New-Item -ItemType Directory -Path "C:\project\liblogin\media" -Force`

---

## 12. แก้ไข web.config

**Backup ก่อนเสมอ!**

```powershell
Copy-Item "C:\iis_root\web.config" `
    "C:\iis_root\web.config.bak$(Get-Date -Format 'yyyyMMdd_HHmm')" -Force
```

เปิดแก้ไข `C:\iis_root\web.config` และ **เพิ่ม rules 3 บรรทัดนี้** ใน `<rules>` block ต่อจาก AIMS (App 2):

```xml
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
```

### web.config ฉบับสมบูรณ์หลัง deploy LibLogin

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

Restart IIS หลังแก้ไข:

```powershell
iisreset /restart
```

---

## 13. ทดสอบผ่าน HTTPS

```powershell
# ทดสอบ login page
$r = Invoke-WebRequest "https://lib.npu.ac.th/liblogin/login/" -UseBasicParsing
Write-Host "Status: $($r.StatusCode)"    # ต้องได้ 200

# ทดสอบ hotspot page (ที่ MikroTik จะเรียกใช้)
Invoke-WebRequest "https://lib.npu.ac.th/liblogin/hotspot/login/" -UseBasicParsing

# ทดสอบ static file
Invoke-WebRequest "https://lib.npu.ac.th/liblogin/static/css/login.css" -UseBasicParsing

# ทดสอบทุก App พร้อมกัน
"projects","aims","liblogin" | ForEach-Object {
    $url = "https://lib.npu.ac.th/$_/"
    $r = try { Invoke-WebRequest $url -UseBasicParsing } catch { $_.Exception.Response }
    Write-Host "$_ : $($r.StatusCode)"
}
```

---

## 14. การบำรุงรักษา

### คำสั่ง NSSM ที่ใช้บ่อย

```powershell
# ดูสถานะ
C:\nssm\nssm.exe status LibLogin

# Restart (เช่น หลัง git pull)
C:\nssm\nssm.exe restart LibLogin

# Stop / Start
C:\nssm\nssm.exe stop LibLogin
C:\nssm\nssm.exe start LibLogin

# ดู error log
Get-Content "C:\project\liblogin\logs\waitress_error.log" -Tail 50 -Wait
```

### อัปเดตโค้ด

```powershell
cd C:\project\liblogin
git pull origin main

$env:DJANGO_SETTINGS_MODULE = "backend.settings"
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py collectstatic --noinput

C:\nssm\nssm.exe restart LibLogin
C:\nssm\nssm.exe status LibLogin
# ต้องได้: SERVICE_RUNNING
```

### Backup Database

```powershell
# Backup db.sqlite3 (ทำก่อนทุกครั้งที่ update)
$ts = Get-Date -Format 'yyyyMMdd_HHmm'
New-Item -ItemType Directory -Path "C:\project\liblogin\backups" -Force
Copy-Item "C:\project\liblogin\db.sqlite3" `
    "C:\project\liblogin\backups\db_$ts.sqlite3"

# Backup media (รูปที่อัปโหลด)
xcopy "C:\project\liblogin\media" `
    "C:\project\liblogin\backups\media_$ts\" /E /I /Y
```

---

## 15. ข้อผิดพลาดที่พบบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| `SERVICE_PAUSED` | Process crash → NSSM pause | ดู error log: `Get-Content logs\waitress_error.log -Tail 30` |
| `ModuleNotFoundError: No module named 'backend'` | `DJANGO_SETTINGS_MODULE` ค้างจากระบบอื่น | ตั้ง `$env:DJANGO_SETTINGS_MODULE = "backend.settings"` |
| `UnicodeEncodeError: 'charmap' codec` | มี emoji ใน print() ของ waitress_serve.py | ลบ emoji ออก + ตรวจสอบ `sys.stdout.reconfigure` อยู่บนสุด |
| `400 Bad Request` | IP/hostname ไม่อยู่ใน `ALLOWED_HOSTS` | เพิ่ม IP ใน `.env` บรรทัด `ALLOWED_HOSTS` |
| `404 Not Found` ที่ `/liblogin/` | `FORCE_SCRIPT_NAME` ทำให้ root redirect ผิด | ทดสอบที่ `/liblogin/login/` แทน |
| Static files ไม่โหลด | ยังไม่ได้ทำ IIS Virtual Directory | ตรวจ IIS Manager: `liblogin/static` ชี้ไปที่ `staticfiles/` ถูกต้องหรือไม่ |
| รูปพื้นหลัง (media) ไม่โหลด | ยังไม่ได้ทำ Virtual Directory สำหรับ media | ตรวจ IIS Manager: `liblogin/media` ชี้ไปที่ `media/` ถูกต้องหรือไม่ |
| `502 Bad Gateway` | Waitress service ไม่รัน | `C:\nssm\nssm.exe start LibLogin` |
| CSRF Error login ไม่ได้ | `CSRF_TRUSTED_ORIGINS` ไม่ถูกต้อง | ตรวจ `.env`: `CSRF_TRUSTED_ORIGINS=https://lib.npu.ac.th` |
| `ImproperlyConfigured: FORCE_SCRIPT_NAME` | settings.py ยังไม่ได้แก้ไขตาม [ส่วนที่ 1](#1-กอน-deploy--แกไข-settingspy) | แก้ไข settings.py ก่อน deploy |
| MikroTik ขึ้น login page ผิด URL | `FORCE_SCRIPT_NAME` ไม่ถูกต้องใน .env | ตรวจ `.env`: `FORCE_SCRIPT_NAME=/liblogin` |

---

## ภาคผนวก — โครงสร้างโฟลเดอร์บน Server

```
C:\project\liblogin\
├── .env                     ← Production environment variables (อย่า commit!)
├── db.sqlite3               ← SQLite database
├── manage.py
├── requirements.txt
│
├── backend\                 ← Django project package
│   ├── settings.py          ← ต้องแก้ไขก่อน deploy (ดูส่วนที่ 1)
│   ├── urls.py
│   └── wsgi.py
│
├── api\                     ← REST API app
├── webapp\                  ← Frontend webapp
│
├── staticfiles\             ← Collected static files (สร้างโดย collectstatic)
├── media\                   ← Uploaded images (รูปพื้นหลัง hotspot)
├── fonts\                   ← TH Sarabun fonts (สำหรับ PDF)
│
├── logs\                    ← NSSM service logs
│   ├── waitress.log
│   └── waitress_error.log
│
├── backups\                 ← Database backups
│
├── venv\                    ← Python virtual environment
│   └── Scripts\
│       ├── python.exe
│       └── pip.exe
│
└── deploy\
    └── waitress_serve.py    ← Waitress startup script สำหรับ NSSM
```

---

## ภาคผนวก — URL ระบบ LibLogin บน Production

| URL | คำอธิบาย | ผู้ใช้งาน |
|-----|----------|-----------|
| `https://lib.npu.ac.th/liblogin/login/` | หน้า Login ระบบ | บรรณารักษ์ |
| `https://lib.npu.ac.th/liblogin/` | Dashboard หลัก | บรรณารักษ์ |
| `https://lib.npu.ac.th/liblogin/backgrounds/` | จัดการรูปพื้นหลัง | บรรณารักษ์ |
| `https://lib.npu.ac.th/liblogin/hotspot/login/` | หน้า Login WiFi | ผู้ใช้ WiFi / MikroTik |
| `https://lib.npu.ac.th/liblogin/hotspot/logout/` | หน้า Logout WiFi | ผู้ใช้ WiFi / MikroTik |
| `https://lib.npu.ac.th/liblogin/hotspot/status/` | หน้า Status WiFi | ผู้ใช้ WiFi / MikroTik |
| `https://lib.npu.ac.th/liblogin/api/` | REST API | MikroTik / Internal |
| `https://lib.npu.ac.th/liblogin/admin/` | Django Admin | Superuser |

### MikroTik Hotspot Configuration

ตั้งค่า Login Page บน MikroTik ชี้มาที่:
```
https://lib.npu.ac.th/liblogin/hotspot/login/
```

---

*เอกสารนี้จัดทำสำหรับการ Deploy ระบบ LibLogin บน lib.npu.ac.th
งานเทคนิคสารสนเทศและการจัดการทรัพยากร สำนักวิทยบริการ มหาวิทยาลัยนครพนม*
