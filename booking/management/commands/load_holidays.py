"""
python manage.py load_holidays
โหลดวันหยุดจาก Google Sheet ที่ได้ กรอกล่วงหน้า
"""
from datetime import date

from django.core.management.base import BaseCommand

from booking.models import HolidayDate

HOLIDAYS = [
    # วันหยุดราชการ 2026 (พ.ศ. 2569)
    (date(2026,  1,  1), 'วันขึ้นปีใหม่'),
    (date(2026,  1,  2), 'วันหยุดทำการเพิ่มเป็นกรณีพิเศษ'),
    (date(2026,  3,  3), 'วันมาฆบูชา'),
    (date(2026,  4,  6), 'วันจักรี'),
    (date(2026,  4, 13), 'วันสงกรานต์'),
    (date(2026,  4, 14), 'วันสงกรานต์'),
    (date(2026,  4, 15), 'วันสงกรานต์'),
    (date(2026,  5,  1), 'วันแรงงานแห่งชาติ'),
    (date(2026,  5,  4), 'วันฉัตรมงคล'),
    (date(2026,  5, 31), 'วันวิสาขบูชา'),
    (date(2026,  6,  1), 'วันหยุดชดเชยวันวิสาขบูชา'),
    (date(2026,  6,  3), 'วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าฯ พระบรมราชินี'),
    (date(2026,  7, 28), 'วันพระบรมราชสมภพ ร.10'),
    (date(2026,  7, 29), 'วันอาสาฬหบูชา'),
    (date(2026,  7, 30), 'วันเข้าพรรษา'),
    (date(2026,  8, 12), 'วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าสิริกิติ์ฯ'),
    (date(2026, 10, 13), 'วันคล้ายวันสวรรคต ร.9'),
    (date(2026, 10, 23), 'วันปิยมหาราช'),
    (date(2026, 12,  5), 'วันคล้ายวันพระบรมราชสมภพ ร.9'),
    (date(2026, 12,  7), 'วันหยุดชดเชยวันพ่อแห่งชาติ'),
    (date(2026, 12, 10), 'วันรัฐธรรมนูญ'),
    (date(2026, 12, 31), 'วันสิ้นปี'),
    # ปิดให้บริการชั่วคราว
    (date(2026,  3, 24), 'งดให้บริการชั่วคราว'),
    (date(2026,  3, 25), 'งดให้บริการชั่วคราว'),
    (date(2026,  3, 26), 'งดให้บริการชั่วคราว'),
    (date(2026,  3, 27), 'งดให้บริการชั่วคราว'),
    (date(2026,  3, 15), 'งดจ่ายกระแสไฟฟ้า'),
    (date(2026,  4, 11), 'ปิดให้บริการชั่วคราว เนื่องในมาตรการประหยัดพลังงาน'),
    (date(2026,  4, 12), 'ปิดให้บริการชั่วคราว เนื่องในมาตรการประหยัดพลังงาน'),
    (date(2026,  4, 13), 'ปิดให้บริการชั่วคราว เนื่องในมาตรการประหยัดพลังงาน'),
]


class Command(BaseCommand):
    help = 'โหลดวันหยุดเริ่มต้น 2026 เข้า HolidayDate'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='ลบข้อมูลเก่าก่อน')

    def handle(self, *args, **options):
        if options['clear']:
            HolidayDate.objects.all().delete()
            self.stdout.write('ลบข้อมูลเดิมแล้ว')

        created = updated = 0
        for d, desc in HOLIDAYS:
            obj, is_new = HolidayDate.objects.update_or_create(
                date=d,
                defaults={'description': desc, 'is_active': True},
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'เสร็จสิ้น: สร้างใหม่ {created} รายการ, อัปเดต {updated} รายการ'
        ))
