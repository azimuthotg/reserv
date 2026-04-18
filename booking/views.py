import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# Google Apps Script form URLs สำหรับแต่ละห้อง
GAS_URLS = {
    'netflix':    'https://script.google.com/macros/s/AKfycbxFkKMyTdR65nNGyKqdiSAJ3QhAvqFbZdfOfLC5FiwwL8txefcHkSej8dykY4W8_jyz/exec',
    'mini':       'https://script.google.com/macros/s/AKfycbztdq1E8ErPtk-IrLhigtcWDh3TlRpNwy5f1Lojo61zMksYSsKF4Wm4361DeeZ31ZBR/exec',
    'canva':      'https://script.google.com/macros/s/AKfycbw_jXGQutF7AytcnS0D5LkB5_XswMA_K4bIkBFEENRjOhjIghcNc7jBo6l4hEUQ4LtJNQ/exec',
    'meeting_f1': 'https://script.google.com/macros/s/AKfycbygZ027Ua3K-EjA5cXTHLem8GFA1fqDsf9mEqjxcPhF2kvptQzLQGMpv9tZ0osNzPkS/exec',
    'chat-gpt':   'https://script.google.com/macros/s/AKfycby_USdtlYlCaYEn9E8uJkGLPYNEHTztcp8O05HtDQdKuz12xL1bQ3XxVbb0Lfht2EyzmQ/exec',
}

NPU_API_BASE  = 'https://api.npu.ac.th'
REGISTER_URL  = f'{NPU_API_BASE}/reserv/lineoa'


def booking_page(request):
    """หน้า LIFF สำหรับจองห้อง — แทนที่ netflix.html เดิม"""
    context = {
        'liff_id': settings.LINE_LIFF_ID,
        'gas_urls': json.dumps(GAS_URLS),
        'register_url': REGISTER_URL,
    }
    return render(request, 'booking/booking.html', context)


@csrf_exempt
@require_http_methods(['POST'])
def check_user(request):
    """
    Proxy → api.npu.ac.th/api/{userId}/
    รับ: { userId }
    คืน: { registered: true, userLdap, user_type } หรือ { registered: false }
    """
    try:
        body     = json.loads(request.body)
        user_id  = body.get('userId', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not user_id:
        return JsonResponse({'error': 'userId required'}, status=400)

    try:
        resp = requests.get(f'{NPU_API_BASE}/api/{user_id}/', timeout=10)
    except requests.RequestException:
        return JsonResponse({'error': 'upstream error'}, status=502)

    if resp.status_code == 200:
        data = resp.json()
        return JsonResponse({
            'registered': True,
            'userLdap':   data.get('user_ldap', ''),
            'user_type':  data.get('user_type', ''),
        })

    # 404 หรือ status อื่น = ยังไม่ได้ลงทะเบียน
    return JsonResponse({'registered': False})
