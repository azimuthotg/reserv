"""Generate admin panel mockup screenshots for the admin manual."""
from playwright.sync_api import sync_playwright

SIDEBAR = """
<style>
:root{--sb:#1a1f2e;--green:#06C755;--sw:220px;--th:52px;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#f0f2f5;font-family:'Sarabun',Arial,sans-serif;font-size:14px;}
#sidebar{position:fixed;top:0;left:0;bottom:0;width:var(--sw);background:var(--sb);z-index:99;overflow-y:auto;}
.sb-brand{padding:14px 16px 10px;border-bottom:1px solid rgba(255,255,255,.08);}
.sb-brand .sub{color:var(--green);font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;}
.sb-brand .title{color:#fff;font-size:14px;font-weight:700;line-height:1.2;}
.sb-brand .org{color:rgba(255,255,255,.4);font-size:10px;margin-top:2px;}
.sb-section{color:rgba(255,255,255,.35);font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:14px 16px 4px;}
.sb-item a{display:flex;align-items:center;gap:8px;padding:9px 16px;color:rgba(255,255,255,.7);text-decoration:none;font-size:13px;border-left:3px solid transparent;}
.sb-item a:hover,.sb-item a.active{background:rgba(6,199,85,.12);color:var(--green);border-left-color:var(--green);font-weight:600;}
.sb-item a i{font-size:15px;width:18px;text-align:center;}
#topbar{position:fixed;top:0;left:var(--sw);right:0;height:var(--th);background:#fff;border-bottom:1px solid #e8e8e8;display:flex;align-items:center;padding:0 20px;z-index:98;justify-content:space-between;}
.tb-title{font-size:15px;font-weight:700;color:#222;}
#main{margin-left:var(--sw);margin-top:var(--th);padding:20px;}
.stat-card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,.07);}
.stat-value{font-size:26px;font-weight:700;color:#222;}
.stat-label{font-size:12px;color:#888;margin-top:2px;}
.stat-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.table-card{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.07);overflow:hidden;margin-bottom:16px;}
.tc-header{padding:12px 16px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;justify-content:space-between;}
.tc-title{font-size:14px;font-weight:700;color:#222;}
table{width:100%;border-collapse:collapse;}
th{padding:8px 12px;font-size:11px;font-weight:700;color:#888;text-transform:uppercase;background:#f8f9fa;text-align:left;}
td{padding:8px 12px;font-size:13px;border-bottom:1px solid #f5f5f5;}
tr:last-child td{border-bottom:none;}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;}
.badge-ok{background:#e8f9ee;color:#06C755;}
.badge-cancel{background:#ffeaea;color:#dc3545;}
.badge-admin{background:#dc3545;color:#fff;}
.badge-staff{background:#6c757d;color:#fff;}
.btn{display:inline-block;padding:4px 12px;border-radius:6px;font-size:12px;cursor:pointer;border:none;text-decoration:none;}
.btn-green{background:#06C755;color:#fff;}
.btn-sm{padding:3px 8px;font-size:11px;}
.btn-outline{background:#fff;border:1px solid #dee2e6;color:#555;}
.btn-outline-warn{background:#fff;border:1px solid #ffc107;color:#856404;}
.btn-outline-danger{background:#fff;border:1px solid #dc3545;color:#dc3545;}
.btn-outline-success{background:#fff;border:1px solid #198754;color:#198754;}
.row{display:grid;gap:12px;}
.row-4{grid-template-columns:repeat(4,1fr);}
.row-2{grid-template-columns:2fr 1fr;}
.form-control{display:block;width:100%;padding:5px 10px;border:1px solid #dee2e6;border-radius:6px;font-size:13px;color:#333;background:#fff;}
.form-label{display:block;font-size:11px;font-weight:600;color:#888;margin-bottom:3px;}
.row-form{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));}
.filter-bar{padding:12px 16px;}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
"""

def sidebar_html(active="dashboard", is_admin=True):
    def a(name, icon, label, url="#"):
        cls = "active" if name == active else ""
        return f'<div class="sb-item"><a href="{url}" class="{cls}"><i class="bi bi-{icon}"></i> {label}</a></div>'
    admin_section = ""
    if is_admin:
        admin_section = f"""
        <div class="sb-section">ผู้ดูแลระบบ</div>
        {a("rooms","door-open","จัดการห้อง")}
        {a("staff","person-gear","เจ้าหน้าที่")}
        """
    return f"""
    <nav id="sidebar">
      <div class="sb-brand">
        <div class="sub">Staff Portal</div>
        <div class="title">Library@NPU</div>
        <div class="org">สำนักวิทยบริการ มนพ.</div>
      </div>
      <div style="padding:10px 0;">
        <div class="sb-section">เมนูหลัก</div>
        {a("dashboard","speedometer2","Dashboard")}
        {a("bookings","calendar-check","รายการจอง")}
        {a("holidays","calendar-x","วันหยุด")}
        {a("line_users","people","ผู้ใช้ LINE")}
        {admin_section}
        <div class="sb-section" style="margin-top:6px;"></div>
        <div class="sb-item"><a href="#"><i class="bi bi-box-arrow-right"></i> ออกจากระบบ</a></div>
      </div>
    </nav>
    """

def topbar_html(title, is_admin=True):
    role_badge = '<span class="badge badge-admin" style="font-size:10px;">ผู้ดูแลระบบ</span>' if is_admin else '<span class="badge badge-staff" style="font-size:10px;">เจ้าหน้าที่</span>'
    return f"""
    <div id="topbar">
      <span class="tb-title">{title}</span>
      <div style="display:flex;align-items:center;gap:8px;">
        {role_badge}
        <span style="font-size:13px;color:#555;">สมชาย ใจดี</span>
      </div>
    </div>
    """

screenshots = {}

# ── 01 Login ──────────────────────────────────────────────────────────────────
screenshots["admin_01_login.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}
<style>
body{{background:linear-gradient(135deg,#1a1f2e 0%,#2a3148 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;}}
.login-card{{background:#fff;border-radius:16px;padding:40px 36px;width:380px;box-shadow:0 8px 32px rgba(0,0,0,.25);}}
.login-logo{{text-align:center;margin-bottom:24px;}}
.login-logo .sub{{color:#06C755;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;}}
.login-logo .title{{font-size:22px;font-weight:800;color:#1a1f2e;}}
.login-logo .org{{font-size:12px;color:#888;margin-top:2px;}}
.form-group{{margin-bottom:16px;}}
label{{display:block;font-size:12px;font-weight:700;color:#555;margin-bottom:5px;}}
input{{width:100%;padding:9px 12px;border:1px solid #dee2e6;border-radius:8px;font-size:14px;}}
input:focus{{outline:none;border-color:#06C755;}}
.btn-login{{width:100%;background:#06C755;color:#fff;border:none;border-radius:8px;padding:10px;font-size:15px;font-weight:700;cursor:pointer;margin-top:4px;}}
</style></head><body>
<div class="login-card">
  <div class="login-logo">
    <div class="sub">Staff Portal</div>
    <div class="title">Library@NPU</div>
    <div class="org">ระบบจัดการการจองพื้นที่บริการ</div>
  </div>
  <div class="form-group">
    <label>ชื่อผู้ใช้</label>
    <input type="text" value="librarian01" placeholder="username">
  </div>
  <div class="form-group">
    <label>รหัสผ่าน</label>
    <input type="password" value="••••••••" placeholder="password">
  </div>
  <button class="btn-login">เข้าสู่ระบบ</button>
  <div style="text-align:center;margin-top:14px;font-size:12px;color:#aaa;">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</div>
</div>
</body></html>"""

# ── 02 Dashboard ──────────────────────────────────────────────────────────────
screenshots["admin_02_dashboard.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("dashboard")}
{topbar_html("Dashboard")}
<div id="main">
  <div class="row row-4" style="margin-bottom:16px;">
    <div class="stat-card">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div><div class="stat-value">7</div><div class="stat-label">การจองวันนี้</div></div>
        <div class="stat-icon" style="background:#e8f9ee;color:#06C755;"><i class="bi bi-calendar-day"></i></div>
      </div>
    </div>
    <div class="stat-card">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div><div class="stat-value">23</div><div class="stat-label">รอดำเนินการ</div></div>
        <div class="stat-icon" style="background:#fff3e0;color:#ff9800;"><i class="bi bi-clock"></i></div>
      </div>
    </div>
    <div class="stat-card">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div><div class="stat-value">142</div><div class="stat-label">จองเดือนนี้</div></div>
        <div class="stat-icon" style="background:#e3f2fd;color:#1976d2;"><i class="bi bi-calendar-month"></i></div>
      </div>
    </div>
    <div class="stat-card">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div><div class="stat-value">318</div><div class="stat-label">ผู้ใช้ LINE</div></div>
        <div class="stat-icon" style="background:#f3e5f5;color:#9c27b0;"><i class="bi bi-people"></i></div>
      </div>
    </div>
  </div>
  <div class="row row-2">
    <div class="table-card">
      <div class="tc-header"><span class="tc-title">การจองล่าสุด</span><a href="#" class="btn btn-sm btn-green">ดูทั้งหมด</a></div>
      <table>
        <thead><tr><th>ห้อง</th><th>วันที่</th><th>เวลา</th><th>กลุ่ม</th><th>ผู้จอง</th></tr></thead>
        <tbody>
          <tr><td>Mini Theater</td><td>20/04/2026</td><td>09:00–11:00</td><td>นิเทศศาสตร์ ม.1</td><td>สุดา มีสุข</td></tr>
          <tr><td>Netflix Room</td><td>20/04/2026</td><td>13:00–15:00</td><td>ดูหนังกลุ่ม IT</td><td>ธนกฤต สว่าง</td></tr>
          <tr><td>Canva Studio</td><td>20/04/2026</td><td>14:00–16:00</td><td>ออกแบบโปสเตอร์</td><td>อารียา โชค</td></tr>
          <tr><td>ChatGPT Room</td><td>19/04/2026</td><td>10:00–12:00</td><td>AI Workshop</td><td>วิทยา พงษ์ดี</td></tr>
          <tr><td>Meeting F1</td><td>19/04/2026</td><td>13:30–15:30</td><td>ประชุมคณะ</td><td>ดร.ประสิทธิ์ นาม</td></tr>
        </tbody>
      </table>
    </div>
    <div class="table-card">
      <div class="tc-header"><span class="tc-title">วันหยุดที่กำลังจะมา</span><a href="#" class="btn btn-sm btn-outline">จัดการ</a></div>
      <div style="padding:4px 0;">
        <div style="padding:8px 16px;border-bottom:1px solid #f5f5f5;"><div style="font-weight:600;font-size:13px;">01 พ.ค. 2026</div><div style="color:#888;font-size:12px;">วันแรงงานแห่งชาติ</div></div>
        <div style="padding:8px 16px;border-bottom:1px solid #f5f5f5;"><div style="font-weight:600;font-size:13px;">05 พ.ค. 2026</div><div style="color:#888;font-size:12px;">วันฉัตรมงคล</div></div>
        <div style="padding:8px 16px;"><div style="font-weight:600;font-size:13px;">22 พ.ค. 2026</div><div style="color:#888;font-size:12px;">วันวิสาขบูชา</div></div>
      </div>
    </div>
  </div>
</div>
</body></html>"""

# ── 03 Bookings ───────────────────────────────────────────────────────────────
screenshots["admin_03_bookings.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("bookings")}
{topbar_html("รายการจอง")}
<div id="main">
  <div class="table-card" style="margin-bottom:12px;">
    <div class="filter-bar">
      <div class="row-form">
        <div><div class="form-label">ห้อง</div><select class="form-control"><option>ทั้งหมด</option></select></div>
        <div><div class="form-label">วันที่</div><input type="date" class="form-control" value="2026-04-20"></div>
        <div><div class="form-label">สถานะ</div><select class="form-control"><option>ยืนยันแล้ว</option></select></div>
        <div><div class="form-label">ค้นหา</div><input type="text" class="form-control" placeholder="ชื่อกลุ่ม / ผู้จอง / คณะ"></div>
        <div style="display:flex;align-items:flex-end;"><button class="btn btn-green" style="width:100%;">ค้นหา</button></div>
      </div>
    </div>
  </div>
  <div class="table-card">
    <div class="tc-header"><span class="tc-title">พบ 7 รายการ</span></div>
    <table>
      <thead><tr><th>#</th><th>ห้อง</th><th>วันที่</th><th>เวลา</th><th>กลุ่ม / กิจกรรม</th><th>ผู้จอง</th><th>คณะ</th><th>สถานะ</th><th></th></tr></thead>
      <tbody>
        <tr><td style="color:#aaa;">101</td><td>Mini Theater</td><td>20/04/2026</td><td>09:00–11:00</td><td>นิเทศศาสตร์ ม.1</td><td><a href="#" style="color:#229799;text-decoration:none;">สุดา มีสุข</a></td><td style="color:#888;font-size:12px;">นิเทศศาสตร์</td><td><span class="badge badge-ok">ยืนยันแล้ว</span></td><td><a href="#" class="btn btn-sm btn-outline" title="Logs"><i class="bi bi-clock-history"></i></a> <button class="btn btn-sm btn-outline-danger">ยกเลิก</button></td></tr>
        <tr><td style="color:#aaa;">102</td><td>Netflix Room</td><td>20/04/2026</td><td>13:00–15:00</td><td>ดูหนังกลุ่ม IT</td><td><a href="#" style="color:#229799;text-decoration:none;">ธนกฤต สว่าง</a></td><td style="color:#888;font-size:12px;">เทคโนโลยีสารสนเทศ</td><td><span class="badge badge-ok">ยืนยันแล้ว</span></td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-clock-history"></i></a> <button class="btn btn-sm btn-outline-danger">ยกเลิก</button></td></tr>
        <tr style="opacity:.65;"><td style="color:#aaa;">98</td><td>Canva Studio</td><td>18/04/2026</td><td>14:00–16:00</td><td>ออกแบบโปสเตอร์<div style="font-size:11px;color:#dc3545;margin-top:2px;"><i class="bi bi-x-circle"></i> ห้องปิดซ่อม</div></td><td><a href="#" style="color:#229799;text-decoration:none;">อารียา โชค</a></td><td style="color:#888;font-size:12px;">ศิลปกรรมศาสตร์</td><td><span class="badge badge-cancel">ยกเลิก</span></td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-clock-history"></i></a></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── 04 Cancel Modal ───────────────────────────────────────────────────────────
screenshots["admin_04_cancel_modal.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}
<style>
.overlay{{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:200;display:flex;align-items:center;justify-content:center;}}
.modal-card{{background:#fff;border-radius:12px;width:420px;box-shadow:0 8px 32px rgba(0,0,0,.2);overflow:hidden;}}
.modal-head{{padding:14px 18px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;}}
.modal-head h6{{font-size:14px;font-weight:700;margin:0;}}
.modal-body{{padding:16px 18px;}}
.modal-body p{{font-size:14px;margin-bottom:12px;}}
textarea{{width:100%;border:1px solid #dee2e6;border-radius:6px;padding:7px 10px;font-size:13px;resize:none;}}
.modal-foot{{padding:12px 18px;border-top:1px solid #f0f0f0;display:flex;justify-content:flex-end;gap:8px;}}
</style></head><body style="background:#f0f2f5;">
{sidebar_html("bookings")}
{topbar_html("รายการจอง")}
<div id="main" style="opacity:.3;">...</div>
<div class="overlay">
  <div class="modal-card">
    <div class="modal-head">
      <h6>ยืนยันการยกเลิกการจอง</h6>
      <span style="cursor:pointer;font-size:18px;color:#888;">×</span>
    </div>
    <div class="modal-body">
      <p>ยืนยันยกเลิกการจอง "<strong>นิเทศศาสตร์ ม.1</strong>" ?</p>
      <div class="form-label">เหตุผล (ถ้ามี)</div>
      <textarea rows="2" placeholder="เช่น ห้องปิดปรับปรุง"></textarea>
    </div>
    <div class="modal-foot">
      <button class="btn btn-outline">ยกเลิก</button>
      <button class="btn" style="background:#dc3545;color:#fff;">ยืนยันยกเลิก</button>
    </div>
  </div>
</div>
</body></html>"""

# ── 05 Booking Logs ───────────────────────────────────────────────────────────
screenshots["admin_05_booking_logs.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("bookings")}
{topbar_html("Logs การจอง #101")}
<div id="main">
  <div style="margin-bottom:12px;">
    <a href="#" class="btn btn-sm btn-outline"><i class="bi bi-arrow-left"></i> กลับรายการจอง</a>
  </div>
  <div class="table-card" style="padding:18px;margin-bottom:12px;">
    <div class="row" style="grid-template-columns:repeat(4,1fr);gap:12px;">
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">ห้อง</div><div style="font-size:15px;font-weight:700;margin-top:3px;">Mini Theater</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">วันที่</div><div style="font-size:15px;font-weight:700;margin-top:3px;">20/04/2026</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">เวลา</div><div style="font-size:15px;font-weight:700;margin-top:3px;">09:00–11:00</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">สถานะ</div><div style="margin-top:5px;"><span class="badge badge-ok">ยืนยันแล้ว</span></div></div>
      <div style="grid-column:span 2;"><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">ผู้จอง</div><div style="margin-top:3px;font-size:14px;"><a href="#" style="color:#229799;text-decoration:none;">สุดา มีสุข</a> <span style="color:#888;font-size:12px;"> — นักศึกษา</span></div></div>
      <div style="grid-column:span 2;"><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:.5px;">กลุ่ม / กิจกรรม</div><div style="margin-top:3px;font-size:14px;">นิเทศศาสตร์ ม.1</div></div>
    </div>
  </div>
  <div class="table-card">
    <div class="tc-header"><span class="tc-title"><i class="bi bi-clock-history"></i> ประวัติการดำเนินการ</span></div>
    <div style="padding:20px;position:relative;">
      <div style="position:absolute;left:37px;top:56px;width:2px;background:#e2e8f0;height:120px;"></div>
      <div style="display:flex;gap:14px;margin-bottom:20px;">
        <div style="flex-shrink:0;width:34px;height:34px;border-radius:50%;background:#d1fae5;color:#059669;display:flex;align-items:center;justify-content:center;font-size:15px;z-index:1;"><i class="bi bi-plus-circle-fill"></i></div>
        <div style="padding-top:3px;">
          <div style="font-weight:700;font-size:14px;">สร้างการจอง</div>
          <div style="font-size:12px;color:#a0aec0;margin-top:3px;"><i class="bi bi-clock"></i> 18/04/2026 14:23:10</div>
        </div>
      </div>
      <div style="display:flex;gap:14px;margin-bottom:20px;">
        <div style="flex-shrink:0;width:34px;height:34px;border-radius:50%;background:#e0e7ff;color:#4f46e5;display:flex;align-items:center;justify-content:center;font-size:15px;z-index:1;"><i class="bi bi-info-circle-fill"></i></div>
        <div style="padding-top:3px;">
          <div style="font-weight:700;font-size:14px;">เข้าถึงข้อมูล</div>
          <div style="font-size:13px;color:#718096;margin-top:2px;">เจ้าหน้าที่ตรวจสอบ</div>
          <div style="font-size:12px;color:#a0aec0;margin-top:3px;"><i class="bi bi-clock"></i> 19/04/2026 09:05:44</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>"""

# ── 06 Holidays ───────────────────────────────────────────────────────────────
screenshots["admin_06_holidays.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("holidays")}
{topbar_html("จัดการวันหยุด")}
<div id="main">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <div style="display:flex;gap:6px;">
      <a href="#" class="btn btn-sm btn-green">2026</a>
      <a href="#" class="btn btn-sm btn-outline">2027</a>
      <a href="#" class="btn btn-sm btn-outline">2028</a>
    </div>
    <a href="#" class="btn btn-sm btn-green"><i class="bi bi-plus-lg"></i> เพิ่มวันหยุด</a>
  </div>
  <div class="table-card">
    <table>
      <thead><tr><th>วันที่</th><th>วัน</th><th>คำอธิบาย</th><th>สถานะ</th><th></th></tr></thead>
      <tbody>
        <tr><td style="font-weight:700;">01/01/2026</td><td style="color:#888;">Thursday</td><td>วันขึ้นปีใหม่</td><td><span class="badge badge-ok">เปิดใช้</span></td><td><button class="btn btn-sm btn-outline-warn">ปิดใช้</button> <button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-danger">ลบ</button></td></tr>
        <tr><td style="font-weight:700;">01/05/2026</td><td style="color:#888;">Friday</td><td>วันแรงงานแห่งชาติ</td><td><span class="badge badge-ok">เปิดใช้</span></td><td><button class="btn btn-sm btn-outline-warn">ปิดใช้</button> <button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-danger">ลบ</button></td></tr>
        <tr><td style="font-weight:700;">12/06/2026</td><td style="color:#888;">Friday</td><td>ปิดบำรุงห้องสมุด</td><td><span class="badge badge-cancel">ปิดใช้</span></td><td><button class="btn btn-sm btn-outline-success">เปิดใช้</button> <button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-danger">ลบ</button></td></tr>
        <tr><td style="font-weight:700;">22/05/2026</td><td style="color:#888;">Friday</td><td>วันวิสาขบูชา</td><td><span class="badge badge-ok">เปิดใช้</span></td><td><button class="btn btn-sm btn-outline-warn">ปิดใช้</button> <button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-danger">ลบ</button></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── 07 Add Holiday Form ───────────────────────────────────────────────────────
screenshots["admin_07_holiday_form.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("holidays")}
{topbar_html("เพิ่มวันหยุด")}
<div id="main">
  <div style="margin-bottom:12px;">
    <a href="#" class="btn btn-sm btn-outline"><i class="bi bi-arrow-left"></i> กลับ</a>
  </div>
  <div class="table-card" style="max-width:500px;padding:24px;">
    <div style="font-size:16px;font-weight:700;margin-bottom:18px;color:#1a1f2e;">เพิ่มวันหยุด</div>
    <div style="margin-bottom:14px;">
      <div class="form-label">วันที่</div>
      <input type="date" class="form-control" value="2026-06-03">
    </div>
    <div style="margin-bottom:14px;">
      <div class="form-label">คำอธิบาย</div>
      <input type="text" class="form-control" value="วันเฉลิมพระชนมพรรษา ร.10">
    </div>
    <div style="margin-bottom:14px;">
      <div class="form-label">สถานะ</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
        <input type="checkbox" checked style="width:16px;height:16px;accent-color:#06C755;">
        <span style="font-size:13px;">เปิดใช้งาน (ระบบจะปิดรับจองวันนี้)</span>
      </div>
    </div>
    <div style="display:flex;gap:8px;margin-top:18px;">
      <button class="btn btn-green">บันทึก</button>
      <a href="#" class="btn btn-outline">ยกเลิก</a>
    </div>
  </div>
</div>
</body></html>"""

# ── 08 LINE Users ─────────────────────────────────────────────────────────────
screenshots["admin_08_line_users.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("line_users")}
{topbar_html("ผู้ใช้ LINE")}
<div id="main">
  <div class="table-card" style="margin-bottom:12px;">
    <div class="filter-bar">
      <div class="row-form">
        <div><div class="form-label">ค้นหา</div><input type="text" class="form-control" placeholder="ชื่อ / รหัส LDAP / คณะ"></div>
        <div><div class="form-label">ประเภท</div><select class="form-control"><option>ทั้งหมด</option><option>นักศึกษา</option><option>บุคลากร</option></select></div>
        <div style="display:flex;align-items:flex-end;"><button class="btn btn-green" style="width:100%;">ค้นหา</button></div>
      </div>
    </div>
  </div>
  <div class="table-card">
    <div class="tc-header"><span class="tc-title">พบ 318 รายการ</span></div>
    <table>
      <thead><tr><th>ชื่อ-นามสกุล</th><th>รหัส LDAP</th><th>ประเภท</th><th>คณะ / หน่วยงาน</th><th>สาขา / ฝ่าย</th><th>ลงทะเบียน</th><th>สถานะ</th><th></th></tr></thead>
      <tbody>
        <tr><td><div style="font-weight:600;">สุดา มีสุข</div><div style="color:#aaa;font-size:11px;">Suda Meesuk</div></td><td>65011234</td><td><span class="badge" style="background:#f0f0f0;color:#333;font-size:10px;">นักศึกษา</span></td><td style="font-size:12px;">นิเทศศาสตร์</td><td style="font-size:12px;color:#888;">สื่อสารมวลชน</td><td style="font-size:12px;color:#888;">15/03/2026</td><td><span class="badge badge-ok">ใช้งาน</span></td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-person-lines-fill"></i></a> <button class="btn btn-sm btn-outline-warn">ปิดใช้</button></td></tr>
        <tr><td><div style="font-weight:600;">ธนกฤต สว่าง</div><div style="color:#aaa;font-size:11px;">Thanakrit Sawang</div></td><td>64021567</td><td><span class="badge" style="background:#f0f0f0;color:#333;font-size:10px;">นักศึกษา</span></td><td style="font-size:12px;">เทคโนโลยีสารสนเทศ</td><td style="font-size:12px;color:#888;">IT</td><td style="font-size:12px;color:#888;">10/02/2026</td><td><span class="badge badge-ok">ใช้งาน</span></td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-person-lines-fill"></i></a> <button class="btn btn-sm btn-outline-warn">ปิดใช้</button></td></tr>
        <tr style="opacity:.55;"><td><div style="font-weight:600;">มานะ หาญ</div><div style="color:#aaa;font-size:11px;">Mana Harn</div></td><td>63031890</td><td><span class="badge" style="background:#f0f0f0;color:#333;font-size:10px;">บุคลากร</span></td><td style="font-size:12px;">สำนักงานอธิการบดี</td><td style="font-size:12px;color:#888;">งานบุคคล</td><td style="font-size:12px;color:#888;">05/01/2026</td><td><span class="badge badge-cancel">ปิดใช้</span></td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-person-lines-fill"></i></a> <button class="btn btn-sm btn-outline-success">เปิดใช้</button></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── 09 User Detail ────────────────────────────────────────────────────────────
screenshots["admin_09_user_detail.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("line_users")}
{topbar_html("ประวัติผู้ใช้")}
<div id="main">
  <div style="margin-bottom:12px;">
    <a href="#" class="btn btn-sm btn-outline"><i class="bi bi-arrow-left"></i> กลับรายชื่อผู้ใช้</a>
  </div>
  <div class="table-card" style="padding:20px;margin-bottom:12px;">
    <div style="display:flex;gap:16px;align-items:start;margin-bottom:16px;">
      <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#229799,#1a7a7c);display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;">👤</div>
      <div style="flex:1;">
        <div style="font-size:18px;font-weight:700;color:#1a202c;">สุดา มีสุข</div>
        <div style="color:#718096;font-size:12px;margin-top:2px;">Suda Meesuk</div>
        <div style="display:flex;gap:6px;margin-top:8px;">
          <span class="badge" style="background:#f0f0f0;color:#333;font-size:11px;">นักศึกษา</span>
          <span class="badge badge-ok">ใช้งาน</span>
        </div>
      </div>
      <button class="btn btn-outline-warn btn-sm">ปิดใช้งาน</button>
    </div>
    <hr style="border-color:#e2e8f0;margin:14px 0;">
    <div class="row" style="grid-template-columns:repeat(4,1fr);gap:12px;">
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;">รหัส LDAP</div><div style="font-size:14px;font-weight:700;margin-top:3px;">65011234</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;">คณะ</div><div style="font-size:13px;margin-top:3px;">นิเทศศาสตร์</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;">สาขา</div><div style="font-size:13px;margin-top:3px;">สื่อสารมวลชน</div></div>
      <div><div style="font-size:10px;color:#888;font-weight:700;text-transform:uppercase;">ลงทะเบียนเมื่อ</div><div style="font-size:13px;margin-top:3px;">15/03/2026 10:22</div></div>
    </div>
  </div>
  <div class="row row-4" style="margin-bottom:12px;">
    <div class="table-card" style="padding:14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#229799;">12</div><div style="font-size:11px;color:#718096;margin-top:3px;">จองทั้งหมด</div></div>
    <div class="table-card" style="padding:14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#059669;">10</div><div style="font-size:11px;color:#718096;margin-top:3px;">ยืนยันแล้ว</div></div>
    <div class="table-card" style="padding:14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#dc2626;">2</div><div style="font-size:11px;color:#718096;margin-top:3px;">ยกเลิกแล้ว</div></div>
    <div class="table-card" style="padding:14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#d97706;">17%</div><div style="font-size:11px;color:#718096;margin-top:3px;">อัตราการยกเลิก</div></div>
  </div>
  <div class="table-card">
    <div class="tc-header"><span class="tc-title"><i class="bi bi-calendar3"></i> ประวัติการจองทั้งหมด (12 รายการ)</span></div>
    <table>
      <thead><tr><th>#</th><th>ห้อง</th><th>วันที่</th><th>เวลา</th><th>กลุ่ม / กิจกรรม</th><th>สถานะ</th><th>เหตุผลยกเลิก</th><th></th></tr></thead>
      <tbody>
        <tr><td style="color:#aaa;">101</td><td>Mini Theater</td><td>20/04/2026</td><td>09:00–11:00</td><td>นิเทศศาสตร์ ม.1</td><td><span class="badge badge-ok">ยืนยันแล้ว</span></td><td>—</td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-clock-history"></i></a></td></tr>
        <tr style="opacity:.7;"><td style="color:#aaa;">88</td><td>Netflix Room</td><td>10/03/2026</td><td>14:00–16:00</td><td>ดูหนังสั้น</td><td><span class="badge badge-cancel">ยกเลิก</span></td><td style="font-size:12px;color:#e53e3e;">ติดสอบ</td><td><a href="#" class="btn btn-sm btn-outline"><i class="bi bi-clock-history"></i></a></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── 10 Rooms (admin) ──────────────────────────────────────────────────────────
screenshots["admin_10_rooms.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("rooms")}
{topbar_html("จัดการห้อง")}
<div id="main">
  <div style="display:flex;justify-content:flex-end;margin-bottom:12px;">
    <a href="#" class="btn btn-sm btn-green"><i class="bi bi-plus-lg"></i> เพิ่มห้อง</a>
  </div>
  <div class="table-card">
    <table>
      <thead><tr><th>ชื่อห้อง</th><th>Booking Key</th><th>ที่ตั้ง</th><th>ความจุ</th><th>เวลาเปิด–ปิด</th><th>สถานะ</th><th></th></tr></thead>
      <tbody>
        <tr><td><strong>Mini Theater</strong></td><td><code style="font-size:12px;background:#f5f5f5;padding:1px 5px;border-radius:4px;">mini</code></td><td style="font-size:12px;color:#666;">ชั้น 1 อาคารบรรณสาร</td><td>30 คน</td><td>08:00–20:00</td><td><span class="badge badge-ok">เปิด</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดห้อง</button></td></tr>
        <tr><td><strong>Netflix Room</strong></td><td><code style="font-size:12px;background:#f5f5f5;padding:1px 5px;border-radius:4px;">netflix</code></td><td style="font-size:12px;color:#666;">ชั้น 2 อาคารบรรณสาร</td><td>10 คน</td><td>08:00–20:00</td><td><span class="badge badge-ok">เปิด</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดห้อง</button></td></tr>
        <tr><td><strong>Canva Studio</strong></td><td><code style="font-size:12px;background:#f5f5f5;padding:1px 5px;border-radius:4px;">canva</code></td><td style="font-size:12px;color:#666;">ชั้น 2 อาคารบรรณสาร</td><td>8 คน</td><td>08:00–18:00</td><td><span class="badge badge-ok">เปิด</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดห้อง</button></td></tr>
        <tr><td><strong>ChatGPT Room</strong></td><td><code style="font-size:12px;background:#f5f5f5;padding:1px 5px;border-radius:4px;">chat-gpt</code></td><td style="font-size:12px;color:#666;">ชั้น 2 อาคารบรรณสาร</td><td>6 คน</td><td>08:00–18:00</td><td><span class="badge badge-ok">เปิด</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดห้อง</button></td></tr>
        <tr><td><strong>Meeting Room F1</strong></td><td><code style="font-size:12px;background:#f5f5f5;padding:1px 5px;border-radius:4px;">meeting_f1</code></td><td style="font-size:12px;color:#666;">ชั้น 1 อาคารบรรณสาร</td><td>20 คน</td><td>08:00–20:00</td><td><span class="badge badge-ok">เปิด</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดห้อง</button></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── 11 Staff (admin) ──────────────────────────────────────────────────────────
screenshots["admin_11_staff.png"] = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
{SIDEBAR}</head><body>
{sidebar_html("staff")}
{topbar_html("จัดการเจ้าหน้าที่")}
<div id="main">
  <div style="display:flex;justify-content:flex-end;margin-bottom:12px;">
    <a href="#" class="btn btn-sm btn-green"><i class="bi bi-plus-lg"></i> เพิ่มเจ้าหน้าที่</a>
  </div>
  <div class="table-card">
    <table>
      <thead><tr><th>ชื่อผู้ใช้</th><th>ชื่อ-นามสกุล</th><th>อีเมล</th><th>บทบาท</th><th>เข้าใช้ล่าสุด</th><th>สถานะ</th><th></th></tr></thead>
      <tbody>
        <tr><td><strong>admin</strong></td><td>สมชาย ใจดี</td><td style="font-size:12px;color:#888;">somchai@npu.ac.th</td><td><span class="badge badge-admin">ผู้ดูแลระบบ</span></td><td style="font-size:12px;color:#888;">20/04/2026 09:10</td><td><span class="badge badge-ok">ใช้งาน</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button></td></tr>
        <tr><td><strong>librarian01</strong></td><td>วันเพ็ญ สุขใจ</td><td style="font-size:12px;color:#888;">wanpen@npu.ac.th</td><td><span class="badge badge-staff">เจ้าหน้าที่</span></td><td style="font-size:12px;color:#888;">19/04/2026 16:44</td><td><span class="badge badge-ok">ใช้งาน</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดใช้</button></td></tr>
        <tr><td><strong>librarian02</strong></td><td>กรรณิการ์ ดีงาม</td><td style="font-size:12px;color:#888;">kanniga@npu.ac.th</td><td><span class="badge badge-staff">เจ้าหน้าที่</span></td><td style="font-size:12px;color:#888;">15/04/2026 11:20</td><td><span class="badge badge-ok">ใช้งาน</span></td><td><button class="btn btn-sm btn-outline">แก้ไข</button> <button class="btn btn-sm btn-outline-warn">ปิดใช้</button></td></tr>
      </tbody>
    </table>
  </div>
</div>
</body></html>"""

# ── Generate all screenshots ──────────────────────────────────────────────────
out_dir = "/mnt/c/projects/reserv/doc/screenshots"

with sync_playwright() as p:
    browser = p.chromium.launch()
    for fname, html in screenshots.items():
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=f"{out_dir}/{fname}", full_page=True)
        print(f"✓ {fname}")
    browser.close()

print("\nAll admin screenshots generated!")
