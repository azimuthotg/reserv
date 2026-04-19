from django import forms
from django.contrib.auth.models import User
from .models import HolidayDate, Room


class HolidayDateForm(forms.ModelForm):
    class Meta:
        model  = HolidayDate
        fields = ['date', 'description', 'is_active']
        widgets = {
            'date':        forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น วันสงกรานต์'}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'date':        'วันที่',
            'description': 'คำอธิบาย / ชื่อวันหยุด',
            'is_active':   'เปิดใช้งาน',
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = ['name', 'booking_name', 'description', 'location',
                  'capacity', 'open_time', 'close_time', 'is_active', 'ha_entity_id']
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'form-control'}),
            'booking_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น netflix, mini'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location':     forms.TextInput(attrs={'class': 'form-control'}),
            'capacity':     forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'open_time':    forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'close_time':   forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'is_active':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ha_entity_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phase 2: IoT entity ID'}),
        }
        labels = {
            'name':         'ชื่อห้อง',
            'booking_name': 'Booking Key (URL param)',
            'description':  'คำอธิบาย',
            'location':     'ที่ตั้ง',
            'capacity':     'ความจุ (คน)',
            'open_time':    'เวลาเปิด',
            'close_time':   'เวลาปิด',
            'is_active':    'เปิดใช้งาน',
            'ha_entity_id': 'Home Assistant Entity ID',
        }


class StaffAddForm(forms.Form):
    username   = forms.CharField(label='ชื่อผู้ใช้', max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='ชื่อ', max_length=150, required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(label='นามสกุล', max_length=150, required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(label='อีเมล', required=False,
                                  widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1  = forms.CharField(label='รหัสผ่าน',
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2  = forms.CharField(label='ยืนยันรหัสผ่าน',
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    is_superuser = forms.BooleanField(label='ผู้ดูแลระบบ (สิทธิ์เต็ม)', required=False,
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('ชื่อผู้ใช้นี้มีอยู่แล้ว')
        return username

    def clean(self):
        cd = super().clean()
        if cd.get('password1') != cd.get('password2'):
            raise forms.ValidationError('รหัสผ่านไม่ตรงกัน')
        return cd


class StaffEditForm(forms.Form):
    first_name = forms.CharField(label='ชื่อ', max_length=150, required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(label='นามสกุล', max_length=150, required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(label='อีเมล', required=False,
                                  widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1  = forms.CharField(label='รหัสผ่านใหม่ (ว่าง = ไม่เปลี่ยน)', required=False,
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2  = forms.CharField(label='ยืนยันรหัสผ่านใหม่', required=False,
                                 widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    is_superuser = forms.BooleanField(label='ผู้ดูแลระบบ (สิทธิ์เต็ม)', required=False,
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError('รหัสผ่านไม่ตรงกัน')
        return cd
