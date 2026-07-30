"""รวมภาพหน้าจอมือถือ (9:16) เป็นภาพประกอบกรอบ 16:9 สำหรับคู่มือผู้ใช้

จอมือถือเป็นแนวตั้ง วางเดี่ยว ๆ ในกรอบ 16:9 จะเหลือขอบว่างมาก
สคริปต์นี้จึงเรียงได้สูงสุด 3 จอในกรอบเดียว พร้อมเลขลำดับขั้นกำกับ
ผลลัพธ์เก็บที่ doc/screenshots/manual2026/composed/
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "screenshots", "manual2026")
OUT  = os.path.join(SRC, "composed")

W, H = 1920, 1080
BG   = (244, 245, 247)
PAD  = 60
GAP  = 50

FONT_CANDIDATES = [
    "/mnt/c/Windows/Fonts/LeelaUIb.ttf",
    "/mnt/c/Windows/Fonts/LeelawUI.ttf",
    "/mnt/c/Windows/Fonts/tahomabd.ttf",
    "/usr/share/fonts/opentype/tlwg/Loma-Bold.otf",
]


def font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def compose(names, out_name, labels=None):
    imgs = []
    for n in names:
        p = os.path.join(SRC, n + ".png")
        if os.path.exists(p):
            imgs.append(Image.open(p).convert("RGB"))
        else:
            print(f"  ! ไม่พบ {n}.png — ข้าม")
    if not imgs:
        print(f"  ! ข้าม {out_name} (ไม่มีภาพต้นทางเลย)")
        return False

    count   = len(imgs)
    label_h = 70 if labels else 0
    avail_h = H - PAD * 2 - label_h
    max_w   = (W - PAD * 2 - GAP * (count - 1)) // count

    scaled = []
    for im in imgs:
        r = min(avail_h / im.height, max_w / im.width)
        scaled.append(im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS))

    total_w = sum(s.width for s in scaled) + GAP * (count - 1)
    canvas  = Image.new("RGB", (W, H), BG)
    dr      = ImageDraw.Draw(canvas)

    x = (W - total_w) // 2
    for i, s in enumerate(scaled):
        y = PAD + label_h + (avail_h - s.height) // 2
        dr.rectangle([x - 3, y - 3, x + s.width + 2, y + s.height + 2], fill=(214, 216, 220))
        canvas.paste(s, (x, y))
        if labels and i < len(labels):
            ty, r_ = PAD + 8, 22
            dr.ellipse([x, ty, x + r_ * 2, ty + r_ * 2], fill=(28, 28, 30))
            dr.text((x + r_, ty + r_), str(i + 1), font=font(26), fill=(255, 255, 255), anchor="mm")
            dr.text((x + r_ * 2 + 14, ty + r_), labels[i], font=font(30), fill=(28, 28, 30), anchor="lm")
        x += s.width + GAP

    os.makedirs(OUT, exist_ok=True)
    canvas.save(os.path.join(OUT, out_name + ".png"))
    print(f"  OK {out_name} ({count} จอ)")
    return True


SPEC = [
    (["mob_register", "mob_register_filled"], "fig_u02_register",
     ["หน้าลงทะเบียน", "เลือกประเภทผู้ใช้"]),

    (["mob_01_landing", "mob_02_room_list", "mob_03_my_bookings"], "fig_u03_landing",
     ["หน้าหลัก", "รายการห้อง", "การจองของฉัน"]),

    (["mob_room_mini", "mob_room_edu"], "fig_u04_room_detail",
     ["Mini Theater", "Edutainment Zone"]),

    (["mob_05_booking_empty", "mob_06_datepicker", "mob_07_date_selected"], "fig_u05_booking_date",
     ["เปิดฟอร์มจอง", "เลือกวันที่", "ดูช่วงที่ถูกจองแล้ว"]),

    (["mob_08_quick_morning", "mob_09_form_filled"], "fig_u06_booking_time",
     ["เลือกช่วงเวลา", "กรอกรายละเอียด"]),

    (["mob_12_success", "mob_04_booking_detail_sheet"], "fig_u07_success",
     ["จองสำเร็จ", "รายละเอียดการจอง"]),

    (["mob_13_checkin_button", "mob_14_active_card"], "fig_u13_checkin",
     ["ปุ่ม Check-in ก่อนเริ่ม 15 นาที", "ระหว่างใช้ห้อง"]),

    (["mob_03_my_bookings"], "fig_u14_cancel", None),

    (["mob_11_room_control"], "fig_u08_room_control", None),
    (["mob_10_card"],         "fig_u09_card",         None),
    (["mob_card_login"],      "fig_u10_card_login",   None),

    (["mob_external", "mob_external_perm"], "fig_u11_external",
     ["ขอรหัสรายวัน", "สมาชิกถาวร"]),

    (["mob_calendar"], "fig_u12_calendar", None),
]


if __name__ == "__main__":
    print("สร้างภาพประกอบ 16:9 จากภาพหน้าจอมือถือ")
    for names, out_name, labels in SPEC:
        compose(names, out_name, labels)
