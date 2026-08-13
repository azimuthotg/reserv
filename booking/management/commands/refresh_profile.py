"""
python manage.py refresh_profile <ค่าที่ใช้ค้นหา>

ล้าง cache profile ของผู้ใช้ทีละคน แล้วดึงชื่อ-คณะ-สาขาใหม่จาก api.npu.ac.th
ใช้ตอนเจ้าหน้าที่ได้รับแจ้งว่า "ชื่อบนบัตร/หน้าจองไม่ใช่ของฉัน"

ค้นได้ทั้งรหัส LDAP, LINE userId และชื่อจริงบางส่วน — ใส่ --dry-run เพื่อดูก่อนแก้
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from booking.models import LineUser
from booking.views import (
    _fetch_npu_user, _get_or_refresh_line_user, _parse_profile, _fetch_npu_profile,
)


class Command(BaseCommand):
    help = 'ดึง profile จาก NPU API มาทับ cache ของ LineUser ที่ระบุ'

    def add_arguments(self, parser):
        parser.add_argument('query', help='รหัส LDAP, LINE userId หรือบางส่วนของชื่อ')
        parser.add_argument('--dry-run', action='store_true',
                            help='แสดงว่าจะเปลี่ยนเป็นอะไร โดยไม่บันทึก')

    def handle(self, *args, **options):
        query = options['query'].strip()
        users = LineUser.objects.filter(
            Q(user_ldap=query) | Q(line_user_id=query) | Q(full_name__icontains=query)
        )
        if not users:
            raise CommandError(f'ไม่พบผู้ใช้ที่ตรงกับ "{query}"')

        for lu in users:
            self.stdout.write(f'\n{lu.line_user_id}  (LINE: {lu.display_name})')
            self.stdout.write(f'  cache เดิม : {lu.user_ldap} | {lu.full_name} | {lu.faculty}')

            # ถามการผูกบัญชีล่าสุดจาก api ก่อน — รหัสที่ cache ไว้อาจเป็นของเก่า
            npu = _fetch_npu_user(lu.line_user_id)
            if not npu:
                self.stdout.write(self.style.WARNING(
                    '  api ไม่พบการผูกบัญชีของ LINE ID นี้ — ให้ผู้ใช้ลงทะเบียนใหม่'))
                continue

            user_ldap = npu.get('userLdap', '')
            user_type = npu.get('user_type', '')

            if options['dry_run']:
                full_name, faculty, dept = _parse_profile(
                    _fetch_npu_profile(user_ldap, user_type))
                self.stdout.write(f'  จะเปลี่ยนเป็น: {user_ldap} | {full_name} | {faculty}')
                continue

            fresh = _get_or_refresh_line_user(
                lu.line_user_id, lu.display_name, user_ldap, user_type, force=True)
            self.stdout.write(self.style.SUCCESS(
                f'  cache ใหม่ : {fresh.user_ldap} | {fresh.full_name} | {fresh.faculty}'))
