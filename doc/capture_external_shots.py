"""แคปหน้าจอระบบบุคคลภายนอกจาก production สำหรับคู่มือ external-access-manual

ภาพทั้งหมดเป็น 1920x1080 (16:9) เก็บที่ doc/screenshots/manual2026/
ให้ตรงกับภาพชุดเดิมที่คู่มือ 2569 ใช้อยู่

ต้องมีบัญชีเจ้าหน้าที่ของ Staff Portal — อ่านจาก environment variable:

    STAFF_USER=<ชื่อผู้ใช้> STAFF_PASS=<รหัสผ่าน> python3 doc/capture_external_shots.py

โดยปกติจะแคปเฉพาะภาพที่คู่มือยังขาด (หน้าแก้ไขข้อมูลสมาชิก) เพื่อไม่ให้ทับภาพเดิม
ใส่ --all เมื่อต้องการแคปใหม่ทั้งชุด

สคริปต์นี้เปิดเฉพาะหน้าจอแบบอ่านอย่างเดียว ไม่กดบันทึก ไม่แก้ข้อมูลใด ๆ บน production
"""
import os
import sys

from playwright.sync_api import sync_playwright

BASE  = "https://lib.npu.ac.th/reserv"
HERE  = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots", "manual2026")

VIEWPORT = {"width": 1920, "height": 1080}


def shot(page, name):
    path = os.path.join(SHOTS, f"{name}.png")
    page.wait_for_timeout(700)
    page.screenshot(path=path)          # ไม่ใช้ full_page เพื่อคุมอัตราส่วน 16:9
    print("  บันทึกแล้ว:", os.path.relpath(path, HERE))


def main():
    capture_all = "--all" in sys.argv
    user = os.getenv("STAFF_USER")
    pwd  = os.getenv("STAFF_PASS")
    if not (user and pwd):
        sys.exit("ต้องตั้ง STAFF_USER และ STAFF_PASS ก่อนรัน (ดูคำอธิบายหัวไฟล์)")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_context(viewport=VIEWPORT).new_page()

        if capture_all:
            print("หน้าสาธารณะ")
            page.goto(f"{BASE}/external/", wait_until="networkidle")
            shot(page, "web_external")
            page.goto(f"{BASE}/external/permanent/", wait_until="networkidle")
            shot(page, "web_external_perm")

        print("เข้าสู่ระบบ Staff Portal")
        page.goto(f"{BASE}/manage/login/", wait_until="networkidle")
        page.fill('input[name="username"]', user)
        page.fill('input[name="password"]', pwd)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        if "/manage/login" in page.url:
            sys.exit("เข้าสู่ระบบไม่สำเร็จ — ตรวจ STAFF_USER / STAFF_PASS")

        page.goto(f"{BASE}/manage/external/", wait_until="networkidle")
        if capture_all:
            shot(page, "staff_13_external_list")

        # หา citizen_id ของสมาชิกรายแรกจากลิงก์ในตาราง เพื่อเปิดหน้ารายละเอียด/แก้ไข
        href = page.eval_on_selector(
            'a[href*="/manage/external/"]:not([href$="/register/"])',
            "el => el.getAttribute('href')",
        )
        member_id = href.rstrip("/").split("/")[-1]
        print("  ใช้สมาชิกรายแรก:", member_id)

        if capture_all:
            page.goto(f"{BASE}/manage/external/{member_id}/", wait_until="networkidle")
            shot(page, "staff_13b_external_detail")
            page.goto(f"{BASE}/manage/external/register/", wait_until="networkidle")
            shot(page, "staff_14_external_register")

        print("หน้าแก้ไขข้อมูลสมาชิก")
        page.goto(f"{BASE}/manage/external/{member_id}/edit/", wait_until="networkidle")
        shot(page, "staff_13c_external_edit")

        browser.close()
    print("เสร็จแล้ว — รัน python3 doc/make_external_manual_docx.py เพื่อสร้างคู่มือใหม่")


if __name__ == "__main__":
    main()
