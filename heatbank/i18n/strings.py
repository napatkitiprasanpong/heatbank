"""C6 multilingual strings (plan R2). English is the reference. Thai is a DRAFT written by Claude and MUST be reviewed by a
human Thai speaker before submission (plan C6; the owner is a Thai speaker). The third language is the team's choice and is
left empty on purpose: add a dict under LANGS and `missing_keys()` tells you what is still untranslated. Missing keys fall
back to English, never to a blank.

Level names are words AND shapes AND colours in the UI, so meaning never depends on colour alone."""
from ..alerts import engine as alerts

REVIEW_STATUS = {"en": "reference", "th": "DRAFT - needs human review"}

_EN = {
    "app_name": "HeatBank",
    "tagline": "A heat budget for every shift",
    "level_0": "Green", "level_1": "Yellow", "level_2": "Orange", "level_3": "Red",
    "action_normal_work": alerts.ACTIONS[0][2],
    "action_drink_shade_break": alerts.ACTIONS[1][2],
    "action_reduce_cool_now": alerts.ACTIONS[2][2],
    "action_stop_cool_buddy": alerts.ACTIONS[3][2],
    "banner_offline": "Offline: using the saved forecast.",
    "banner_stale": "Forecast is old. Alert level raised for safety.",
    "banner_no_data": "No forecast. Treat this as Red.",
    "banner_sensor": "Site sensor is not trustworthy. Level raised.",
    "banner_battery": "Site sensor battery is low.",
    "banner_model": "The heat model could not run. Treat this as Red.",
    "banner_demo": "DEMO: simulated data and a simulated clock. Not real conditions.",
    "heat_budget": "Heat budget used",
    "budget_note": "Share of the safe exposure time already used",
    "this_hour": "This hour",
    "work": "Work", "rest": "Rest", "min": "min",
    "today": "Today",
    "next_change": "Next change",
    "no_change": "No change expected today",
    "changes_to": "{level} expected from {hour}:00",
    "updated": "Forecast saved",
    "age_min": "{n} min ago",
    "worker_view": "Worker view", "supervisor_view": "Supervisor view",
    "col_level": "Level",
    "crew_group": "Crew group", "zone": "Zone", "crew_size": "Crew",
    "first_break": "First break", "at_minute": "at minute {n}",
    "no_break_needed": "none needed",
    "rotation": "Rotation", "rotate_yes": "Rotate heavy tasks", "rotate_no": "-",
    "pooled": "Other zones (pooled)",
    "site_worst": "Site status",
    "site_worst_note": "Highest level in any crew group. No counts, no names.",
    "privacy_note": "Crew groups come from the task roster. No names, no readings, no individual health data.",
    "small_groups_note": "Groups smaller than {k} are pooled so no one can be singled out.",
    "disclaimer": "Planning prototype. Not a medical device. Thresholds are proposed values, not clinical guidance. People decide.",
    "simulated": "SIMULATED crew and weather",
    "red_card_title": "If someone may be ill from heat",
    "red_card_body": "Call the medic or emergency number now. Move the person to shade or a cool place. Cool the body with water and air. Do not leave them alone. Do this if they are confused, faint, very unwell, or have stopped sweating.",
    "red_card_review": "Draft first-aid wording: a clinician or occupational health professional must review it.",
    "demo_controls": "Demo controls",
    "archetype": "Worker type", "hour": "Hour", "condition": "Connection",
    "cond_ok": "Normal", "cond_offline": "Offline (fresh cache)", "cond_stale": "Offline 5 hours (stale)", "cond_none": "No forecast",
    "language": "Language",
    "work_rest_line": "Work {w} min, then rest {r} min.",
    "task_light": "Light work", "task_moderate": "Moderate work", "task_heavy": "Heavy work",
    "cloth_light_clothing": "light clothing", "cloth_coverall_ppe": "coverall / PPE",
    "acc_yes": "acclimatised", "acc_no": "not acclimatised",
}

_TH = {
    "app_name": "HeatBank",
    "tagline": "งบประมาณความร้อนสำหรับทุกกะงาน",
    "level_0": "เขียว", "level_1": "เหลือง", "level_2": "ส้ม", "level_3": "แดง",
    "action_normal_work": "ทำงานตามปกติ เก็บน้ำดื่มไว้ใกล้มือ",
    "action_drink_shade_break": "ดื่มน้ำ และพักในที่ร่มตามเวลาที่กำหนด",
    "action_reduce_cool_now": "ลดความหนักของงานหรือสลับงาน แล้วพักให้ร่างกายเย็นลงทันที",
    "action_stop_cool_buddy": "หยุดงานหนัก พักให้ร่างกายเย็นลง ให้เพื่อนร่วมงานช่วยเช็กอาการ และเรียกหน่วยพยาบาลหากมีอาการผิดปกติ",
    "banner_offline": "ออฟไลน์: ใช้ข้อมูลพยากรณ์ที่บันทึกไว้",
    "banner_stale": "ข้อมูลพยากรณ์เก่าแล้ว ระบบเพิ่มระดับเตือนเพื่อความปลอดภัย",
    "banner_no_data": "ไม่มีข้อมูลพยากรณ์ ให้ถือว่าเป็นระดับแดง",
    "banner_sensor": "เซนเซอร์หน้างานไม่น่าเชื่อถือ เพิ่มระดับเตือนแล้ว",
    "banner_battery": "แบตเตอรี่เซนเซอร์หน้างานใกล้หมด",
    "banner_model": "ระบบคำนวณความเครียดจากความร้อนไม่ได้ ให้ถือว่าเป็นระดับแดง",
    "banner_demo": "โหมดสาธิต: ข้อมูลและเวลาเป็นการจำลอง ไม่ใช่สภาพจริง",
    "heat_budget": "งบความร้อนที่ใช้ไปแล้ว",
    "budget_note": "สัดส่วนของเวลาที่ปลอดภัยซึ่งใช้ไปแล้ว",
    "this_hour": "ชั่วโมงนี้",
    "work": "ทำงาน", "rest": "พัก", "min": "นาที",
    "today": "วันนี้",
    "next_change": "การเปลี่ยนแปลงถัดไป",
    "no_change": "วันนี้ไม่คาดว่าจะเปลี่ยนระดับ",
    "changes_to": "คาดว่าจะเป็นระดับ{level}ตั้งแต่ {hour}:00 น.",
    "updated": "บันทึกพยากรณ์เมื่อ",
    "age_min": "{n} นาทีที่แล้ว",
    "worker_view": "มุมมองคนทำงาน", "supervisor_view": "มุมมองหัวหน้างาน",
    "col_level": "ระดับ",
    "crew_group": "กลุ่มงาน", "zone": "พื้นที่", "crew_size": "จำนวนคน",
    "first_break": "พักครั้งแรก", "at_minute": "นาทีที่ {n}",
    "no_break_needed": "ไม่จำเป็น",
    "rotation": "การสลับงาน", "rotate_yes": "สลับงานหนัก", "rotate_no": "-",
    "pooled": "พื้นที่อื่น (รวมกลุ่ม)",
    "site_worst": "สถานะหน้างาน",
    "site_worst_note": "ระดับสูงสุดของกลุ่มงานใด ๆ ไม่แสดงจำนวนและไม่แสดงชื่อ",
    "privacy_note": "กลุ่มงานมาจากรายการมอบหมายงาน ไม่มีชื่อ ไม่มีค่าที่วัดจากตัวบุคคล ไม่มีข้อมูลสุขภาพรายบุคคล",
    "small_groups_note": "กลุ่มที่มีน้อยกว่า {k} คนจะถูกรวมกัน เพื่อไม่ให้ระบุตัวบุคคลได้",
    "disclaimer": "ต้นแบบสำหรับการวางแผน ไม่ใช่อุปกรณ์การแพทย์ ค่าเกณฑ์เป็นค่าที่เสนอ ไม่ใช่คำแนะนำทางคลินิก คนเป็นผู้ตัดสินใจ",
    "simulated": "ข้อมูลลูกทีมและสภาพอากาศเป็นการจำลอง",
    "red_card_title": "หากสงสัยว่าใครป่วยจากความร้อน",
    "red_card_body": "เรียกหน่วยพยาบาลหรือเบอร์ฉุกเฉินทันที พาผู้ป่วยไปที่ร่มหรือที่เย็น ระบายความร้อนด้วยน้ำและลม อย่าปล่อยให้อยู่คนเดียว ทำเช่นนี้หากสับสน เป็นลม ไม่สบายมาก หรือหยุดมีเหงื่อ",
    "red_card_review": "ข้อความปฐมพยาบาลฉบับร่าง: ต้องให้แพทย์หรือผู้เชี่ยวชาญด้านอาชีวอนามัยตรวจก่อนใช้จริง",
    "demo_controls": "ตัวควบคุมโหมดสาธิต",
    "archetype": "ประเภทงาน", "hour": "ชั่วโมง", "condition": "การเชื่อมต่อ",
    "cond_ok": "ปกติ", "cond_offline": "ออฟไลน์ (แคชยังใหม่)", "cond_stale": "ออฟไลน์ 5 ชั่วโมง (เก่า)", "cond_none": "ไม่มีพยากรณ์",
    "language": "ภาษา",
    "work_rest_line": "ทำงาน {w} นาที แล้วพัก {r} นาที",
    "task_light": "งานเบา", "task_moderate": "งานปานกลาง", "task_heavy": "งานหนัก",
    "cloth_light_clothing": "เสื้อผ้าบาง", "cloth_coverall_ppe": "ชุดคลุม / อุปกรณ์ป้องกัน (PPE)",
    "acc_yes": "ปรับตัวกับความร้อนแล้ว", "acc_no": "ยังไม่ปรับตัวกับความร้อน",
}

LANGS = {"en": _EN, "th": _TH}     # the team's third language goes here
LANG_LABEL = {"en": "English", "th": "ไทย"}


def missing_keys(lang: str):
    return sorted(set(_EN) - set(LANGS.get(lang, {})))


def get(lang: str, key: str) -> str:
    return LANGS.get(lang, {}).get(key) or _EN[key]


def bundle():
    """Full table per language with English fallback filled in, for the static front end."""
    return {l: {k: get(l, k) for k in _EN} for l in LANGS}
