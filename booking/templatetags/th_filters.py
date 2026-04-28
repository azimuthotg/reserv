from django import template
from django.utils import timezone

register = template.Library()

_MONTHS_LONG = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']

_WEEKDAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']


@register.filter
def th_date(value):
    """05/05/2568"""
    if not value:
        return '—'
    try:
        return f'{value.day:02d}/{value.month:02d}/{value.year + 543}'
    except AttributeError:
        return str(value)


@register.filter
def th_date_long(value):
    """5 พฤษภาคม 2568"""
    if not value:
        return '—'
    try:
        return f'{value.day} {_MONTHS_LONG[value.month]} {value.year + 543}'
    except (AttributeError, IndexError):
        return str(value)


@register.filter
def th_weekday(value):
    """จันทร์"""
    if not value:
        return '—'
    try:
        return _WEEKDAYS[value.weekday()]
    except AttributeError:
        return str(value)


@register.filter
def th_datetime(value):
    """05/05/2568 14:30"""
    if not value:
        return '—'
    try:
        v = timezone.localtime(value) if timezone.is_aware(value) else value
        return f'{v.day:02d}/{v.month:02d}/{v.year + 543} {v.hour:02d}:{v.minute:02d}'
    except AttributeError:
        return str(value)


@register.filter
def th_datetime_sec(value):
    """05/05/2568 14:30:25"""
    if not value:
        return '—'
    try:
        v = timezone.localtime(value) if timezone.is_aware(value) else value
        return f'{v.day:02d}/{v.month:02d}/{v.year + 543} {v.hour:02d}:{v.minute:02d}:{v.second:02d}'
    except AttributeError:
        return str(value)
