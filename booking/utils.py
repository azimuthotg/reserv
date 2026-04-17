import requests
from django.conf import settings

NPU_API = settings.NPU_API_BASE  # https://api.npu.ac.th


def get_npu_user(line_user_id):
    """เช็คว่า LINE userId ผูกบัญชีแล้วไหม
    return: {id, userId, userLdap, user_type} หรือ None
    """
    try:
        r = requests.get(f"{NPU_API}/api/{line_user_id}/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            # API คืน null หรือ object เปล่าถ้ายังไม่ผูก
            if data and data.get('userId'):
                return data
    except Exception:
        pass
    return None


def register_npu_user(line_user_id, user_ldap, user_type):
    """ผูกบัญชีใหม่ที่ api.npu.ac.th
    return: True/False
    """
    try:
        r = requests.post(f"{NPU_API}/api/", json={
            "userId": line_user_id,
            "userLdap": user_ldap,
            "user_type": user_type,
        }, timeout=5)
        return r.status_code in [200, 201]
    except Exception:
        return False


def get_profile(user_ldap, user_type):
    """ดึงชื่อ-คณะ-สาขา ตาม user_type
    return: {full_name, faculty, department} หรือ None
    """
    try:
        if user_type == "นักศึกษา":
            r = requests.get(f"{NPU_API}/std-info/{user_ldap}/", timeout=5)
            if r.status_code == 200:
                d = r.json()
                return {
                    "full_name":  f"{d['prefix_name']}{d['student_name']} {d['student_surname']}",
                    "faculty":    d["faculty_name"],
                    "department": d["program_name"],
                    "student_code": d.get("student_code", user_ldap),
                }
        else:  # บุคลากรภายในมหาวิทยาลัย
            r = requests.get(f"{NPU_API}/staff-info/{user_ldap}/", timeout=5)
            if r.status_code == 200:
                d = r.json()
                return {
                    "full_name":  f"{d['prefixfullname']}{d['staffname']} {d['staffsurname']}",
                    "faculty":    d["departmentname"],
                    "department": d["posnameth"],
                    "citizen_id": d.get("staffcitizenid", user_ldap),
                }
    except Exception:
        pass
    return None


def verify_ldap(username, password):
    """ตรวจสอบ username/password กับ AD มน. ผ่าน api.npu.ac.th
    return: (success: bool, error_message: str|None)
    """
    try:
        r = requests.post(f"{NPU_API}/auth-ldap/auth_ldap/", json={
            "userLdap": username,
            "passLdap": password,
        }, timeout=5)
        if r.status_code == 200:
            return True, None
        return False, "ไม่พบข้อมูลในระบบ LDAP"
    except Exception:
        return False, "ไม่สามารถเชื่อมต่อระบบได้"


def get_walai_status(user_ldap):
    """ตรวจสอบสมาชิกห้องสมุด Walai AutoLib (Phase 3)
    return: dict หรือ None
    """
    try:
        r = requests.get(f"{NPU_API}/walai/check_user_walai/{user_ldap}/", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None
