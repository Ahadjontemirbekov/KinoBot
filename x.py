import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler
from telegram.ext import Filters
import json
import os
from datetime import datetime
import time

# ═══════════════════════════════════════════════════════════════════════════
# 🎬 TELEGRAM KINO BOT - MULTI ADMIN PROFESSIONAL VERSION
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ KONFIGURATSIYA
# ═══════════════════════════════════════════════════════════════════════════

DATA_FILE = 'movies_data.json'
STATS_FILE = 'stats.json'
BLOCKED_FILE = 'blocked_users.json'
ADMINS_FILE = 'admins.json'

MAIN_ADMIN_ID = 8381500320  # 🔴 ASOSIY ADMIN ID (faqat siz!)
BOT_TOKEN = "8266825005:AAEj2OcohuiT2dbj09BQQbW6hUKUZXN5j-4"

# 📢 MAJBURIY KANALLAR
REQUIRED_CHANNELS = [
    "@kinolar873",
    "@uzmovi873",
]


# ═══════════════════════════════════════════════════════════════════════════
# 💾 MA'LUMOTLAR BILAN ISHLASH
# ═══════════════════════════════════════════════════════════════════════════

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            if isinstance(stats.get('total_users'), list):
                stats['total_users'] = set(stats['total_users'])
            return stats
    return {'total_users': set(), 'total_requests': 0, 'movies_sent': 0}


def save_stats(stats):
    stats_copy = stats.copy()
    stats_copy['total_users'] = list(stats_copy['total_users'])
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats_copy, f, ensure_ascii=False, indent=2)


def load_blocked_users():
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_blocked_users(blocked):
    with open(BLOCKED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(blocked), f, ensure_ascii=False, indent=2)


def load_admins():
    """Adminlar ro'yxatini yuklash"""
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return {MAIN_ADMIN_ID}  # Asosiy admin doim ro'yxatda


def save_admins(admins):
    """Adminlar ro'yxatini saqlash"""
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(admins), f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GLOBAL O'ZGARUVCHILAR
# ═══════════════════════════════════════════════════════════════════════════

movies = load_data()
stats = load_stats()
blocked_users = load_blocked_users()
admins = load_admins()


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 ADMIN TEKSHIRISH FUNKSIYALARI
# ═══════════════════════════════════════════════════════════════════════════

def is_admin(user_id):
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in admins


def is_main_admin(user_id):
    """Foydalanuvchi asosiy admin ekanligini tekshirish"""
    return user_id == MAIN_ADMIN_ID


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 OBUNA TEKSHIRISH
# ═══════════════════════════════════════════════════════════════════════════

def check_subscription(update: Update, context: CallbackContext) -> bool:
    """Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshiradi"""
    user_id = update.effective_user.id

    not_subscribed = []

    for channel in REQUIRED_CHANNELS:
        try:
            member = context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel)
        except Exception as e:
            logger.error(f"Kanal tekshirishda xatolik {channel}: {e}")
            not_subscribed.append(channel)

    if not_subscribed:
        keyboard = []
        for channel in REQUIRED_CHANNELS:
            channel_name = channel.replace('@', '')
            keyboard.append([InlineKeyboardButton(
                f"📢 {channel_name}",
                url=f"https://t.me/{channel_name}"
            )])
        keyboard.append([InlineKeyboardButton("✅ Obuna bo'ldim", callback_data='check_subscription')])

        update.effective_message.reply_text(
            "⚠️ *DIQQAT!*\n\n"
            "🎬 Botdan foydalanish uchun quyidagi *kanallarga obuna* bo'lishingiz kerak:\n\n"
            "👇 *Kanallarga o'ting va \"Obuna bo'lish\" tugmasini bosing*\n\n"
            "✅ Obuna bo'lganingizdan so'ng *\"Obuna bo'ldim\"* tugmasini bosing!"
            ,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ ADMIN KLAVIATURALARI
# ═══════════════════════════════════════════════════════════════════════════

def get_admin_keyboard(user_id):
    """Admin panelidagi tugmalar - foydalanuvchi huquqiga qarab"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Kino qo'shish", callback_data='add_movie'),
            InlineKeyboardButton("🗑 Kino o'chirish", callback_data='delete_movie')
        ],
        [
            InlineKeyboardButton("📋 Barcha kinolar", callback_data='list_movies'),
            InlineKeyboardButton("📊 Statistika", callback_data='statistics')
        ],
        [
            InlineKeyboardButton("📢 Reklama yuborish", callback_data='send_ad'),
            InlineKeyboardButton("🚫 Bloklash", callback_data='block_menu')
        ],
    ]

    # Faqat asosiy admin uchun admin boshqaruv tugmasi
    if is_main_admin(user_id):
        keyboard.append([InlineKeyboardButton("👥 Admin boshqaruvi", callback_data='admin_management')])

    keyboard.append([InlineKeyboardButton("❌ Yopish", callback_data='close')])

    return InlineKeyboardMarkup(keyboard)


def get_admin_management_keyboard():
    """Admin boshqaruv paneli"""
    keyboard = [
        [InlineKeyboardButton("➕ Admin qo'shish", callback_data='add_admin')],
        [InlineKeyboardButton("➖ Admin o'chirish", callback_data='remove_admin')],
        [InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data='admin_list')],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='back_to_admin')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_block_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚫 Foydalanuvchi bloklash", callback_data='block_user')],
        [InlineKeyboardButton("✅ Blokdan chiqarish", callback_data='unblock_user')],
        [InlineKeyboardButton("📋 Bloklangan foydalanuvchilar", callback_data='blocked_list')],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='back_to_admin')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 /START KOMANDASI
# ═══════════════════════════════════════════════════════════════════════════

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    # Bloklangan foydalanuvchilarni tekshirish
    if user_id in blocked_users:
        update.message.reply_text(
            "🚫 *BLOKLANGAN!*\n\n"
            "❌ Siz ushbu botdan foydalanish huquqidan *mahrum qilindingiz*.\n\n"
            "📞 Murojaat uchun admin bilan bog'laning.",
            
        )
        return

    # Obunani tekshirish (adminlar uchun emas)
    if not is_admin(user_id):
        if not check_subscription(update, context):
            return

    # Statistikani yangilash
    stats['total_users'].add(user_id)
    save_stats(stats)

    if is_admin(user_id):
        admin_type = "ASOSIY ADMIN" if is_main_admin(user_id) else "ADMIN"
        update.message.reply_text(
            f"👑 *{admin_type} PANELI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 *BOT FUNKSIYALARI:*\n"
            "• Kino raqamini yuboring → Kino yuklanadi\n"
            "• /admin → Admin panel ochiladi\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 *HOZIRGI STATISTIKA:*\n\n"
            f"👥 Foydalanuvchilar: *{len(stats['total_users'])}* ta\n"
            f"👨‍💼 Adminlar: *{len(admins)}* ta\n"
            f"🎬 Yuborilgan kinolar: *{stats.get('movies_sent', 0)}* ta\n"
            f"📥 Jami so'rovlar: *{stats.get('total_requests', 0)}* ta\n"
            f"🎞 Bazadagi kinolar: *{len(movies)}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            
        )
    else:
        update.message.reply_text(
            f"👋 *Assalomu alaykum, {user.first_name}!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 *KINO BOTIGA XUSH KELIBSIZ!*\n\n"
            "📝 *Foydalanish qoidalari:*\n"
            "• Kino raqamini yuboring\n"
            "• Kino avtomatik yuklanadi\n\n"
            "💡 *Misol:* `1`, `2`, `3` va hokazo...\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Botda *{len(movies)}* ta kino mavjud\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# 👨‍💼 ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════

def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            
        )
        return

    admin_type = "ASOSIY ADMIN" if is_main_admin(user_id) else "ADMIN"

    update.message.reply_text(
        f"🎛 *{admin_type} PANEL*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kerakli bo'limni tanlang:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=get_admin_keyboard(user_id),
        
    )


# ═══════════════════════════════════════════════════════════════════════════
# 🔘 CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    # Obuna tekshirish
    if query.data == 'check_subscription':
        if check_subscription(update, context):
            query.edit_message_text(
                "✅ *MUVAFFAQIYATLI!*\n\n"
                "🎉 Siz barcha kanallarga obuna bo'ldingiz!\n\n"
                "🎬 Endi botdan foydalanishingiz mumkin.\n\n"
                "📝 Kino raqamini yuboring va kino yuklanadi!",
                
            )
        return

    if not is_admin(user_id):
        query.edit_message_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            
        )
        return

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KINO QO'SHISH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if query.data == 'add_movie':
        context.user_data['action'] = 'add_movie_number'
        query.edit_message_text(
            "➕ *KINO QO'SHISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Kino raqamini yuboring:\n\n"
            "💡 Misol: `1`, `2`, `3` va hokazo",
            
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KINO O'CHIRISH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'delete_movie':
        context.user_data['action'] = 'delete_movie_number'
        query.edit_message_text(
            "🗑 *KINO O'CHIRISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 O'chirmoqchi bo'lgan kino raqamini yuboring:",
            
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KINOLAR RO'YXATI
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'list_movies':
        if not movies:
            query.edit_message_text(
                "📋 *KINOLAR RO'YXATI*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ Hozircha kinolar yo'q",
                reply_markup=get_admin_keyboard(user_id),
                
            )
        else:
            movie_list = "📋 *BARCHA KINOLAR*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for num, data in sorted(movies.items(), key=lambda x: int(x[0])):
                movie_list += f"🎬 *{num}.* {data['name']}\n"

            movie_list += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n📊 Jami: *{len(movies)}* ta kino"
            query.edit_message_text(
                movie_list,
                reply_markup=get_admin_keyboard(user_id),
                
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATISTIKA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'statistics':
        stats_text = (
            "📊 *BOT STATISTIKASI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Jami foydalanuvchilar: *{len(stats['total_users'])}* ta\n"
            f"👨‍💼 Adminlar: *{len(admins)}* ta\n"
            f"🚫 Bloklangan: *{len(blocked_users)}* ta\n"
            f"🎬 Yuborilgan kinolar: *{stats.get('movies_sent', 0)}* ta\n"
            f"📥 Jami so'rovlar: *{stats.get('total_requests', 0)}* ta\n"
            f"🎞 Bazada kinolar: *{len(movies)}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        query.edit_message_text(
            stats_text,
            reply_markup=get_admin_keyboard(user_id),
            
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # REKLAMA YUBORISH - YANGILANGAN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'send_ad':
        context.user_data['action'] = 'send_ad'
        query.edit_message_text(
            "📢 *REKLAMA YUBORISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 *Reklamangizni yuboring!*\n\n"
            "✅ *Qo'llab-quvvatlanadigan formatlar:*\n\n"
            "• 📝 Matn xabar\n"
            "• 🖼 Rasm (caption bilan yoki bo'lmasdan)\n"
            "• 🎥 Video (caption bilan yoki bo'lmasdan)\n"
            "• 📄 Hujjat (caption bilan yoki bo'lmasdan)\n"
            "• 🎵 Audio\n"
            "• 🎤 Voice xabar\n"
            "• 📹 Video xabar\n"
            "• 📍 Joylashuv\n"
            "• 📞 Kontakt\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 *Qanday ishlaydi?*\n"
            "Siz qanday xabar yuborsangiz, aynan shunday xabar barcha foydalanuvchilarga yuboriladi!\n\n"
            "🚀 *Xabaringizni yuboring...*",
            
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BLOKLASH MENYUSI
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'block_menu':
        query.edit_message_text(
            "🚫 *BLOKLASH MENYUSI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Kerakli amalni tanlang:",
            reply_markup=get_block_keyboard(),
            
        )

    elif query.data == 'block_user':
        context.user_data['action'] = 'block_user'
        query.edit_message_text(
            "🚫 *FOYDALANUVCHI BLOKLASH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Bloklash uchun foydalanuvchi ID raqamini yuboring:\n\n"
            "💡 ID raqamni qanday topish mumkin?\n"
            "Foydalanuvchi botga /start yuborganda sizga xabar keladi.",
            
        )

    elif query.data == 'unblock_user':
        context.user_data['action'] = 'unblock_user'
        query.edit_message_text(
            "✅ *BLOKDAN CHIQARISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Blokdan chiqarish uchun foydalanuvchi ID raqamini yuboring:",
            
        )

    elif query.data == 'blocked_list':
        if not blocked_users:
            query.edit_message_text(
                "📋 *BLOKLANGAN FOYDALANUVCHILAR*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ Hozircha bloklangan foydalanuvchilar yo'q",
                reply_markup=get_block_keyboard(),
                
            )
        else:
            blocked_list = "📋 *BLOKLANGAN FOYDALANUVCHILAR*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for uid in blocked_users:
                blocked_list += f"🚫 `{uid}`\n"
            blocked_list += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n📊 Jami: *{len(blocked_users)}* ta"
            query.edit_message_text(
                blocked_list,
                reply_markup=get_block_keyboard(),
                
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ADMIN BOSHQARUVI - FAQAT ASOSIY ADMIN UCHUN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'admin_management':
        if not is_main_admin(user_id):
            query.answer("❌ Faqat asosiy admin uchun!", show_alert=True)
            return

        query.edit_message_text(
            "👥 *ADMIN BOSHQARUVI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Kerakli amalni tanlang:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_management_keyboard(),
            
        )

    elif query.data == 'add_admin':
        if not is_main_admin(user_id):
            query.answer("❌ Faqat asosiy admin uchun!", show_alert=True)
            return

        context.user_data['action'] = 'add_admin'
        query.edit_message_text(
            "➕ *ADMIN QO'SHISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Yangi admin qilmoqchi bo'lgan foydalanuvchining ID raqamini yuboring:\n\n"
            "💡 Foydalanuvchi botga /start yuborganida uning ID raqami ko'rinadi.",
            
        )

    elif query.data == 'remove_admin':
        if not is_main_admin(user_id):
            query.answer("❌ Faqat asosiy admin uchun!", show_alert=True)
            return

        context.user_data['action'] = 'remove_admin'
        query.edit_message_text(
            "➖ *ADMIN O'CHIRISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 O'chirmoqchi bo'lgan admin ID raqamini yuboring:",
            
        )

    elif query.data == 'admin_list':
        if not is_main_admin(user_id):
            query.answer("❌ Faqat asosiy admin uchun!", show_alert=True)
            return

        admin_list_text = "👥 *ADMINLAR RO'YXATI*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for admin_id in admins:
            if admin_id == MAIN_ADMIN_ID:
                admin_list_text += f"👑 `{admin_id}` - Asosiy Admin\n"
            else:
                admin_list_text += f"👨‍💼 `{admin_id}`\n"
        admin_list_text += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n📊 Jami: *{len(admins)}* ta"
        query.edit_message_text(
            admin_list_text,
            reply_markup=get_admin_management_keyboard(),
            
        )

    elif query.data == 'back_to_admin':
        query.edit_message_text(
            "🎛 *ADMIN PANEL*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Kerakli bo'limni tanlang:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_keyboard(user_id),
            
        )

    elif query.data == 'close':
        query.edit_message_text(
            "✅ *YOPILDI*\n\n"
            "Admin panel yopildi.",
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# 💬 XABAR HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    # Bloklangan foydalanuvchilarni tekshirish
    if user_id in blocked_users:
        update.message.reply_text(
            "🚫 *BLOKLANGAN!*\n\n"
            "❌ Siz ushbu botdan foydalanish huquqidan mahrum qilindingiz.",
            
        )
        return

    # Obunani tekshirish (adminlar uchun emas)
    if not is_admin(user_id):
        if not check_subscription(update, context):
            return

    # Statistikani yangilash
    stats['total_users'].add(user_id)
    stats['total_requests'] = stats.get('total_requests', 0) + 1
    save_stats(stats)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ADMIN ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_admin(user_id) and 'action' in context.user_data:
        action = context.user_data['action']

        # KINO RAQAMINI QO'SHISH
        if action == 'add_movie_number':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat raqam yuboring!",
                    
                )
                return

            context.user_data['movie_number'] = text
            context.user_data['action'] = 'add_movie_name'
            update.message.reply_text(
                f"✅ *KINO RAQAMI:* `{text}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 Endi kino nomini yuboring:",
                
            )
            return

        # KINO NOMINI QO'SHISH
        elif action == 'add_movie_name':
            context.user_data['movie_name'] = text
            context.user_data['action'] = 'add_movie_video'
            update.message.reply_text(
                f"✅ *KINO NOMI:* {text}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎥 Endi kino video faylini yuboring:",
                
            )
            return

        # KINO O'CHIRISH
        elif action == 'delete_movie_number':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat raqam yuboring!",
                    
                )
                return

            if text in movies:
                movie_name = movies[text]['name']
                del movies[text]
                save_data(movies)
                del context.user_data['action']
                update.message.reply_text(
                    "✅ *KINO O'CHIRILDI!*\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎬 Raqam: `{text}`\n"
                    f"📝 Nomi: {movie_name}",
                    reply_markup=get_admin_keyboard(user_id),
                    
                )
            else:
                update.message.reply_text(
                    f"❌ *TOPILMADI!*\n\n"
                    f"`{text}` raqamli kino bazada mavjud emas!",
                    reply_markup=get_admin_keyboard(user_id),
                    
                )
                del context.user_data['action']
            return

        # FOYDALANUVCHI BLOKLASH
        elif action == 'block_user':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    
                )
                return

            block_id = int(text)

            # Asosiy adminni bloklash mumkin emas
            if block_id == MAIN_ADMIN_ID:
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Asosiy adminni bloklash mumkin emas!",
                    
                )
                return

            # Adminlarni bloklash mumkin emas
            if block_id in admins:
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Adminni bloklash mumkin emas!\n\n"
                    "Avval admin huquqini olib tashlang.",
                    
                )
                return

            blocked_users.add(block_id)
            save_blocked_users(blocked_users)
            del context.user_data['action']
            update.message.reply_text(
                "✅ *BLOKLANDI!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🚫 Foydalanuvchi ID: `{block_id}`\n\n"
                "Ushbu foydalanuvchi endi botdan foydalana olmaydi.",
                reply_markup=get_block_keyboard(),
                
            )
            return

        # BLOKDAN CHIQARISH
        elif action == 'unblock_user':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    
                )
                return

            unblock_id = int(text)
            if unblock_id in blocked_users:
                blocked_users.remove(unblock_id)
                save_blocked_users(blocked_users)
                del context.user_data['action']
                update.message.reply_text(
                    "✅ *BLOKDAN CHIQARILDI!*\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"✅ Foydalanuvchi ID: `{unblock_id}`\n\n"
                    "Ushbu foydalanuvchi yana botdan foydalanishi mumkin.",
                    reply_markup=get_block_keyboard(),
                    
                )
            else:
                update.message.reply_text(
                    "❌ *TOPILMADI!*\n\n"
                    f"`{unblock_id}` bloklangan foydalanuvchilar ro'yxatida yo'q!",
                    reply_markup=get_block_keyboard(),
                    
                )
                del context.user_data['action']
            return

        # ADMIN QO'SHISH - FAQAT ASOSIY ADMIN
        elif action == 'add_admin':
            if not is_main_admin(user_id):
                update.message.reply_text(
                    "❌ *RUXSAT RAD ETILDI!*\n\n"
                    "Faqat asosiy admin boshqa adminlar qo'sha oladi!",
                    
                )
                return

            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    
                )
                return

            new_admin_id = int(text)

            if new_admin_id in admins:
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    f"`{new_admin_id}` allaqachon admin!",
                    
                )
                return

            admins.add(new_admin_id)
            save_admins(admins)
            del context.user_data['action']

            update.message.reply_text(
                "✅ *ADMIN QO'SHILDI!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👨‍💼 Yangi admin ID: `{new_admin_id}`\n\n"
                "Ushbu foydalanuvchi endi admin huquqlariga ega!",
                reply_markup=get_admin_management_keyboard(),
                
            )

            # Yangi adminni xabardor qilish
            try:
                context.bot.send_message(
                    chat_id=new_admin_id,
                    text="🎉 *TABRIKLAYMIZ!*\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━\n\n"
                         "👑 Siz admin huquqiga ega bo'ldingiz!\n\n"
                         "📝 /admin - Admin panel\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━",
                    
                )
            except:
                pass
            return

        # ADMIN O'CHIRISH - FAQAT ASOSIY ADMIN
        elif action == 'remove_admin':
            if not is_main_admin(user_id):
                update.message.reply_text(
                    "❌ *RUXSAT RAD ETILDI!*\n\n"
                    "Faqat asosiy admin boshqa adminlarni o'chira oladi!",
                    
                )
                return

            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    
                )
                return

            remove_admin_id = int(text)

            # Asosiy adminni o'chirish mumkin emas
            if remove_admin_id == MAIN_ADMIN_ID:
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Asosiy adminni o'chirish mumkin emas!",
                    
                )
                return

            if remove_admin_id not in admins:
                update.message.reply_text(
                    "❌ *TOPILMADI!*\n\n"
                    f"`{remove_admin_id}` adminlar ro'yxatida yo'q!",
                    
                )
                return

            admins.remove(remove_admin_id)
            save_admins(admins)
            del context.user_data['action']

            update.message.reply_text(
                "✅ *ADMIN O'CHIRILDI!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"➖ Admin ID: `{remove_admin_id}`\n\n"
                "Ushbu foydalanuvchi endi oddiy foydalanuvchi!",
                reply_markup=get_admin_management_keyboard(),
                
            )

            # O'chirilgan adminni xabardor qilish
            try:
                context.bot.send_message(
                    chat_id=remove_admin_id,
                    text="⚠️ *XABARDORLIK*\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━\n\n"
                         "Sizning admin huquqingiz olib tashlandi!\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━",
                    
                )
            except:
                pass
            return

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KINO SO'RASH (BARCHA FOYDALANUVCHILAR)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if text and text.isdigit():
        movie_num = text
        if movie_num in movies:
            movie_data = movies[movie_num]
            try:
                update.message.reply_video(
                    video=movie_data['file_id'],
                    caption=(
                        f"🎬 *{movie_data['name']}*\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"📊 Kino #{movie_num}\n"
                        f"📅 {movie_data.get('added_date', 'N/A')}"
                    ),
                    
                )
                stats['movies_sent'] = stats.get('movies_sent', 0) + 1
                save_stats(stats)
            except Exception as e:
                logger.error(f"Video yuborishda xato: {e}")
                update.message.reply_text(
                    "❌ *XATOLIK!*\n\n"
                    "Kino yuborishda xatolik yuz berdi!\n\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    
                )
        else:
            update.message.reply_text(
                f"❌ *TOPILMADI!*\n\n"
                f"`{movie_num}` raqamli kino bazada mavjud emas!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 Bazada *{len(movies)}* ta kino mavjud",
                
            )
    elif text:
        update.message.reply_text(
            "❌ *NOTO'G'RI FORMAT!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Iltimos, kino raqamini yuboring!\n\n"
            "💡 Misol: `1`, `2`, `3` va hokazo...",
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# 🎥 VIDEO HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_video(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        update.message.reply_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            
        )
        return

    if 'action' in context.user_data and context.user_data['action'] == 'add_movie_video':
        video = update.message.video
        movie_num = context.user_data.get('movie_number')
        movie_name = context.user_data.get('movie_name')

        movies[movie_num] = {
            'name': movie_name,
            'file_id': video.file_id,
            'added_date': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        save_data(movies)

        del context.user_data['action']
        del context.user_data['movie_number']
        del context.user_data['movie_name']

        update.message.reply_text(
            "✅ *KINO QO'SHILDI!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎬 Raqam: `{movie_num}`\n"
            f"📝 Nomi: {movie_name}\n"
            f"📅 {movies[movie_num]['added_date']}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_keyboard(user_id),
            
        )
    else:
        update.message.reply_text(
            "❌ *XATO!*\n\n"
            "Avval /admin orqali \"➕ Kino qo'shish\" tugmasini bosing!",
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# 📢 UNIVERSAL REKLAMA HANDLER - HAR QANDAY FORMATDAGI XABARLAR
# ═══════════════════════════════════════════════════════════════════════════

def handle_broadcast(update: Update, context: CallbackContext):
    """Har qanday formatdagi xabarni barcha foydalanuvchilarga yuborish"""
    user_id = update.effective_user.id

    # Admin tekshirish
    if not is_admin(user_id):
        return

    # Reklama rejimini tekshirish
    if 'action' not in context.user_data or context.user_data['action'] != 'send_ad':
        return

    message = update.message
    success = 0
    failed = 0

    # Yuborilayotganini xabar qilish
    status_msg = update.message.reply_text(
        "⏳ *REKLAMA YUBORILMOQDA...*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Jami foydalanuvchilar: *{len(stats['total_users'])}* ta\n\n"
        "Iltimos, kuting...",
        
    )

    # Barcha foydalanuvchilarga yuborish
    for user in stats['total_users']:
        if user in blocked_users:
            failed += 1
            continue

        try:
            # MATN XABAR
            if message.text:
                context.bot.send_message(
                    chat_id=user,
                    text=message.text
                     if '*' in message.text or '_' in message.text else None
                )

            # RASM
            elif message.photo:
                context.bot.send_photo(
                    chat_id=user,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            # VIDEO
            elif message.video:
                context.bot.send_video(
                    chat_id=user,
                    video=message.video.file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            # HUJJAT
            elif message.document:
                context.bot.send_document(
                    chat_id=user,
                    document=message.document.file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            # AUDIO
            elif message.audio:
                context.bot.send_audio(
                    chat_id=user,
                    audio=message.audio.file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            # VOICE
            elif message.voice:
                context.bot.send_voice(
                    chat_id=user,
                    voice=message.voice.file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            # VIDEO NOTE (Aylana video)
            elif message.video_note:
                context.bot.send_video_note(
                    chat_id=user,
                    video_note=message.video_note.file_id
                )

            # STICKER
            elif message.sticker:
                context.bot.send_sticker(
                    chat_id=user,
                    sticker=message.sticker.file_id
                )

            # JOYLASHUV
            elif message.location:
                context.bot.send_location(
                    chat_id=user,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude
                )

            # KONTAKT
            elif message.contact:
                context.bot.send_contact(
                    chat_id=user,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name
                )

            # ANIMATION (GIF)
            elif message.animation:
                context.bot.send_animation(
                    chat_id=user,
                    animation=message.animation.file_id,
                    caption=message.caption
                     if message.caption and (
                                '*' in message.caption or '_' in message.caption) else None
                )

            success += 1
            time.sleep(0.05)  # Flood kontroli uchun

        except Exception as e:
            logger.error(f"Reklamani yuborishda xato {user}: {e}")
            failed += 1

    # Actionni o'chirish
    del context.user_data['action']

    # Yakuniy natija
    try:
        status_msg.edit_text(
            "✅ *REKLAMA YUBORILDI!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Muvaffaqiyatli: *{success}* ta\n"
            f"❌ Xato: *{failed}* ta\n"
            f"👥 Jami: *{len(stats['total_users'])}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_keyboard(user_id),
            
        )
    except:
        update.message.reply_text(
            "✅ *REKLAMA YUBORILDI!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Muvaffaqiyatli: *{success}* ta\n"
            f"❌ Xato: *{failed}* ta\n"
            f"👥 Jami: *{len(stats['total_users'])}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_keyboard(user_id),
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# ⚠️ XATOLIK HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Xatolik: {context.error}")
    if update and update.effective_message:
        update.effective_message.reply_text(
            "❌ *XATOLIK YUZ BERDI!*\n\n"
            "Iltimos, qaytadan urinib ko'ring!\n\n"
            "Agar muammo davom etsa, admin bilan bog'laning.",
            
        )


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 ASOSIY FUNKSIYA
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Botni ishga tushiruvchi asosiy funksiya"""
    try:
        logger.info("🚀 Bot ishga tushmoqda...")

        # Updater va Dispatcher yaratish
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KOMANDA HANDLERLAR
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("admin", admin_panel))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # CALLBACK QUERY HANDLER
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_handler(CallbackQueryHandler(button_callback))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # VIDEO HANDLER - Kino qo'shish uchun
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_handler(MessageHandler(Filters.video, handle_video))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # UNIVERSAL BROADCAST HANDLER - Har qanday formatdagi xabar
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_handler(MessageHandler(
            Filters.photo | Filters.document | Filters.audio |
            Filters.voice | Filters.video_note | Filters.sticker |
            Filters.location | Filters.contact | Filters.animation,
            handle_broadcast
        ))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # MATN XABAR HANDLER - Eng oxirida qo'shiladi
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # XATOLIK HANDLER
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dp.add_error_handler(error_handler)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BOTNI ISHGA TUSHIRISH
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"👑 Asosiy Admin ID: {MAIN_ADMIN_ID}")
        logger.info(f"👨‍💼 Jami adminlar: {len(admins)} ta")
        logger.info(f"👥 Jami foydalanuvchilar: {len(stats['total_users'])} ta")
        logger.info(f"🎬 Bazadagi kinolar: {len(movies)} ta")
        logger.info(f"🚫 Bloklangan: {len(blocked_users)} ta")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("🔄 Bot xabarlarni kutmoqda...")

        updater.bot.set_my_commands([
            BotCommand("start", "Botni boshlash"),
            BotCommand("admin", "Adminlar uchun"),
        ])

        # Polling rejimida ishga tushirish
        updater.start_polling()
        updater.idle()

    except Exception as e:
        logger.error(f"❌ Botni ishga tushirishda xatolik: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# 🎯 DASTURNI ISHGA TUSHIRISH NUQTASI
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    try:
        print("\n" + "═" * 80)
        print("🎬 TELEGRAM KINO BOT - MULTI ADMIN PROFESSIONAL VERSION")
        print("═" * 80)
        print("🚀 Bot ishga tushmoqda...")
        print("=" * 80 + "\n")

        main()

    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("⏹ Bot to'xtatildi!")
        print("=" * 80 + "\n")
        logger.info("⏹ Bot foydalanuvchi tomonidan to'xtatildi")

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ KRITIK XATOLIK: {e}")
        print("=" * 80 + "\n")
        logger.critical(f"❌ Kritik xatolik: {e}")
        raise



