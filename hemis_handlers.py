"""
HEMIS funksiyalari uchun bot handlerlari
PRODUCTION READY VERSION
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from datetime import datetime

from hemis_api import HemisAPI
from rate_limit import rate_limited
from admin_notify import notify

# Conversation states
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)

hemis_api = HemisAPI()

# ---------------- STRINGS ----------------
HEMIS_STRINGS = {
    "uz": {
        "hemis_main": "🎓 *HEMIS Tizimi*\n\nQuyidagi bo'limlardan birini tanlang:",
        "btn_login": "🔐 Tizimga kirish",
        "btn_my_info": "👤 Mening ma'lumotlarim",
        "btn_subjects": "📚 Fanlar",
        "btn_grades": "📊 Baholar",
        "btn_attendance": "📅 Davomat",
        "btn_schedule": "🕐 Dars jadvali",
        "btn_payment": "💳 To'lov ma'lumotlari",
        "btn_logout": "🚪 Chiqish",
        "login_prompt": "🔐 *HEMIS login (ID)* ni kiriting:",
        "password_prompt": "🔑 *Parolni kiriting:*",
        "loading": "⏳ Yuklanmoqda...",
        "login_failed": "❌ Login yoki parol xato",
        "not_logged": "⚠️ Avval HEMIS ga kiring",
        "logout": "🚪 Tizimdan chiqdingiz"
    }
}

# ---------------- HELPERS ----------------
def _get_tokens(context):
    return context.user_data.get("hemis_access"), context.user_data.get("hemis_refresh")

def _save_tokens(context, new):
    if new:
        context.user_data["hemis_access"] = new["access"]
        context.user_data["hemis_refresh"] = new["refresh"]

# ---------------- MAIN MENU ----------------
def hemis_main_menu(update, context):
    lang = context.user_data.get("lang", "uz")
    s = HEMIS_STRINGS[lang]

    logged = context.user_data.get("hemis_access")

    if logged:
        keyboard = [
            [InlineKeyboardButton(s["btn_my_info"], callback_data="hemis_info")],
            [InlineKeyboardButton(s["btn_subjects"], callback_data="hemis_subjects")],
            [InlineKeyboardButton(s["btn_grades"], callback_data="hemis_grades")],
            [InlineKeyboardButton(s["btn_schedule"], callback_data="hemis_schedule")],
            [InlineKeyboardButton(s["btn_payment"], callback_data="hemis_payment")],
            [InlineKeyboardButton(s["btn_logout"], callback_data="hemis_logout")]
        ]
    else:
        keyboard = [[InlineKeyboardButton(s["btn_login"], callback_data="hemis_login_start")]]

    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        update.callback_query.message.reply_text(
            s["hemis_main"], parse_mode="Markdown", reply_markup=markup
        )
    else:
        update.message.reply_text(
            s["hemis_main"], parse_mode="Markdown", reply_markup=markup
        )

# ---------------- LOGIN ----------------
def hemis_login_start(update, context):
    print("DEBUG: hemis_login_start called")
    update.callback_query.answer()
    update.callback_query.message.reply_text(
        HEMIS_STRINGS["uz"]["login_prompt"], parse_mode="Markdown"
    )
    return LOGIN_USERNAME

def hemis_login_username(update, context):
    print(f"DEBUG: hemis_login_username called with {update.message.text}")
    context.user_data["hemis_username"] = update.message.text.strip()
    update.message.reply_text(
        HEMIS_STRINGS["uz"]["password_prompt"], parse_mode="Markdown"
    )
    return LOGIN_PASSWORD

def hemis_login_password(update, context):
    password = update.message.text.strip()
    username = context.user_data.get("hemis_username")

    try:
        update.message.delete()
    except:
        pass

    if rate_limited(context, "hemis_login", 2):
        update.message.reply_text("⏳ Sekinroq urinib ko‘ring")
        return ConversationHandler.END

    result = hemis_api.login(username, password)

    if not result["success"]:
        error_msg = result.get("error", "")
        if "connection" in error_msg.lower() or "network" in error_msg.lower():
            update.message.reply_text(
                "❌ *HEMIS serveriga ulanib bo'lmadi*\n\n"
                "Internet aloqangizni tekshiring yoki keyinroq urinib ko'ring.\n\n"
                "Agar muammo davom etsa, HEMIS serveri vaqtincha ishlamayotgan bo'lishi mumkin.",
                parse_mode="Markdown"
            )
        else:
            update.message.reply_text(HEMIS_STRINGS["uz"]["login_failed"])
        return ConversationHandler.END

    context.user_data["hemis_access"] = result["access"]
    context.user_data["hemis_refresh"] = result["refresh"]

    notify(
        context.bot,
        f"🟢 HEMIS LOGIN: {result['student'].get('name','Nomaʼlum')}"
    )

    update.message.reply_text(
        f"✅ Xush kelibsiz\n👤 {result['student'].get('name','')}"
    )

    print(f"DEBUG: Login success for {result['student'].get('name')}")
    hemis_main_menu(update, context)
    return ConversationHandler.END

# ---------------- INFO ----------------
def hemis_info(update, context):
    query = update.callback_query
    query.answer()

    access, refresh = _get_tokens(context)
    if not access:
        query.message.reply_text(HEMIS_STRINGS["uz"]["not_logged"])
        return

    msg = query.message.reply_text(HEMIS_STRINGS["uz"]["loading"])

    data, new = hemis_api.student_info(access, refresh)
    _save_tokens(context, new)

    if not data:
        msg.edit_text("❌ Maʼlumot olinmadi")
        return

    text = (
        f"👤 *{data.get('name')}*\n"
        f"🆔 {data.get('student_id_number')}\n"
        f"👥 {data.get('group',{}).get('name')}\n"
        f"🏛 {data.get('faculty',{}).get('name')}"
    )
    msg.edit_text(text, parse_mode="Markdown")

# ---------------- SUBJECTS ----------------
def hemis_subjects(update, context):
    query = update.callback_query
    query.answer()

    access, refresh = _get_tokens(context)
    if not access:
        query.message.reply_text(HEMIS_STRINGS["uz"]["not_logged"])
        return

    msg = query.message.reply_text("⏳ Yuklanmoqda...")
    r, new = hemis_api.safe_get(
        f"{hemis_api.base_url}/education/student-subject",
        access, refresh
    )
    _save_tokens(context, new)

    if not r:
        msg.edit_text("❌ Xatolik")
        return

    items = r.json()["data"]["items"]
    text = "📚 *Fanlar:*\n\n"
    for i in items:
        text += f"• {i['subject']['name']} ({i['credit']} kredit)\n"

    msg.edit_text(text, parse_mode="Markdown")

# ---------------- GRADES ----------------
def hemis_grades(update, context):
    query = update.callback_query
    query.answer()

    access, refresh = _get_tokens(context)
    if not access:
        query.message.reply_text(HEMIS_STRINGS["uz"]["not_logged"])
        return

    msg = query.message.reply_text("⏳ Yuklanmoqda...")
    r, new = hemis_api.safe_get(
        f"{hemis_api.base_url}/education/student-grade",
        access, refresh
    )
    _save_tokens(context, new)

    if not r:
        msg.edit_text("❌ Xatolik")
        return

    items = r.json()["data"]["items"]
    text = "📊 *Baholar:*\n\n"
    for g in items:
        text += f"• {g['subject']['name']} — *{g['grade']}*\n"

    msg.edit_text(text, parse_mode="Markdown")

# ---------------- SCHEDULE ----------------
def hemis_schedule(update, context):
    query = update.callback_query
    query.answer()

    access, refresh = _get_tokens(context)
    if not access:
        query.message.reply_text(HEMIS_STRINGS["uz"]["not_logged"])
        return

    today = datetime.now().strftime("%Y-%m-%d")
    msg = query.message.reply_text("⏳ Yuklanmoqda...")

    r, new = hemis_api.safe_get(
        f"{hemis_api.base_url}/education/time-table?date={today}",
        access, refresh
    )
    _save_tokens(context, new)

    if not r:
        msg.edit_text("❌ Xatolik")
        return

    items = r.json()["data"]["items"]
    if not items:
        msg.edit_text("✅ Bugun dars yo‘q")
        return

    text = "🕐 *Bugungi jadval:*\n\n"
    for l in items:
        text += f"{l['start_time']} - {l['end_time']} | {l['subject']['name']}\n"

    msg.edit_text(text, parse_mode="Markdown")

# ---------------- PAYMENT ----------------
def hemis_payment(update, context):
    query = update.callback_query
    query.answer()

    access, refresh = _get_tokens(context)
    if not access:
        query.message.reply_text(HEMIS_STRINGS["uz"]["not_logged"])
        return

    msg = query.message.reply_text("⏳ Yuklanmoqda...")
    r, new = hemis_api.safe_get(
        f"{hemis_api.base_url}/finance/student-contract",
        access, refresh
    )
    _save_tokens(context, new)

    if not r:
        msg.edit_text("❌ Xatolik")
        return

    d = r.json()["data"]
    msg.edit_text(
        f"💳 *To‘lov*\n"
        f"Umumiy: {d['summa']}\n"
        f"To‘langan: {d['paid_summa']}\n"
        f"Qarz: {d['debt_summa']}",
        parse_mode="Markdown"
    )

# ---------------- LOGOUT ----------------
def hemis_logout(update, context):
    query = update.callback_query
    query.answer()

    context.user_data.pop("hemis_access", None)
    context.user_data.pop("hemis_refresh", None)
    context.user_data.pop("hemis_username", None)

    query.message.reply_text(HEMIS_STRINGS["uz"]["logout"])
    hemis_main_menu(update, context)
