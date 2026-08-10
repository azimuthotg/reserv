"""ดึงวันหยุดราชการจากปฏิทินสาธารณะเข้าตาราง HolidayDate

    python manage.py sync_holidays                # 12 เดือนข้างหน้า (ค่าเริ่มต้น)
    python manage.py sync_holidays --days 180     # กำหนดช่วงเอง
    python manage.py sync_holidays --year 2027    # ทั้งปี (ระบุซ้ำได้)
    python manage.py sync_holidays --dry-run      # ดูอย่างเดียว ไม่เขียนฐาน

**ค่าเริ่มต้นดึงล่วงหน้าไม่เกิน 1 ปี** (ผู้ใช้กำหนด 2026-08-09) เพราะวันหยุดปีไกล ๆ
ครม. ยังไม่ประกาศและเปลี่ยนได้อีก ดึงมาก่อนก็รกรายการที่เจ้าหน้าที่ต้องตรวจเปล่า ๆ
ตั้งให้รันทุก 30 วัน จะได้ทันวันหยุดพิเศษที่ประกาศกลางปี

**บันทึกเป็นฉบับร่างเสมอ (`is_active=False`)** เพราะปฏิทินสาธารณะไม่ตรงกับวันหยุด
ของสำนักฯ 100% (ดู booking/holiday_feed.py) เจ้าหน้าที่ต้องกด "เปิดใช้" เองที่
/manage/holidays/ วันหยุดจึงจะมีผลบล็อกการจอง

**ไม่แตะแถวที่เจ้าหน้าที่เพิ่มเอง** (`source='manual'`) แม้วันจะตรงกัน — กันไม่ให้
คำอธิบายหรือสถานะที่คนตั้งไว้ถูกเขียนทับ
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from booking.holiday_feed import HolidayFeedError, fetch_holidays
from booking.models import HolidayDate, HolidaySyncRun

DEFAULT_DAYS = 365


class Command(BaseCommand):
    help = ('ดึงวันหยุดราชการจากปฏิทินสาธารณะเข้า HolidayDate '
            '(ล่วงหน้า 1 ปี เป็นฉบับร่าง รอเจ้าหน้าที่ยืนยัน)')

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=DEFAULT_DAYS,
                            help=f'ดึงล่วงหน้ากี่วันนับจากวันนี้ (ค่าเริ่มต้น {DEFAULT_DAYS})')
        parser.add_argument('--year', type=int, action='append',
                            help='ระบุทั้งปี ค.ศ. แทนการนับวัน (ระบุซ้ำได้)')
        parser.add_argument('--dry-run', action='store_true', help='ไม่เขียนฐานข้อมูล')

    def handle(self, *args, **options):
        dry = options['dry_run']
        today = date.today()

        if options['year']:
            batches = [({'year': y}, f'ปี {y}') for y in options['year']]
        else:
            end = today + timedelta(days=options['days'])
            batches = [({'start': today, 'end': end}, f'{today} ถึง {end}')]

        created = skipped_manual = existed = 0
        for kwargs, label in batches:
            try:
                items = fetch_holidays(**kwargs)
            except HolidayFeedError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                return

            self.stdout.write(f'\n{label}: ปฏิทินมี {len(items)} วัน')
            for d, summary in items:
                existing = HolidayDate.objects.filter(date=d).first()
                if existing:
                    if existing.source == HolidayDate.SOURCE_MANUAL:
                        skipped_manual += 1
                        self.stdout.write(
                            f'  – {d} ข้ามไว้ (เจ้าหน้าที่เพิ่มเอง: {existing.description})')
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

        # บันทึกไว้แม้ created = 0 — แดชบอร์ดต้องแยก "ดึงแล้วไม่เจอวันใหม่"
        # ออกจาก "ไม่มีใครดึงเลย" ให้ได้ ไม่งั้นเงียบเหมือนกันทั้งสองแบบ
        if not dry:
            HolidaySyncRun.objects.create(created_count=created,
                                          trigger=HolidaySyncRun.TRIGGER_COMMAND)

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
