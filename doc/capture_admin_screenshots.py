"""Capture real screenshots from the live Staff Portal for admin manual."""
from playwright.sync_api import sync_playwright
import os

BASE_URL = "https://lib.npu.ac.th/reserv"
USERNAME = "admin_e"
PASSWORD = "41132834"
OUT_DIR  = "/mnt/c/projects/reserv/doc/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

def wait(page):
    page.wait_for_load_state("networkidle", timeout=15000)

def login(page):
    page.goto(f"{BASE_URL}/manage/login/")
    wait(page)
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    wait(page)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()

    # 01 Login page
    page.goto(f"{BASE_URL}/manage/login/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_01_login.png", full_page=True)
    print("✓ real_01_login.png")

    # Login
    login(page)
    print("  → logged in, current URL:", page.url)

    # 02 Dashboard
    page.goto(f"{BASE_URL}/manage/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_02_dashboard.png", full_page=True)
    print("✓ real_02_dashboard.png")

    # 03 Daily Schedule
    page.goto(f"{BASE_URL}/manage/daily/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_03_daily.png", full_page=True)
    print("✓ real_03_daily.png")

    # 04 Bookings list
    page.goto(f"{BASE_URL}/manage/bookings/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_04_bookings.png", full_page=True)
    print("✓ real_04_bookings.png")

    # 05 Bookings — cancel modal (hover/click first cancel button if exists)
    page.goto(f"{BASE_URL}/manage/bookings/?status=confirmed")
    wait(page)
    cancel_btn = page.query_selector('button.btn-outline-danger')
    if cancel_btn:
        cancel_btn.click()
        page.wait_for_timeout(600)
        page.screenshot(path=f"{OUT_DIR}/real_05_cancel_modal.png", full_page=True)
        print("✓ real_05_cancel_modal.png")
        # Close modal / press Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    else:
        print("  (ไม่มีการจองที่ยังยืนยันอยู่ — ข้าม cancel modal)")

    # 06 Booking logs (first booking if any)
    page.goto(f"{BASE_URL}/manage/bookings/")
    wait(page)
    logs_link = page.query_selector('a[href*="/logs/"]')
    if logs_link:
        logs_link.click()
        wait(page)
        page.screenshot(path=f"{OUT_DIR}/real_06_booking_logs.png", full_page=True)
        print("✓ real_06_booking_logs.png")
    else:
        print("  (ไม่พบ booking logs link — ข้าม)")

    # 07 Holidays
    page.goto(f"{BASE_URL}/manage/holidays/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_07_holidays.png", full_page=True)
    print("✓ real_07_holidays.png")

    # 08 Add holiday form
    page.goto(f"{BASE_URL}/manage/holidays/add/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_08_holiday_form.png", full_page=True)
    print("✓ real_08_holiday_form.png")

    # 09 Room Closures
    page.goto(f"{BASE_URL}/manage/closures/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_09_closures.png", full_page=True)
    print("✓ real_09_closures.png")

    # 10 Add closure form
    page.goto(f"{BASE_URL}/manage/closures/add/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_10_closure_form.png", full_page=True)
    print("✓ real_10_closure_form.png")

    # 11 LINE Users
    page.goto(f"{BASE_URL}/manage/line-users/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_11_line_users.png", full_page=True)
    print("✓ real_11_line_users.png")

    # 12 LINE User detail (first user if any)
    page.goto(f"{BASE_URL}/manage/line-users/")
    wait(page)
    detail_link = page.query_selector('a[href*="/manage/line-users/"][href$="/"]')
    if detail_link:
        href = detail_link.get_attribute("href")
        if href and "/manage/line-users/" in href and href != f"/reserv/manage/line-users/":
            detail_link.click()
            wait(page)
            page.screenshot(path=f"{OUT_DIR}/real_12_user_detail.png", full_page=True)
            print("✓ real_12_user_detail.png")
        else:
            print("  (ไม่พบ user detail link — ข้าม)")
    else:
        print("  (ไม่พบ user detail link — ข้าม)")

    # 13 Rooms (admin only)
    page.goto(f"{BASE_URL}/manage/rooms/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_13_rooms.png", full_page=True)
    print("✓ real_13_rooms.png")

    # 14 Room edit form (first room)
    edit_link = page.query_selector('a[href*="/manage/rooms/"][href*="/edit/"]')
    if edit_link:
        edit_link.click()
        wait(page)
        page.screenshot(path=f"{OUT_DIR}/real_14_room_form.png", full_page=True)
        print("✓ real_14_room_form.png")
        page.goto(f"{BASE_URL}/manage/rooms/")
        wait(page)
    else:
        page.goto(f"{BASE_URL}/manage/rooms/add/")
        wait(page)
        page.screenshot(path=f"{OUT_DIR}/real_14_room_form.png", full_page=True)
        print("✓ real_14_room_form.png (add form)")

    # 15 Room devices (first room)
    page.goto(f"{BASE_URL}/manage/rooms/")
    wait(page)
    devices_link = page.query_selector('a[href*="/devices/"]')
    if devices_link:
        devices_link.click()
        wait(page)
        page.screenshot(path=f"{OUT_DIR}/real_15_room_devices.png", full_page=True)
        print("✓ real_15_room_devices.png")
    else:
        print("  (ไม่พบ devices link — ข้าม)")

    # 16 IoT Monitor
    page.goto(f"{BASE_URL}/manage/iot-monitor/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_16_iot_monitor.png", full_page=True)
    print("✓ real_16_iot_monitor.png")

    # 17 Staff list
    page.goto(f"{BASE_URL}/manage/staff/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_17_staff.png", full_page=True)
    print("✓ real_17_staff.png")

    # 18 Add staff form
    page.goto(f"{BASE_URL}/manage/staff/add/")
    wait(page)
    page.screenshot(path=f"{OUT_DIR}/real_18_staff_form.png", full_page=True)
    print("✓ real_18_staff_form.png")

    # 19 Calendar
    page.goto(f"{BASE_URL}/manage/calendar/")
    wait(page)
    page.wait_for_timeout(2000)  # FullCalendar needs extra time
    page.screenshot(path=f"{OUT_DIR}/real_19_calendar.png", full_page=True)
    print("✓ real_19_calendar.png")

    browser.close()

print("\nAll real screenshots captured!")
