"""Capture user-facing screenshots — real for public pages, mockups for LIFF pages."""
from playwright.sync_api import sync_playwright
import os

BASE_URL = "https://lib.npu.ac.th/reserv"
OUT_DIR  = "/mnt/c/projects/reserv/doc/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Mockup HTML helpers ──────────────────────────────────────────────────────

COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Sarabun', 'Segoe UI', sans-serif; background: #f0f2f5; }
"""

def mock_landing():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>จองพื้นที่บริการ</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Sarabun', 'Segoe UI', sans-serif; background: #f0f2f5; }
.app-header {
  background: linear-gradient(135deg,#06C755 0%,#00a844 100%);
  padding: 16px 20px 14px; position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 8px rgba(6,199,85,.3);
}
.header-top { display: flex; align-items: center; justify-content: space-between; }
.header-brand .org  { font-size: 11px; color: rgba(255,255,255,.8); margin-bottom: 2px; }
.header-brand .name { font-size: 18px; font-weight: 700; color: #fff; line-height: 1; }
.btn-calendar {
  background: rgba(255,255,255,.2); color: #fff;
  border: 1.5px solid rgba(255,255,255,.4); border-radius: 20px;
  padding: 5px 12px; font-size: 12px; font-weight: 600;
  text-decoration: none; display: flex; align-items: center; gap: 5px;
}
.user-bar {
  background: rgba(255,255,255,.15); border-radius: 10px;
  padding: 8px 12px; margin-top: 12px;
  display: flex; align-items: center; gap: 10px;
}
.user-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(255,255,255,.3); display: flex;
  align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.user-name { font-size: 14px; font-weight: 700; color: #fff; }
.user-type { font-size: 11px; color: rgba(255,255,255,.75); }
.content { padding: 16px 14px; max-width: 480px; margin: 0 auto; }
.section-title {
  font-size: 12px; font-weight: 700; color: #999;
  text-transform: uppercase; letter-spacing: .6px; margin-bottom: 10px;
}
.room-card {
  background: #fff; border-radius: 14px; padding: 14px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 8px;
  display: flex; align-items: center; gap: 14px;
  text-decoration: none; color: inherit;
}
.room-icon {
  width: 42px; height: 42px; border-radius: 10px;
  background: #e8fdf0; display: flex; align-items: center;
  justify-content: center; font-size: 20px; flex-shrink: 0;
}
.room-name { font-size: 15px; font-weight: 700; color: #1a1a1a; }
.room-meta { font-size: 12px; color: #aaa; margin-top: 2px; }
.avail-badge {
  margin-left: auto; padding: 4px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.avail { background: #e8fdf0; color: #059944; }
.busy  { background: #fef2f2; color: #dc2626; }
.my-bookings { margin-top: 14px; }
.booking-item {
  background: #fff; border-radius: 12px; padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 8px;
  display: flex; align-items: center; gap: 12px;
}
.bk-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: #e8f4ff; display: flex; align-items: center;
  justify-content: center; font-size: 18px; flex-shrink: 0;
}
.bk-room { font-size: 13px; font-weight: 700; color: #1a1a1a; }
.bk-time { font-size: 12px; color: #888; margin-top: 2px; }
.bk-status {
  margin-left: auto; padding: 3px 9px; border-radius: 12px;
  font-size: 11px; font-weight: 700;
  background: #dcfce7; color: #15803d; flex-shrink: 0;
}
</style></head><body>
<div class="app-header">
  <div class="header-top">
    <div class="header-brand">
      <div class="org">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</div>
      <div class="name">📚 จองพื้นที่บริการ</div>
    </div>
    <a class="btn-calendar" href="#">📅 ปฏิทิน</a>
  </div>
  <div class="user-bar">
    <div class="user-avatar">ส</div>
    <div>
      <div class="user-name">สมชาย ใจดี</div>
      <div class="user-type">นักศึกษา · คณะวิทยาการจัดการ</div>
    </div>
  </div>
</div>
<div class="content">
  <div class="section-title">เลือกห้องที่ต้องการจอง</div>
  <a class="room-card" href="#">
    <div class="room-icon">🎬</div>
    <div>
      <div class="room-name">Mini Theater</div>
      <div class="room-meta">ชั้น 3 · รองรับ 2–15 คน · สูงสุด 2 ชม.</div>
    </div>
    <span class="avail-badge avail">ว่าง</span>
  </a>
  <a class="room-card" href="#">
    <div class="room-icon">🎮</div>
    <div>
      <div class="room-name">Edutainment Room</div>
      <div class="room-meta">ชั้น 3 · รองรับ 2–10 คน · สูงสุด 2 ชม.</div>
    </div>
    <span class="avail-badge busy">ไม่ว่าง</span>
  </a>
  <a class="room-card" href="#">
    <div class="room-icon">🎨</div>
    <div>
      <div class="room-name">Canva Design Room</div>
      <div class="room-meta">ชั้น 3 · รองรับ 1–4 คน · สูงสุด 2 ชม.</div>
    </div>
    <span class="avail-badge avail">ว่าง</span>
  </a>
  <a class="room-card" href="#">
    <div class="room-icon">🤖</div>
    <div>
      <div class="room-name">ChatGPT Room</div>
      <div class="room-meta">ชั้น 3 · รองรับ 1–4 คน · สูงสุด 2 ชม.</div>
    </div>
    <span class="avail-badge avail">ว่าง</span>
  </a>
  <a class="room-card" href="#">
    <div class="room-icon">🏢</div>
    <div>
      <div class="room-name">ห้องประชุมชั้น 1</div>
      <div class="room-meta">ชั้น 1 · รองรับ 2–20 คน · สูงสุด 2 ชม.</div>
    </div>
    <span class="avail-badge avail">ว่าง</span>
  </a>

  <div class="my-bookings">
    <div class="section-title">การจองของฉัน</div>
    <div class="booking-item">
      <div class="bk-icon">🎬</div>
      <div>
        <div class="bk-room">Mini Theater</div>
        <div class="bk-time">วันพฤหัสบดีที่ 5 มิถุนายน 2568 · 13:00–15:00 น.</div>
      </div>
      <span class="bk-status">ยืนยัน</span>
    </div>
  </div>
</div>
</body></html>"""

def mock_register():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ลงทะเบียน — Library@NPU</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f5f5f5; font-family: 'Sarabun', 'Segoe UI', sans-serif; min-height: 100vh; }
.reg-header {
  background: linear-gradient(135deg,#06C755,#00a844);
  color: #fff; padding: 24px 20px 20px; text-align: center;
}
.reg-header .brand { font-size: 12px; opacity: .8; margin-bottom: 4px; }
.reg-header .title { font-size: 20px; font-weight: 700; }
.reg-header .subtitle { font-size: 13px; opacity: .85; margin-top: 4px; }
.profile-preview {
  display: flex; align-items: center; gap: 12px;
  background: rgba(255,255,255,.15); border-radius: 12px;
  padding: 12px 14px; margin-top: 14px;
}
.profile-pic {
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(255,255,255,.3); display: flex;
  align-items: center; justify-content: center; font-size: 20px; font-weight: 700;
}
.profile-name { font-size: 15px; font-weight: 600; }
.profile-hint { font-size: 12px; opacity: .8; }
.form-card {
  background: #fff; border-radius: 16px;
  margin: 16px; padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
}
.hint-box {
  background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 10px; padding: 10px 14px;
  font-size: 13px; color: #92400e; margin-bottom: 16px;
}
.form-section-title {
  font-size: 12px; color: #aaa; font-weight: 700;
  text-transform: uppercase; letter-spacing: .6px; margin-bottom: 14px;
}
.form-label { font-size: 13px; color: #555; font-weight: 600; display: block; margin-bottom: 5px; }
.form-control {
  width: 100%; font-size: 14px; border-radius: 10px;
  border: 1.5px solid #e0e0e0; padding: 10px 12px; outline: none;
}
.type-options { display: flex; gap: 8px; margin-top: 4px; margin-bottom: 16px; }
.type-opt { flex: 1; }
.type-label {
  display: block; padding: 10px 8px; text-align: center;
  border: 2px solid #e0e0e0; border-radius: 10px;
  font-size: 13px; font-weight: 600; color: #888; cursor: pointer;
}
.type-label.active { border-color: #06C755; background: #f0faf4; color: #059944; }
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.btn-submit {
  width: 100%; padding: 13px; border-radius: 12px;
  background: #06C755; color: #fff; border: none;
  font-size: 16px; font-weight: 700; margin-top: 4px; cursor: pointer;
}
</style></head><body>
<div class="reg-header">
  <div class="brand">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</div>
  <div class="title">ลงทะเบียนใช้งาน</div>
  <div class="subtitle">ผูกบัญชี LINE กับระบบของมหาวิทยาลัย</div>
  <div class="profile-preview">
    <div class="profile-pic">ส</div>
    <div>
      <div class="profile-name">Somchai Jaidee</div>
      <div class="profile-hint">LINE Account ที่ใช้ผูกบัญชี</div>
    </div>
  </div>
</div>
<div class="form-card">
  <div class="form-section-title">ข้อมูลบัญชีมหาวิทยาลัย</div>
  <div class="hint-box">💡 ใช้รหัส LDAP เดียวกับระบบ e-Office / อีเมลมหาวิทยาลัย</div>
  <div class="mb-3">
    <span class="form-label">ประเภทผู้ใช้งาน</span>
    <div class="type-options">
      <div class="type-opt"><div class="type-label">👨‍💼 บุคลากร</div></div>
      <div class="type-opt"><div class="type-label active">🎓 นักศึกษา</div></div>
    </div>
  </div>
  <div class="mb-3">
    <label class="form-label">รหัสผู้ใช้ (LDAP)</label>
    <input class="form-control" placeholder="เช่น 6401234567 หรือ sxxxxxx" value="">
  </div>
  <div class="mb-4">
    <label class="form-label">รหัสผ่าน</label>
    <input class="form-control" type="password" placeholder="รหัสผ่านระบบมหาวิทยาลัย" value="">
  </div>
  <button class="btn-submit">ลงทะเบียนและเข้าใช้งาน</button>
</div>
</body></html>"""

def mock_booking_form():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>จองพื้นที่บริการ</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f5f5f5; font-family: 'Sarabun', 'Segoe UI', sans-serif; }
.room-banner {
  background: linear-gradient(135deg,#06C755,#00a844);
  color: #fff; padding: 16px; border-radius: 12px; margin: 14px 14px 0;
}
.room-banner .banner-name { font-size: 18px; font-weight: 700; }
.room-banner .banner-meta { font-size: 13px; opacity: .85; margin-top: 4px; }
.banner-tags { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.banner-tag {
  background: rgba(255,255,255,.2); border-radius: 20px;
  padding: 3px 10px; font-size: 11px;
}
.user-info-bar {
  background: #fff; border-radius: 10px; padding: 10px 14px;
  margin: 10px 14px; box-shadow: 0 1px 4px rgba(0,0,0,.07);
  display: flex; align-items: center; gap: 10px;
}
.user-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: #06C755; color: #fff; display: flex;
  align-items: center; justify-content: center; font-size: 16px; font-weight: 700;
}
.user-name { font-size: 15px; font-weight: 600; color: #222; }
.user-meta { font-size: 12px; color: #aaa; }
.form-section {
  background: #fff; border-radius: 14px; padding: 16px;
  margin: 8px 14px; box-shadow: 0 1px 4px rgba(0,0,0,.07);
}
.section-label {
  font-size: 11px; font-weight: 700; color: #aaa;
  text-transform: uppercase; letter-spacing: .6px; margin-bottom: 12px;
}
.form-label { font-size: 13px; color: #555; font-weight: 600; display: block; margin-bottom: 5px; }
.form-control {
  width: 100%; font-size: 14px; border-radius: 10px;
  border: 1.5px solid #e0e0e0; padding: 10px 12px;
}
.form-control:focus { border-color: #06C755; outline: none; }
.mb-3 { margin-bottom: 12px; }
.time-row { display: flex; gap: 10px; }
.time-row .mb-3 { flex: 1; }
.slot-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.slot-btn {
  padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600;
  border: 1.5px solid #e0e0e0; background: #fff; color: #555; cursor: pointer;
}
.slot-btn.selected { border-color: #06C755; background: #e8fdf0; color: #059944; }
.slot-btn.disabled { border-color: #f0f0f0; background: #f9f9f9; color: #ccc; cursor: default; }
.btn-submit {
  width: calc(100% - 28px); margin: 12px 14px 20px; padding: 13px;
  border-radius: 12px; background: #06C755; color: #fff; border: none;
  font-size: 16px; font-weight: 700; cursor: pointer;
}
</style></head><body>
<div class="room-banner">
  <div class="banner-name">🎬 Mini Theater</div>
  <div class="banner-meta">📍 ชั้น 3 อาคารสำนักวิทยบริการ</div>
  <div class="banner-tags">
    <span class="banner-tag">👥 2–15 คน</span>
    <span class="banner-tag">⏱ สูงสุด 2 ชม.</span>
    <span class="banner-tag">🕐 08:30–16:30 น.</span>
  </div>
</div>
<div class="user-info-bar">
  <div class="user-avatar">ส</div>
  <div>
    <div class="user-name">สมชาย ใจดี</div>
    <div class="user-meta">นักศึกษา · คณะวิทยาการจัดการ</div>
  </div>
</div>
<div class="form-section">
  <div class="section-label">ข้อมูลการจอง</div>
  <div class="mb-3">
    <label class="form-label">ชื่อกลุ่ม / ชื่อกิจกรรม</label>
    <input class="form-control" placeholder="เช่น ทีมโปรเจกต์ IS301" value="">
  </div>
  <div class="mb-3">
    <label class="form-label">วันที่จอง</label>
    <input class="form-control" value="วันพฤหัสบดีที่ 5 มิถุนายน 2568" readonly>
  </div>
  <div class="mb-3">
    <label class="form-label">เวลาเริ่มต้น</label>
    <div class="slot-grid">
      <button class="slot-btn">08:30</button>
      <button class="slot-btn">09:00</button>
      <button class="slot-btn">09:30</button>
      <button class="slot-btn selected">10:00</button>
      <button class="slot-btn">10:30</button>
      <button class="slot-btn">11:00</button>
      <button class="slot-btn disabled">11:30</button>
      <button class="slot-btn disabled">13:00</button>
      <button class="slot-btn">14:00</button>
    </div>
  </div>
  <div class="mb-3">
    <label class="form-label">ระยะเวลา</label>
    <select class="form-control">
      <option>30 นาที</option>
      <option selected>1 ชั่วโมง</option>
      <option>1 ชั่วโมง 30 นาที</option>
      <option>2 ชั่วโมง</option>
    </select>
  </div>
  <div class="mb-3">
    <label class="form-label">จำนวนผู้เข้าใช้งาน</label>
    <input class="form-control" value="5" type="number">
  </div>
</div>
<button class="btn-submit">ยืนยันการจอง</button>
</body></html>"""

def mock_booking_success():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>จองสำเร็จ</title>
<style>
* { box-sizing: border-box; }
body { background: #f5f5f5; font-family: 'Sarabun', 'Segoe UI', sans-serif; }
.container { max-width: 480px; margin: 0 auto; padding: 32px 16px; }
.success-icon { font-size: 64px; text-align: center; }
h4 { text-align: center; font-size: 22px; font-weight: 700; margin-top: 10px; }
.sub { text-align: center; color: #888; font-size: 14px; margin-bottom: 24px; }
.card-info {
  background: #fff; border-radius: 12px; padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}
.info-row {
  display: flex; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid #f0f0f0;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: #888; font-size: 13px; }
.info-value { font-size: 14px; font-weight: 600; color: #333; text-align: right; max-width: 60%; }
.btn-home {
  display: block; width: 100%; margin-top: 20px; padding: 13px;
  border-radius: 12px; background: #06C755; color: #fff; border: none;
  font-size: 16px; font-weight: 700; text-align: center; text-decoration: none;
}
</style></head><body>
<div class="container">
  <div class="success-icon">✅</div>
  <h4>จองสำเร็จแล้ว!</h4>
  <p class="sub">ระบบได้รับการจองของคุณเรียบร้อยแล้ว</p>
  <div class="card-info">
    <div class="info-row">
      <span class="info-label">เลขที่การจอง</span>
      <span class="info-value">#1042</span>
    </div>
    <div class="info-row">
      <span class="info-label">ห้อง</span>
      <span class="info-value">Mini Theater</span>
    </div>
    <div class="info-row">
      <span class="info-label">สถานที่</span>
      <span class="info-value">ชั้น 3 อาคารสำนักวิทยบริการ</span>
    </div>
    <div class="info-row">
      <span class="info-label">วันที่</span>
      <span class="info-value">วันพฤหัสบดีที่ 5 มิถุนายน 2568</span>
    </div>
    <div class="info-row">
      <span class="info-label">เวลา</span>
      <span class="info-value">10:00 – 11:00 น.</span>
    </div>
    <div class="info-row">
      <span class="info-label">ชื่อกลุ่ม</span>
      <span class="info-value">ทีมโปรเจกต์ IS301</span>
    </div>
    <div class="info-row">
      <span class="info-label">ผู้จอง</span>
      <span class="info-value">สมชาย ใจดี</span>
    </div>
  </div>
  <a href="#" class="btn-home">← กลับหน้าหลัก</a>
</div>
</body></html>"""

def mock_cancel():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ยืนยันยกเลิก</title>
<style>
* { box-sizing: border-box; }
body { background: rgba(0,0,0,.5); font-family: 'Sarabun','Segoe UI',sans-serif; min-height: 100vh;
       display: flex; align-items: center; justify-content: center; }
.modal {
  background: #fff; border-radius: 20px; padding: 28px 24px;
  max-width: 360px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,.3);
  text-align: center;
}
.modal-icon { font-size: 48px; margin-bottom: 12px; }
.modal-title { font-size: 18px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.modal-sub { font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px; }
.info-box {
  background: #f9fafb; border-radius: 10px; padding: 12px 14px;
  margin-bottom: 20px; text-align: left;
}
.info-row { display: flex; justify-content: space-between; font-size: 13px;
             padding: 5px 0; border-bottom: 1px solid #f0f0f0; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #888; }
.info-value { font-weight: 600; color: #333; text-align: right; }
.btn-row { display: flex; gap: 10px; }
.btn { flex: 1; padding: 12px; border-radius: 12px; font-size: 14px; font-weight: 700;
       border: none; cursor: pointer; }
.btn-cancel-confirm { background: #ef4444; color: #fff; }
.btn-back { background: #f3f4f6; color: #555; }
</style></head><body>
<div class="modal">
  <div class="modal-icon">⚠️</div>
  <div class="modal-title">ยืนยันการยกเลิกการจอง</div>
  <div class="modal-sub">การดำเนินการนี้ไม่สามารถย้อนกลับได้<br>คุณแน่ใจหรือไม่?</div>
  <div class="info-box">
    <div class="info-row">
      <span class="info-label">ห้อง</span>
      <span class="info-value">Mini Theater</span>
    </div>
    <div class="info-row">
      <span class="info-label">วันที่</span>
      <span class="info-value">5 มิ.ย. 68</span>
    </div>
    <div class="info-row">
      <span class="info-label">เวลา</span>
      <span class="info-value">10:00 – 11:00 น.</span>
    </div>
  </div>
  <div class="btn-row">
    <button class="btn btn-back">ไม่ยกเลิก</button>
    <button class="btn btn-cancel-confirm">ยืนยันยกเลิก</button>
  </div>
</div>
</body></html>"""

def mock_checkin():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>เช็คอิน</title>
<style>
* { box-sizing: border-box; }
body { background: #f0f2f5; font-family: 'Sarabun','Segoe UI',sans-serif; }
.app-header {
  background: linear-gradient(135deg,#06C755 0%,#00a844 100%);
  padding: 16px 20px; box-shadow: 0 2px 8px rgba(6,199,85,.3);
}
.header-brand .org  { font-size: 11px; color: rgba(255,255,255,.8); }
.header-brand .name { font-size: 18px; font-weight: 700; color: #fff; }
.content { padding: 16px 14px; max-width: 480px; margin: 0 auto; }
.booking-card {
  background: #fff; border-radius: 16px; padding: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08); margin-bottom: 14px;
}
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.card-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: #e8fdf0; display: flex; align-items: center;
  justify-content: center; font-size: 24px;
}
.card-title { font-size: 17px; font-weight: 700; color: #1a1a1a; }
.card-time { font-size: 13px; color: #888; }
.info-row { display: flex; justify-content: space-between; padding: 8px 0;
             border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #888; }
.info-value { font-weight: 600; color: #333; }
.checkin-section { margin-top: 14px; }
.time-window {
  background: #eff6ff; border-radius: 10px; padding: 10px 14px;
  font-size: 13px; color: #1d4ed8; margin-bottom: 12px;
  display: flex; align-items: center; gap: 8px;
}
.btn-checkin {
  width: 100%; padding: 14px; border-radius: 12px;
  background: #06C755; color: #fff; border: none;
  font-size: 16px; font-weight: 700; cursor: pointer;
}
</style></head><body>
<div class="app-header">
  <div class="header-brand">
    <div class="org">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</div>
    <div class="name">📚 จองพื้นที่บริการ</div>
  </div>
</div>
<div class="content">
  <div class="booking-card">
    <div class="card-header">
      <div class="card-icon">🎬</div>
      <div>
        <div class="card-title">Mini Theater</div>
        <div class="card-time">วันพฤหัสบดีที่ 5 มิถุนายน 2568</div>
      </div>
    </div>
    <div class="info-row">
      <span class="info-label">เวลา</span>
      <span class="info-value">10:00 – 11:00 น.</span>
    </div>
    <div class="info-row">
      <span class="info-label">ผู้จอง</span>
      <span class="info-value">สมชาย ใจดี</span>
    </div>
    <div class="info-row">
      <span class="info-label">จำนวนผู้เข้าใช้</span>
      <span class="info-value">5 คน</span>
    </div>
    <div class="checkin-section">
      <div class="time-window">
        ⏰ เช็คอินได้ตั้งแต่ 09:45 น. ถึง 10:15 น.
      </div>
      <button class="btn-checkin">✅ เช็คอิน</button>
    </div>
  </div>
</div>
</body></html>"""

def mock_virtual_card():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>บัตรสมาชิกดิจิทัล</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Sarabun','Segoe UI',sans-serif;
  background: linear-gradient(145deg,#1a4080 0%,#243d6e 60%,#162d5a 100%);
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 16px 10px;
}
.card-wrap {
  background: linear-gradient(135deg,#253d6e 0%,#1a3060 100%);
  border-radius: 20px; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
  width: 100%; max-width: 380px;
}
.card-header-stripe {
  background: linear-gradient(90deg,#229799 0%,#1a7a7c 100%);
  padding: 14px 20px; display: flex; align-items: center; gap: 10px;
}
.card-header-logo { font-size: 20px; }
.card-header-title { color: #fff; font-size: 13px; font-weight: 600; }
.card-header-sub { color: rgba(255,255,255,.8); font-size: 11px; }
.card-profile { display: flex; align-items: center; gap: 14px; padding: 20px 20px 16px; }
.profile-avatar {
  width: 72px; height: 72px; border-radius: 50%;
  border: 3px solid rgba(34,151,153,.6);
  background: linear-gradient(135deg,#3a5080,#2a4070);
  display: flex; align-items: center; justify-content: center;
  font-size: 28px;
}
.profile-name { color: #fff; font-size: 17px; font-weight: 700; }
.profile-type {
  display: inline-block; margin-top: 5px;
  background: rgba(34,151,153,.25); border: 1px solid rgba(34,151,153,.5);
  color: #7ee8ea; font-size: 11px; padding: 2px 10px; border-radius: 12px;
}
.profile-org { margin-top: 5px; color: rgba(220,235,255,.88); font-size: 12px; }
.card-divider {
  height: 1px;
  background: linear-gradient(90deg,transparent,rgba(255,255,255,.1),transparent);
  margin: 0 20px;
}
.walai-status { padding: 14px 20px; display: flex; align-items: center; gap: 10px; }
.walai-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  font-size: 13px; font-weight: 600;
  background: rgba(34,197,94,.15); border: 1px solid rgba(34,197,94,.4); color: #4ade80;
}
.walai-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #4ade80;
}
.qr-section { padding: 14px 20px 20px; text-align: center; }
.qr-label { font-size: 11px; color: rgba(255,255,255,.5); margin-bottom: 10px; }
.qr-box {
  width: 140px; height: 140px; background: #fff; border-radius: 12px;
  margin: 0 auto; display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #555;
}
.id-row { margin-top: 10px; }
.id-label { font-size: 11px; color: rgba(255,255,255,.5); }
.id-value { font-size: 13px; font-weight: 700; color: rgba(255,255,255,.85); letter-spacing: 1px; }
</style></head><body>
<div class="card-wrap">
  <div class="card-header-stripe">
    <div class="card-header-logo">📚</div>
    <div>
      <div class="card-header-title">บัตรสมาชิกห้องสมุด</div>
      <div class="card-header-sub">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</div>
    </div>
  </div>
  <div class="card-profile">
    <div class="profile-avatar">👨‍🎓</div>
    <div>
      <div class="profile-name">สมชาย ใจดี</div>
      <div><span class="profile-type">นักศึกษา</span></div>
      <div class="profile-org">คณะวิทยาการจัดการ<br>มหาวิทยาลัยนครพนม</div>
    </div>
  </div>
  <div class="card-divider"></div>
  <div class="walai-status">
    <div class="walai-badge">
      <span class="walai-dot"></span>
      สมาชิก Walai@NPU
    </div>
    <span style="font-size:12px;color:rgba(255,255,255,.5);margin-left:8px;">ยืมได้สูงสุด 5 เล่ม</span>
  </div>
  <div class="card-divider"></div>
  <div class="qr-section">
    <div class="qr-label">สแกนเพื่อยืนยันตัวตน</div>
    <div class="qr-box">[ QR Code ]</div>
    <div class="id-row">
      <div class="id-label">รหัสนักศึกษา</div>
      <div class="id-value">6401234567</div>
    </div>
  </div>
</div>
</body></html>"""

def mock_room_control():
    return """<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ควบคุมอุปกรณ์</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f0f2f5; font-family: 'Sarabun','Segoe UI',sans-serif; }
.ctrl-header {
  background: linear-gradient(135deg,#1a1f2e 0%,#2a3148 100%);
  padding: 20px 20px 16px;
}
.back-btn { color: rgba(255,255,255,.6); font-size: 13px; text-decoration: none;
             display: inline-flex; align-items: center; gap: 4px; margin-bottom: 12px; }
.room-title { font-size: 22px; font-weight: 700; color: #fff; }
.room-meta { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.time-badge {
  background: rgba(255,255,255,.12); border-radius: 20px;
  padding: 4px 12px; font-size: 12px; font-weight: 600; color: rgba(255,255,255,.85);
}
.ctrl-body { padding: 20px 16px; max-width: 480px; }
.section-label {
  font-size: 11px; font-weight: 700; color: #aaa;
  text-transform: uppercase; letter-spacing: .8px; margin-bottom: 10px;
}
.device-card {
  background: #fff; border-radius: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.07);
  padding: 18px 20px; display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 10px; gap: 16px;
}
.device-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: #dcfce7; display: flex; align-items: center;
  justify-content: center; font-size: 20px;
}
.device-icon.off-icon { background: #f3f4f6; }
.dev-name { font-size: 15px; font-weight: 700; color: #1a1a1a; }
.dev-status { font-size: 12px; color: #aaa; margin-top: 3px; display: flex; align-items: center; gap: 4px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; }
.status-dot.off { background: #9ca3af; }
.toggle-btn {
  position: relative; width: 52px; height: 30px;
  background: #06C755; border-radius: 15px; border: none; cursor: pointer;
}
.toggle-btn::after {
  content: ''; position: absolute; top: 3px; right: 3px;
  width: 24px; height: 24px; border-radius: 50%; background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
}
.toggle-btn.off { background: #d1d5db; }
.toggle-btn.off::after { left: 3px; right: auto; }
</style></head><body>
<div class="ctrl-header">
  <a class="back-btn" href="#">← กลับหน้าหลัก</a>
  <div class="room-title">🎬 Mini Theater</div>
  <div class="room-meta">
    <span class="time-badge">⏰ สิ้นสุด 11:00 น.</span>
  </div>
</div>
<div class="ctrl-body">
  <div class="section-label">อุปกรณ์ในห้อง</div>
  <div class="device-card">
    <div class="device-icon">💡</div>
    <div style="flex:1">
      <div class="dev-name">ไฟห้อง</div>
      <div class="dev-status"><span class="status-dot"></span>เปิดอยู่</div>
    </div>
    <button class="toggle-btn"></button>
  </div>
  <div class="device-card">
    <div class="device-icon">❄️</div>
    <div style="flex:1">
      <div class="dev-name">แอร์</div>
      <div class="dev-status"><span class="status-dot"></span>เปิดอยู่</div>
    </div>
    <button class="toggle-btn"></button>
  </div>
  <div class="device-card">
    <div class="device-icon off-icon">🖥️</div>
    <div style="flex:1">
      <div class="dev-name">โปรเจกเตอร์</div>
      <div class="dev-status"><span class="status-dot off"></span>ปิดอยู่</div>
    </div>
    <button class="toggle-btn off"></button>
  </div>
</div>
</body></html>"""

# ─── Main ─────────────────────────────────────────────────────────────────────

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    def shot_html(html: str, filename: str):
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{OUT_DIR}/{filename}", full_page=True)
        ctx.close()
        print(f"✓ {filename}")

    def shot_url(url: str, filename: str, wait_extra: int = 0):
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle", timeout=15000)
        if wait_extra:
            page.wait_for_timeout(wait_extra)
        page.screenshot(path=f"{OUT_DIR}/{filename}", full_page=True)
        ctx.close()
        print(f"✓ {filename}")

    # ── Mockup screenshots (mobile, 390×844) ──────────────────────────────────
    shot_html(mock_landing(),        "user_01_landing.png")
    shot_html(mock_register(),       "user_02_register.png")
    shot_html(mock_booking_form(),   "user_03_booking_form.png")
    shot_html(mock_booking_success(), "user_04_success.png")
    shot_html(mock_cancel(),         "user_05_cancel.png")
    shot_html(mock_checkin(),        "user_06_checkin.png")
    shot_html(mock_virtual_card(),   "user_07_virtual_card.png")
    shot_html(mock_room_control(),   "user_08_room_control.png")

    # ── Real screenshots (desktop) ────────────────────────────────────────────
    shot_url(f"{BASE_URL}/calendar/", "user_09_calendar.png", wait_extra=2000)
    shot_url(f"{BASE_URL}/room/mini/", "user_10_room_detail_mini.png")
    shot_url(f"{BASE_URL}/room/edutainment/", "user_11_room_detail_edutainment.png")
    shot_url(f"{BASE_URL}/room/canva/", "user_12_room_detail_canva.png")

    browser.close()

print("\nAll user screenshots captured!")
