@echo off
REM ดึงวันหยุดราชการเข้าระบบจอง (ล่วงหน้า 1 ปี เป็นฉบับร่างรอเจ้าหน้าที่ตรวจ)
REM ตั้งให้ Task Scheduler รันเดือนละครั้ง — ดู doc/deploy_guide.md
REM
REM production มี venv ต้องเรียก python ผ่าน venv เสมอ ห้ามเรียก python เปล่า ๆ

setlocal
set PROJECT_DIR=C:\project\reserv
set LOG=%PROJECT_DIR%\logs\sync_holidays.log

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

echo. >> "%LOG%"
echo ===== %DATE% %TIME% ===== >> "%LOG%"
"%PROJECT_DIR%\venv\Scripts\python.exe" "%PROJECT_DIR%\manage.py" sync_holidays >> "%LOG%" 2>&1
echo exit code %ERRORLEVEL% >> "%LOG%"
endlocal
