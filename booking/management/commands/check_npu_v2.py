"""
ตรวจว่า reserv ขอ/ใช้ JWT token v2 ของ NPU API ได้จริง — ไม่แตะ flow ใช้งานจริง

# ขอ token + ยิง v2 endpoint ทดสอบ
python manage.py check_npu_v2

ผลที่คาดหวัง:
  - obtain token: ✅
  - v2 auth check: HTTP 404 = token ผ่าน (endpoint รับ Bearer แล้วแค่ไม่พบ record)
                   HTTP 401 = token ไม่ผ่าน (credential/permission ผิด)
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from booking.views import _npu_v2_token, _npu_v2_request


class Command(BaseCommand):
    help = 'ตรวจการขอ/ใช้ JWT token v2 ของ NPU API'

    def handle(self, *args, **options):
        if settings.NPU_API_V2_TOKEN:
            self.stdout.write('config: ใช้ NPU_API_V2_TOKEN (access token สำเร็จรูปจาก .env)')
        elif settings.NPU_API_USERNAME and settings.NPU_API_PASSWORD:
            self.stdout.write('config: ใช้ NPU_API_USERNAME/PASSWORD ขอ token จาก /v2/token/')
        else:
            self.stdout.write('❌ ยังไม่ได้ตั้ง NPU_API_V2_TOKEN หรือ NPU_API_USERNAME/PASSWORD ใน .env')
            return

        token = _npu_v2_token(force_refresh=True)
        if not token:
            self.stdout.write('❌ obtain token: ล้มเหลว — เช็ค username/password หรือการเชื่อมต่อ api.npu.ac.th')
            return
        self.stdout.write(f'✅ obtain token: สำเร็จ (len={len(token)})')

        # ยิง endpoint ที่ต้องใช้ Bearer ด้วย id ที่ไม่มีจริง → คาดหวัง 404 (auth ผ่าน) ไม่ใช่ 401
        resp = _npu_v2_request('GET', '/v2/data/__check_npu_v2__/')
        if resp is None:
            self.stdout.write('❌ v2 request: เชื่อมต่อไม่ได้')
            return

        code = resp.status_code
        if code == 401:
            self.stdout.write(f'❌ v2 auth check: HTTP 401 — token ไม่ได้รับการยอมรับ (เช็คสิทธิ์บัญชี reserv)')
        elif code in (403, 404):
            self.stdout.write(f'✅ v2 auth check: HTTP {code} — token ผ่าน (endpoint รับ Bearer แล้ว)')
        else:
            self.stdout.write(f'⚠️ v2 auth check: HTTP {code} — token น่าจะผ่าน แต่ตรวจ response เพิ่ม: {resp.text[:200]}')
