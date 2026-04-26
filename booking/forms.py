from django import forms
from django.contrib.auth.models import User
from .models import HolidayDate, Room, RoomClosure


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


class RoomClosureForm(forms.ModelForm):
    class Meta:
        model  = RoomClosure
        fields = ['room', 'date', 'period', 'reason', 'is_active']
        widgets = {
            'room':      forms.Select(attrs={'class': 'form-select'}),
            'date':      forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period':    forms.Select(attrs={'class': 'form-select'}),
            'reason':    forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'เช่น ซ่อมแอร์, ประชุมภายใน'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'room':      'ห้อง',
            'date':      'วันที่',
            'period':    'ช่วงเวลา',
            'reason':    'สาเหตุ',
            'is_active': 'เปิดใช้งาน',
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = [
            'name', 'booking_name', 'description', 'location',
            'capacity', 'min_attendees', 'max_booking_hours',
            'open_time', 'close_time',
            'eligible_users', 'how_to_use', 'facilities', 'rules',
            'is_active', 'ha_entity_id',
        ]
        widgets = {
            'name':              forms.TextInput(attrs={'class': 'form-control'}),
            'booking_name':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น mini, canva'}),
            'description':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location':          forms.TextInput(attrs={'class': 'form-control'}),
            'capacity':          forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_attendees':     forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_booking_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'open_time':         forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'close_time':        forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'eligible_users':    forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'เช่น นักศึกษา บุคลากร และอาจารย์ มนพ.'}),
            'how_to_use':        forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                     'placeholder': 'สแกน QR Code เพื่อจองผ่าน LINE OA\nแสดง QR Code การจองแก่เจ้าหน้าที่\nรับกุญแจและเข้าใช้บริการ'}),
            'facilities':        forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                     'placeholder': 'โปรเจกเตอร์\nระบบเสียง\nไมโครโฟน\nจอ LED'}),
            'rules':             forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                     'placeholder': 'ห้ามนำอาหารและเครื่องดื่มเข้าห้อง\nต้องคืนกุญแจหลังใช้งาน'}),
            'is_active':         forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ha_entity_id':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phase 2: IoT entity ID'}),
        }
        labels = {
            'name':              'ชื่อห้อง',
            'booking_name':      'Booking Key (URL param)',
            'description':       'คำอธิบาย',
            'location':          'ที่ตั้ง',
            'capacity':          'ความจุสูงสุด (คน)',
            'min_attendees':     'จำนวนผู้ใช้ขั้นต่ำ (คน)',
            'max_booking_hours': 'เวลาจองสูงสุดต่อครั้ง (ชั่วโมง)',
            'open_time':         'เวลาเปิด',
            'close_time':        'เวลาปิด',
            'eligible_users':    'ผู้มีสิทธิ์ใช้บริการ',
            'how_to_use':        'ขั้นตอนการใช้บริการ',
            'facilities':        'อุปกรณ์ / สิ่งอำนวยความสะดวก',
            'rules':             'กฎระเบียบการใช้ห้อง',
            'is_active':         'เปิดใช้งาน',
            'ha_entity_id':      'Home Assistant Entity ID',
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
