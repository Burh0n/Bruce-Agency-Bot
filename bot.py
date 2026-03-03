#!/usr/bin/env python3
"""
🦇 BRUCE | Digital Agency — Client Bot
Multilingual: English, Russian, Uzbek
Orders forwarded to Admin Bot (Alfred).
"""

import os
import json
import logging
import httpx
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN       = os.getenv("BOT_TOKEN",)
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN",)
ADMIN_CHAT_ID   = int(os.getenv("ADMIN_CHAT_ID", "0"))
ORDERS_FILE     = "orders.json"

CHOOSING_LANG, CHOOSING_SERVICE, ENTERING_DETAILS, ENTERING_BUDGET, ENTERING_CONTACT = range(5)

logging.basicConfig(
    format="%(asctime)s | GOTHAM COMMS | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── TRANSLATIONS ──────────────────────────────────────────────────────────────
TEXTS = {
    "en": {
        "welcome": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "_Welcome to the shadows, {name}._\n\n"
            "We operate in the dark so your brand can shine in the light. "
            "From the rooftops of Gotham to the peaks of digital excellence.\n\n"
            "What does the night call for?"
        ),
        "btn_order":    "🦇 Order a Service",
        "btn_services": "📋 Our Services",
        "btn_about":    "🏙️ About Bruce Agency",
        "btn_order_now":"🦇 Order Now",
        "btn_back":     "◀ Back",
        "btn_hq":       "🏠 Back to HQ",
        "services_title": "*🦇 Bruce Agency Arsenal:*\n\n",
        "services_footer": "\n_Every pixel crafted in the shadows, every line forged like Batarangs._",
        "about": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "We are the digital guardians your brand deserves.\n\n"
            "Born in the darkness of competitive markets, forged by the flames of creativity. "
            "Bruce Agency delivers digital solutions that strike fear into mediocrity.\n\n"
            "📍 Operating from the shadows\n"
            "⚡ Response time: faster than a Batmobile\n"
            "🎯 Mission: Your brand's total domination\n\n"
            "_{quote}_"
        ),
        "choose_service": (
            "*🦇 Choose Your Weapon:*\n\n"
            "_Select the service you need. Bruce handles the rest from the shadows._"
        ),
        "service_selected": "*{name} — Selected* ✅\n\n_Now tell Alfred the details..._\n\nDescribe your project: what do you need, your vision, any requirements?",
        "ask_budget": "*🦇 Noted by Alfred.*\n\nWhat's your budget range?\n\n_E.g.: $500–1000, $2000+, flexible_",
        "ask_contact": "*🦇 Budget received.*\n\nHow should Bruce contact you?\n\n_Phone, email, or Telegram username_",
        "order_done": (
            "*🦇 Mission Brief Received — Order #{sid}*\n\n"
            "_The bat-signal has been lit. Bruce is already on it._\n\n"
            "Service: {service}\nBudget: {budget}\n\n"
            "We'll contact you at: *{contact}*\n"
            "Response time: within 24 hours.\n\n"
            "_{quote}_"
        ),
        "cancelled": "_Even Batman retreats sometimes. Order cancelled._\n\nType /start to return.",
        "quotes": [
            '"It\'s not who I am underneath, but what I do that defines me."',
            '"Why do we fall? So we can learn to pick ourselves back up."',
            '"The night is darkest just before the dawn."',
            '"I am the shadows. I am vengeance. I am BRUCE."',
        ],
        "services": {
            "web_dev":    "🌐 Web Development",
            "design":     "🎨 UI/UX Design",
            "branding":   "🦇 Brand Identity",
            "seo":        "📡 SEO & Marketing",
            "mobile":     "📱 Mobile App",
            "consulting": "🕵️ Strategy Consulting",
        },
    },
    "ru": {
        "welcome": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "_Добро пожаловать в тени, {name}._\n\n"
            "Мы работаем в темноте, чтобы ваш бренд сиял на свету. "
            "С крыш Готэма до вершин цифрового совершенства.\n\n"
            "Что зовёт тебя в эту ночь?"
        ),
        "btn_order":    "🦇 Заказать услугу",
        "btn_services": "📋 Наши услуги",
        "btn_about":    "🏙️ О Bruce Agency",
        "btn_order_now":"🦇 Заказать",
        "btn_back":     "◀ Назад",
        "btn_hq":       "🏠 На главную",
        "services_title": "*🦇 Арсенал Bruce Agency:*\n\n",
        "services_footer": "\n_Каждый пиксель создан в тени, каждая строка кода — как бэтаранг._",
        "about": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "Мы — цифровые стражи, которых заслуживает ваш бренд.\n\n"
            "Рождены в темноте конкурентных рынков, закалены пламенем творчества. "
            "Bruce Agency создаёт цифровые решения, которые вселяют страх в посредственность.\n\n"
            "📍 Работаем из теней\n"
            "⚡ Время ответа: быстрее Бэтмобиля\n"
            "🎯 Миссия: Полное доминирование вашего бренда\n\n"
            "_{quote}_"
        ),
        "choose_service": (
            "*🦇 Выбери своё оружие:*\n\n"
            "_Выберите нужную услугу. Брюс сделает всё остальное из теней._"
        ),
        "service_selected": "*{name} — Выбрано* ✅\n\n_Теперь расскажите Альфреду детали..._\n\nОпишите ваш проект: что нужно, ваше видение, требования?",
        "ask_budget": "*🦇 Альфред записал.*\n\nКаков ваш бюджет?\n\n_Например: $500–1000, $2000+, гибкий_",
        "ask_contact": "*🦇 Бюджет получен.*\n\nКак Брюс может с вами связаться?\n\n_Телефон, email или Telegram_",
        "order_done": (
            "*🦇 Бриф получен — Заказ #{sid}*\n\n"
            "_Бэт-сигнал зажжён. Брюс уже в деле._\n\n"
            "Услуга: {service}\nБюджет: {budget}\n\n"
            "Мы свяжемся с вами: *{contact}*\n"
            "Время ответа: в течение 24 часов.\n\n"
            "_{quote}_"
        ),
        "cancelled": "_Даже Бэтмен иногда отступает. Заказ отменён._\n\nНапишите /start для возврата.",
        "quotes": [
            '"Важно не то, кто я внутри, а то, что я делаю."',
            '"Почему мы падаем? Чтобы научиться подниматься."',
            '"Ночь темнее всего перед рассветом."',
            '"Я — тени. Я — возмездие. Я — БРЮС."',
        ],
        "services": {
            "web_dev":    "🌐 Веб-разработка",
            "design":     "🎨 UI/UX Дизайн",
            "branding":   "🦇 Айдентика бренда",
            "seo":        "📡 SEO и маркетинг",
            "mobile":     "📱 Мобильное приложение",
            "consulting": "🕵️ Стратегический консалтинг",
        },
    },
    "uz": {
        "welcome": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "_Soyalarga xush kelibsiz, {name}._\n\n"
            "Biz zulmatda ishlaymiz, brendingiz yorug'likda porlashi uchun. "
            "Gotham tomlaridan raqamli mukammallik cho'qqilariga.\n\n"
            "Bu kecha nima kerak?"
        ),
        "btn_order":    "🦇 Xizmat buyurtma qilish",
        "btn_services": "📋 Xizmatlarimiz",
        "btn_about":    "🏙️ Bruce Agency haqida",
        "btn_order_now":"🦇 Buyurtma berish",
        "btn_back":     "◀ Orqaga",
        "btn_hq":       "🏠 Bosh sahifaga",
        "services_title": "*🦇 Bruce Agency arsenali:*\n\n",
        "services_footer": "\n_Har bir piksel soyada yaratilgan, har bir kod satri bumerang kabi._",
        "about": (
            "*🦇 BRUCE | Digital Agency*\n\n"
            "Biz brendingiz loyiq bo'lgan raqamli qo'riqchilarimiz.\n\n"
            "Raqobat bozorining zulmatida tug'ilgan, ijod alangasida toblanган. "
            "Bruce Agency o'rtamiyonalikdan qo'rquvni uyg'otadigan raqamli yechimlar yaratadi.\n\n"
            "📍 Soyalardan ishlaymiz\n"
            "⚡ Javob vaqti: Betmobildan tezroq\n"
            "🎯 Missiya: Brendingizning to'liq ustunligi\n\n"
            "_{quote}_"
        ),
        "choose_service": (
            "*🦇 Qurolni tanlang:*\n\n"
            "_Kerakli xizmatni tanlang. Bruce qolganini soyalardan hal qiladi._"
        ),
        "service_selected": "*{name} — Tanlandi* ✅\n\n_Endi Alfred-ga tafsilotlarni ayting..._\n\nLoyihangizni tasvirlab bering: nima kerak, tasavvuringiz, talablar?",
        "ask_budget": "*🦇 Alfred yozib oldi.*\n\nBudjetingiz qancha?\n\n_Masalan: $500–1000, $2000+, moslashuvchan_",
        "ask_contact": "*🦇 Budjet qabul qilindi.*\n\nBruce siz bilan qanday bog'lansin?\n\n_Telefon, email yoki Telegram username_",
        "order_done": (
            "*🦇 Bref qabul qilindi — Buyurtma #{sid}*\n\n"
            "_Bat-signal yoqildi. Bruce allaqachon ishda._\n\n"
            "Xizmat: {service}\nBudjet: {budget}\n\n"
            "Siz bilan bog'lanamiz: *{contact}*\n"
            "Javob vaqti: 24 soat ichida.\n\n"
            "_{quote}_"
        ),
        "cancelled": "_Hatto Batman ham ba'zan chekinadi. Buyurtma bekor qilindi._\n\nQaytish uchun /start yozing.",
        "quotes": [
            '"Men kimligim emas, nima qilishim meni belgilaydi."',
            '"Nima uchun yiqilamiz? O\'rnimizdan turishni o\'rganish uchun."',
            '"Tong oldidan tun eng qorong\'i bo\'ladi."',
            '"Men — soyalar. Men — qasos. Men — BRUCE."',
        ],
        "services": {
            "web_dev":    "🌐 Veb-dasturlash",
            "design":     "🎨 UI/UX Dizayn",
            "branding":   "🦇 Brend identifikatsiyasi",
            "seo":        "📡 SEO va marketing",
            "mobile":     "📱 Mobil ilova",
            "consulting": "🕵️ Strategik konsalting",
        },
    },
}

def t(context, key):
    lang = context.user_data.get("lang", "en")
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, ""))

def get_quote(context):
    import random
    lang = context.user_data.get("lang", "en")
    return random.choice(TEXTS[lang]["quotes"])

def get_services(context):
    lang = context.user_data.get("lang", "en")
    return TEXTS[lang]["services"]

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def load_orders():
    try:
        with open(ORDERS_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_order(order):
    orders = load_orders()
    order_id = len(orders) + 1
    order["id"] = order_id
    orders.append(order)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)
    return order_id

async def notify_admin_bot(order: dict, order_id: int):
    sid = str(order_id).zfill(3)
    msg = (
        "BAT-SIGNAL RECEIVED! New Order #" + sid + "\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Client: " + order['user_name'] + " (" + order['username'] + ")\n"
        "User ID: " + str(order['user_id']) + "\n"
        "Language: " + order.get('lang', 'en').upper() + "\n"
        "Service: " + order['service_name'] + "\n"
        "Details: " + order['details'] + "\n"
        "Budget: " + order['budget'] + "\n"
        "Contact: " + order['contact'] + "\n"
        "Time: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Reply with /order " + str(order_id) + " to manage this mission."
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage",
                json={"chat_id": ADMIN_CHAT_ID, "text": msg}
            )
            if resp.status_code == 200:
                logger.info(f"Order #{order_id} forwarded to Admin Bot.")
            else:
                logger.error(f"Admin Bot notify failed [{resp.status_code}]: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to reach Admin Bot: {e}")

# ─── LANGUAGE SELECTION ────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang_uz")],
    ]
    await update.message.reply_text(
        "🦇 *BRUCE | Digital Agency*\n\n"
        "Choose your language / Выберите язык / Tilni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_LANG

async def lang_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    context.user_data["lang"] = lang

    user = query.from_user
    keyboard = [
        [InlineKeyboardButton(t(context, "btn_order"),    callback_data="order")],
        [InlineKeyboardButton(t(context, "btn_services"), callback_data="services")],
        [InlineKeyboardButton(t(context, "btn_about"),    callback_data="about")],
    ]
    await query.edit_message_text(
        t(context, "welcome").format(name=user.first_name),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── MAIN MENU ─────────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # language switch from main menu
    if data.startswith("lang_"):
        await lang_chosen(update, context)
        return

    back_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t(context, "btn_order_now"), callback_data="order"),
        InlineKeyboardButton(t(context, "btn_back"),      callback_data="back_start"),
    ]])

    if data == "services":
        text = t(context, "services_title")
        for name in get_services(context).values():
            emoji, label = name.split(" ", 1)
            text += f"{emoji} *{label}*\n"
        text += t(context, "services_footer")
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb)

    elif data == "about":
        about_text = t(context, "about").replace("{quote}", get_quote(context))
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=back_kb)

    elif data == "back_start":
        user = query.from_user
        keyboard = [
            [InlineKeyboardButton(t(context, "btn_order"),    callback_data="order")],
            [InlineKeyboardButton(t(context, "btn_services"), callback_data="services")],
            [InlineKeyboardButton(t(context, "btn_about"),    callback_data="about")],
        ]
        await query.edit_message_text(
            t(context, "welcome").format(name=user.first_name),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "order":
        services = get_services(context)
        keyboard = [[InlineKeyboardButton(name, callback_data=f"svc_{key}")]
                    for key, name in services.items()]
        keyboard.append([InlineKeyboardButton(t(context, "btn_back"), callback_data="back_start")])
        await query.edit_message_text(
            t(context, "choose_service"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSING_SERVICE

async def service_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("svc_", "")
    services = get_services(context)
    service_name = services.get(key, key)
    context.user_data["service"] = key
    context.user_data["service_name"] = service_name
    await query.edit_message_text(
        t(context, "service_selected").format(name=service_name),
        parse_mode="Markdown"
    )
    return ENTERING_DETAILS

async def got_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text
    await update.message.reply_text(t(context, "ask_budget"), parse_mode="Markdown")
    return ENTERING_BUDGET

async def got_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text(t(context, "ask_contact"), parse_mode="Markdown")
    return ENTERING_CONTACT

async def got_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["contact"] = update.message.text

    order = {
        "timestamp":    datetime.now().isoformat(),
        "user_id":      user.id,
        "user_name":    user.full_name,
        "username":     f"@{user.username}" if user.username else "No username",
        "lang":         context.user_data.get("lang", "en"),
        "service":      context.user_data.get("service"),
        "service_name": context.user_data.get("service_name"),
        "details":      context.user_data.get("details"),
        "budget":       context.user_data.get("budget"),
        "contact":      context.user_data.get("contact"),
        "status":       "new",
    }

    order_id = save_order(order)  # id is now set inside save_order
    await notify_admin_bot(order, order_id)

    confirmation = t(context, "order_done").format(
        sid=str(order_id).zfill(3),
        service=order["service_name"],
        budget=order["budget"],
        contact=order["contact"],
        quote=get_quote(context),
    )
    await update.message.reply_text(
        confirmation,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t(context, "btn_hq"), callback_data="back_start")
        ]])
    )
    lang = context.user_data.get("lang", "en")  # save language before clearing
    context.user_data.clear()
    context.user_data["lang"] = lang             # restore it after
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t(context, "cancelled"), parse_mode="Markdown")
    lang = context.user_data.get("lang", "en")
    context.user_data.clear()
    context.user_data["lang"] = lang
    return ConversationHandler.END

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(lang_chosen,     pattern="^lang_"),
            CallbackQueryHandler(button_handler,  pattern="^order$"),
            CallbackQueryHandler(service_chosen,  pattern="^svc_"),
        ],
        states={
            CHOOSING_LANG:    [CallbackQueryHandler(lang_chosen,    pattern="^lang_")],
            CHOOSING_SERVICE: [
                CallbackQueryHandler(service_chosen, pattern="^svc_"),
                CallbackQueryHandler(button_handler, pattern="^order$"),
            ],
            ENTERING_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_details)],
            ENTERING_BUDGET:  [MessageHandler(filters.TEXT & ~filters.COMMAND, got_budget)],
            ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🦇 Bruce Agency Bot is online. Gotham is protected.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()