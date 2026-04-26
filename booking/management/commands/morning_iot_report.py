"""
python manage.py morning_iot_report
รันทุกเช้าผ่าน Windows Task Scheduler (แนะนำ 07:30 น.)
ดึงสถานะ IoT ทุกอุปกรณ์ทุกห้อง แล้วส่งสรุปไปกลุ่ม LINE ผู้ดูแล
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from booking.models import Room, RoomDevice

LINE_PUSH_URL = 'https://api.line.me/v2/bot/message/push'


def _ha_get_state(entity_id):
    """คืน state ('on'/'off'/'unknown') หรือ None ถ้าเชื่อมต่อไม่ได้"""
    if not settings.HA_IP or not settings.HA_TOKEN:
        return None
    try:
        r = requests.get(
            f'http://{settings.HA_IP}:{settings.HA_PORT}/api/states/{entity_id}',
            headers={
                'Authorization': f'Bearer {settings.HA_TOKEN}',
                'Content-Type':  'application/json',
            },
            timeout=5,
        )
        if r.status_code == 200:
            return r.json().get('state', 'unknown')
        return None
    except requests.RequestException:
        return None


def _push_group(messages):
    """ส่ง push message ไปกลุ่ม LINE"""
    group_id = getattr(settings, 'LINE_GROUP_ID', '')
    token    = settings.LINE_CHANNEL_ACCESS_TOKEN
    if not group_id or not token:
        return False
    try:
        resp = requests.post(
            LINE_PUSH_URL,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type':  'application/json',
            },
            json={'to': group_id, 'messages': messages},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


class Command(BaseCommand):
    help = 'ส่งรายงานสถานะ IoT ประจำเช้าไปกลุ่ม LINE ผู้ดูแล'

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        rooms = Room.objects.filter(is_active=True).prefetch_related('devices')

        all_ok    = True
        room_lines = []
        total_online  = 0
        total_offline = 0
        total_unknown = 0

        for room in rooms:
            devices = list(room.devices.all())
            if not devices:
                continue

            device_lines = []
            room_ok = True
            for d in devices:
                state = _ha_get_state(d.entity_id)
                if state is None:
                    icon  = '❓'
                    label = 'ไม่ทราบ (HA offline?)'
                    total_unknown += 1
                    room_ok = False
                elif state in ('on', 'off'):
                    icon  = '🟢' if state == 'on' else '⚫'
                    label = 'Online' if state == 'on' else 'Standby'
                    total_online += 1
                else:
                    icon  = '🔴'
                    label = f'Offline ({state})'
                    total_offline += 1
                    room_ok = False
                device_lines.append(f'  {icon} {d.device_name}: {label}')

            if not room_ok:
                all_ok = False

            status_icon = '✅' if room_ok else '⚠️'
            room_lines.append(f'{status_icon} {room.name}')
            room_lines.extend(device_lines)

        # สร้างข้อความสรุป
        date_str = now.strftime('%d/%m/%Y %H:%M')
        if all_ok:
            header = f'✅ IoT ปกติทุกอุปกรณ์ — {date_str}'
        else:
            header = f'⚠️ พบอุปกรณ์ผิดปกติ — {date_str}'

        summary = f'Online: {total_online}  Offline: {total_offline}  ไม่ทราบ: {total_unknown}'

        lines = [header, '', summary, '']
        lines.extend(room_lines)
        if not all_ok:
            lines.append('')
            lines.append('กรุณาตรวจสอบและดำเนินการแก้ไข')

        text = '\n'.join(lines)

        ok = _push_group([{'type': 'text', 'text': text}])
        if ok:
            self.stdout.write(f'[{now.strftime("%H:%M:%S")}] ส่งรายงาน IoT เช้าสำเร็จ')
        else:
            self.stdout.write(self.style.WARNING(
                f'[{now.strftime("%H:%M:%S")}] ส่งรายงานไม่สำเร็จ (ตรวจสอบ LINE_GROUP_ID และ token)'
            ))
