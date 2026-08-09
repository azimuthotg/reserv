"""แปลงรูปต้นฉบับให้เป็นรูปห้องตามสเปกของระบบ

    python doc/prep_room_image.py "img/chatgpt.png" chat-gpt [--width 1440]

สเปกรูปห้อง (ดู MEM.md 2026-08-09):
- **16:9 เป๊ะ** — กล่องรูปทั้งหน้าแรกและหน้ารายละเอียดเป็น `aspect-ratio: 16/9`
  ถ้าไฟล์ไม่ใช่ 16:9 จะถูก crop ทิ้ง สคริปต์นี้จึง crop กึ่งกลางให้ก่อนย่อ ไม่ resize ทื่อ ๆ
- **PNG quantize 256 สี** — ภาพจาก AI แบบเต็มสีหนัก ~2 MB ต่อใบ หน้าแรกโหลดพร้อมกัน 6 ใบ
  256 สีเหลือ ~0.6–0.8 MB และตรวจแล้วไม่เห็น banding ทั้งพื้นสว่างและพื้นเข้ม
- **ความกว้าง** ปกติ 1920 · ภาพพื้นเข้มที่มี noise/particle เยอะจะบีบไม่ลง ใช้ 1440 แทนได้
  (จอแสดงจริงกว้างสุด 560 CSS px — 1440 ยังเผื่อ retina 2.5 เท่า)
- ชื่อไฟล์ปลายทางต้องเท่ากับ `Room.booking_name` เป๊ะ ไม่งั้นหน้าเว็บขึ้นไอคอน 🏢
- ไฟล์อยู่ใน .gitignore (`*.png`) → commit ต้องใช้ `git add -f`
"""
import argparse
import os

from PIL import Image

DST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "booking", "static", "booking", "images", "rooms")
TARGET_AR = 16 / 9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="ไฟล์ต้นฉบับ")
    ap.add_argument("booking_name", help="booking_name ของห้อง (ใช้เป็นชื่อไฟล์)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--colors", type=int, default=256)
    args = ap.parse_args()

    dst = os.path.join(DST_DIR, f"{args.booking_name}.png")
    im = Image.open(args.src)
    w, h = im.size

    if w / h > TARGET_AR:                       # กว้างเกิน -> ตัดซ้าย-ขวา
        new_w = round(h * TARGET_AR)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:                                       # สูงเกิน -> ตัดบน-ล่าง
        new_h = round(w / TARGET_AR)
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)

    out_size = (args.width, round(args.width / TARGET_AR))
    im = im.crop(box).resize(out_size, Image.LANCZOS).convert("RGB")
    im.quantize(colors=args.colors, dither=Image.FLOYDSTEINBERG).save(dst, "PNG", optimize=True)

    print(f"{os.path.basename(args.src)}  {w}x{h}"
          f"  ->  crop {box[2]-box[0]}x{box[3]-box[1]}"
          f"  ->  {out_size[0]}x{out_size[1]}  {args.colors} สี")
    print(f"บันทึก: {dst}  ({round(os.path.getsize(dst)/1024)} KB)")
    print("อย่าลืม: git add -f " + os.path.relpath(dst, os.path.dirname(DST_DIR)))


if __name__ == "__main__":
    main()
