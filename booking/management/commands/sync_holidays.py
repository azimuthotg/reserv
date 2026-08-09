"""ดึงวันหยุดราชการจากปฏิทินสาธารณะเข้าตาราง HolidayDate

    python manage.py sync_holidays                # ปีนี้ + ปีหน้า
    python manage.py sync_holidays --year 2027
    python manage.py sync_holidays --dry-run      # ดูอย่างเดียว ไม่เขียนฐาน

**บันทึกเป็นฉบับร่างเสมอ (`is_active=False`)** เพราะปฏิทินสาธารณะไม่ตรงกับวันหยุด
ของสำนักฯ 100% (ดู booking/holiday_feed.py) เจ้าหน้าที่ต้องกด "เปิดใช้" เองที่
/manage/holidays/ วันหยุดจึงจะมีผลบล็อกการจอง

**ไม่แตะแถวที่เจ้าหน้าที่เพิ่มเอง** (`source='manual'`) แม้วันจะตรงกัน — กันไม่ให้
คำอธิบายหรือสถานะที่คนตั้งไว้ถูกเขียนทับ
"""
from datetime import date

from django.core.management.base import BaseCommand

from booking.holiday_feed import HolidayFeedError, fetch_holidays
from booking.models import HolidayDate


class Command(BaseCommand):
    help = 'ดึงวันหยุดราชการจากปฏิทินสาธารณะเข้า HolidayDate (เป็นฉบับร่าง รอเจ้าหน้าที่ยืนยัน)'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, action='append',
                            help='ปี ค.ศ. ที่ต้องการ (ระบุซ้ำได้) ไม่ระบุ = ปีนี้และปีหน้า')
        parser.add_argument('--dry-run', action='store_true', help='ไม่เขียนฐานข้อมูล')

    def handle(self, *args, **options):
        years = options['year'] or [date.today().year, date.today().year + 1]
        dry = options['dry_run']

        created = skipped_manual = existed = 0
        for year in years:
            try:
                items = fetch_holidays(year=year)
            except HolidayFeedError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                return

            self.stdout.write(f'\nปี {year}: ปฏิทินมี {len(items)} วัน')
            for d, summary in items:
                existing = HolidayDate.objects.filter(date=d).first()
                if existing:
                    if existing.source == HolidayDate.SOURCE_MANUAL:
                        skipped_manual += 1
                        self.stdout.write(f'  – {d} ข้ามไว้ (เจ้าหน้าที่เพิ่มเอง: {existing.description})')
                    else:
                        existed += 1
                    continue

                created += 1
                mark = '[ดูอย่างเดียว] ' if dry else ''
                self.stdout.write(self.style.WARNING(f'  + {mark}{d} {summary}'))
                if not dry:
                    HolidayDate.objects.create(
                        date=d, description=summary,
                        is_active=False,               # ฉบับร่าง รอเจ้าหน้าที่ยืนยัน
                        source=HolidayDate.SOURCE_AUTO,
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'เพิ่มใหม่ {created} วัน · มีอยู่แล้ว {existed} วัน · '
            f'ข้ามเพราะเจ้าหน้าที่เพิ่มเอง {skipped_manual} วัน'
        ))
        if created and not dry:
            self.stdout.write(self.style.WARNING(
                'รายการใหม่ทั้งหมดเป็น "ฉบับร่าง" ยังไม่บล็อกการจอง — '
                'ให้เจ้าหน้าที่ตรวจและกดเปิดใช้ที่ /manage/holidays/'
            ))
