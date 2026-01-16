import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatMember
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import json
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# 🎬 TELEGRAM KINO BOT - PROFESSIONAL VERSION
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

ADMIN_ID = 8381500320  # 🔴 O'Z TELEGRAM ID RAQAMINGIZNI YOZING!
BOT_TOKEN = "8266825005:AAEj2OcohuiT2dbj09BQQbW6hUKUZXN5j-4"  # 🔴 BOT TOKENINGIZNI YOZING!

# 📢 MAJBURIY KANALLAR (o'z kanallaringizni qo'shing)
REQUIRED_CHANNELS = [
    "@kinolar873",  # 🔴 Kanal 1 username
    "@uzmovi873",  # 🔴 Kanal 2 username
    # Qo'shimcha kanallar qo'shish mumkin
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


# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GLOBAL O'ZGARUVCHILAR
# ═══════════════════════════════════════════════════════════════════════════

movies = load_data()
stats = load_stats()
blocked_users = load_blocked_users()


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
            "✅ Obuna bo'lganingizdan so'ng *\"Obuna bo'ldim\"* tugmasini bosing!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ ADMIN KLAVIATURALARI
# ═══════════════════════════════════════════════════════════════════════════

def get_admin_keyboard():
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
        [InlineKeyboardButton("❌ Yopish", callback_data='close')]
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
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Obunani tekshirish
    if user_id != ADMIN_ID:
        if not check_subscription(update, context):
            return

    # Statistikani yangilash
    stats['total_users'].add(user_id)
    save_stats(stats)

    if user_id == ADMIN_ID:
        update.message.reply_text(
            "👑 *ADMIN PANELI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 *BOT FUNKSIYALARI:*\n"
            "• Kino raqamini yuboring → Kino yuklanadi\n"
            "• /admin → Admin panel ochiladi\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 *HOZIRGI STATISTIKA:*\n\n"
            f"👥 Foydalanuvchilar: *{len(stats['total_users'])}* ta\n"
            f"🎬 Yuborilgan kinolar: *{stats.get('movies_sent', 0)}* ta\n"
            f"📥 Jami so'rovlar: *{stats.get('total_requests', 0)}* ta\n"
            f"🎞 Bazadagi kinolar: *{len(movies)}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
        )


# ═══════════════════════════════════════════════════════════════════════════
# 👨‍💼 ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════

def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        update.message.reply_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    update.message.reply_text(
        "🎛 *ADMIN PANEL*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kerakli bo'limni tanlang:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
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
                parse_mode=ParseMode.MARKDOWN
            )
        return

    if user_id != ADMIN_ID:
        query.edit_message_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
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
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            movie_list = "📋 *BARCHA KINOLAR*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for num, data in sorted(movies.items(), key=lambda x: int(x[0])):
                movie_list += f"🎬 *{num}.* {data['name']}\n"

            movie_list += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n📊 Jami: *{len(movies)}* ta kino"
            query.edit_message_text(
                movie_list,
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STATISTIKA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'statistics':
        stats_text = (
            "📊 *BOT STATISTIKASI*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Jami foydalanuvchilar: *{len(stats['total_users'])}* ta\n"
            f"🚫 Bloklangan: *{len(blocked_users)}* ta\n"
            f"🎬 Yuborilgan kinolar: *{stats.get('movies_sent', 0)}* ta\n"
            f"📥 Jami so'rovlar: *{stats.get('total_requests', 0)}* ta\n"
            f"🎞 Bazada kinolar: *{len(movies)}* ta\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        query.edit_message_text(
            stats_text,
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # REKLAMA YUBORISH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif query.data == 'send_ad':
        context.user_data['action'] = 'send_ad'
        query.edit_message_text(
            "📢 *REKLAMA YUBORISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Reklama xabaringizni yuboring:\n\n"
            "✅ Qo'llab-quvvatlanadigan formatlar:\n"
            "• 📝 Text\n"
            "• 🖼 Rasm\n"
            "• 🎥 Video\n"
            "• 📄 Hujjat\n\n"
            "💡 Xabaringizni yuboring va barcha foydalanuvchilarga avtomatik yuboriladi!",
            parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == 'block_user':
        context.user_data['action'] = 'block_user'
        query.edit_message_text(
            "🚫 *FOYDALANUVCHI BLOKLASH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Bloklash uchun foydalanuvchi ID raqamini yuboring:\n\n"
            "💡 ID raqamni qanday topish mumkin?\n"
            "Foydalanuvchi botga /start yuborganda sizga xabar keladi.",
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == 'unblock_user':
        context.user_data['action'] = 'unblock_user'
        query.edit_message_text(
            "✅ *BLOKDAN CHIQARISH*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Blokdan chiqarish uchun foydalanuvchi ID raqamini yuboring:",
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == 'blocked_list':
        if not blocked_users:
            query.edit_message_text(
                "📋 *BLOKLANGAN FOYDALANUVCHILAR*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ Hozircha bloklangan foydalanuvchilar yo'q",
                reply_markup=get_block_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            blocked_list = "📋 *BLOKLANGAN FOYDALANUVCHILAR*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for user_id in blocked_users:
                blocked_list += f"🚫 `{user_id}`\n"
            blocked_list += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n📊 Jami: *{len(blocked_users)}* ta"
            query.edit_message_text(
                blocked_list,
                reply_markup=get_block_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )

    elif query.data == 'back_to_admin':
        query.edit_message_text(
            "🎛 *ADMIN PANEL*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Kerakli bo'limni tanlang:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == 'close':
        query.edit_message_text(
            "✅ *YOPILDI*\n\n"
            "Admin panel yopildi.",
            parse_mode=ParseMode.MARKDOWN
        )


# ═══════════════════════════════════════════════════════════════════════════
# 💬 XABAR HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Bloklangan foydalanuvchilarni tekshirish
    if user_id in blocked_users:
        update.message.reply_text(
            "🚫 *BLOKLANGAN!*\n\n"
            "❌ Siz ushbu botdan foydalanish huquqidan mahrum qilindingiz.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Obunani tekshirish
    if user_id != ADMIN_ID:
        if not check_subscription(update, context):
            return

    # Statistikani yangilash
    stats['total_users'].add(user_id)
    stats['total_requests'] = stats.get('total_requests', 0) + 1
    save_stats(stats)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ADMIN ACTIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if user_id == ADMIN_ID and 'action' in context.user_data:
        action = context.user_data['action']

        # KINO RAQAMINI QO'SHISH
        if action == 'add_movie_number':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat raqam yuboring!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            context.user_data['movie_number'] = text
            context.user_data['action'] = 'add_movie_name'
            update.message.reply_text(
                f"✅ *KINO RAQAMI:* `{text}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 Endi kino nomini yuboring:",
                parse_mode=ParseMode.MARKDOWN
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
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # KINO O'CHIRISH
        elif action == 'delete_movie_number':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat raqam yuboring!",
                    parse_mode=ParseMode.MARKDOWN
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
                    reply_markup=get_admin_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text(
                    f"❌ *TOPILMADI!*\n\n"
                    f"`{text}` raqamli kino bazada mavjud emas!",
                    reply_markup=get_admin_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                del context.user_data['action']
            return

        # FOYDALANUVCHI BLOKLASH
        elif action == 'block_user':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            block_id = int(text)
            if block_id == ADMIN_ID:
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "O'zingizni bloklay olmaysiz!",
                    parse_mode=ParseMode.MARKDOWN
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
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # BLOKDAN CHIQARISH
        elif action == 'unblock_user':
            if not text.isdigit():
                update.message.reply_text(
                    "❌ *XATO!*\n\n"
                    "Iltimos, faqat ID raqam yuboring!",
                    parse_mode=ParseMode.MARKDOWN
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
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                update.message.reply_text(
                    "❌ *TOPILMADI!*\n\n"
                    f"`{unblock_id}` bloklangan foydalanuvchilar ro'yxatida yo'q!",
                    reply_markup=get_block_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                del context.user_data['action']
            return

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KINO SO'RASH (ODDIY FOYDALANUVCHI)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if text.isdigit():
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
                    parse_mode=ParseMode.MARKDOWN
                )
                stats['movies_sent'] = stats.get('movies_sent', 0) + 1
                save_stats(stats)
            except Exception as e:
                logger.error(f"Video yuborishda xato: {e}")
                update.message.reply_text(
                    "❌ *XATOLIK!*\n\n"
                    "Kino yuborishda xatolik yuz berdi!\n\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text(
                f"❌ *TOPILMADI!*\n\n"
                f"`{movie_num}` raqamli kino bazada mavjud emas!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 Bazada *{len(movies)}* ta kino mavjud",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        update.message.reply_text(
            "❌ *NOTO'G'RI FORMAT!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 Iltimos, kino raqamini yuboring!\n\n"
            "💡 Misol: `1`, `2`, `3` va hokazo...",
            parse_mode=ParseMode.MARKDOWN
        )


# ═══════════════════════════════════════════════════════════════════════════
# 🎥 VIDEO HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_video(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        update.message.reply_text(
            "❌ *RUXSAT RAD ETILDI!*\n\n"
            "Sizda admin huquqi yo'q!",
            parse_mode=ParseMode.MARKDOWN
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
            reply_markup=get_admin_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text(
            "❌ *XATO!*\n\n"
            "Avval /admin orqali \"➕ Kino qo'shish\" tugmasini bosing!",
            parse_mode=ParseMode.MARKDOWN
        )


# ═══════════════════════════════════════════════════════════════════════════
# 📢 REKLAMA HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_ad_content(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    if 'action' not in context.user_data or context.user_data['action'] != 'send_ad':
        return

    message = update.message
    success = 0
    failed = 0

    update.message.reply_text(
        "⏳ *REKLAMA YUBORILMOQDA...*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Iltimos, kuting...",
        parse_mode=ParseMode.MARKDOWN
    )

    for user in stats['total_users']:
        try:
            if message.text:
                context.bot.send_message(
                    chat_id=user,
                    text=f"📢 *REKLAMA*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{message.text}",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif message.photo:
                context.bot.send_photo(
                    chat_id=user,
                    photo=message.photo[-1].file_id,
                    caption=f"📢 *REKLAMA*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{message.caption or ''}",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif message.video:
                context.bot.send_video(
                    chat_id=user,
                    video=message.video.file_id,
                    caption=f"📢 *REKLAMA*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{message.caption or ''}",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif message.document:
                context.bot.send_document(
                    chat_id=user,
                    document=message.document.file_id,
                    caption=f"📢 *REKLAMA*\n\n━━━━━━━━━━━━━━━━━━━━━\n\n{message.caption or ''}",
                    parse_mode=ParseMode.MARKDOWN
                )
            success += 1
        except Exception as e:
            logger.error(f"Reklamani yuborishda xato {user}: {e}")
            failed += 1

    del context.user_data['action']

    update.message.reply_text(
        "✅ *REKLAMA YUBORILDI!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Muvaffaqiyatli: *{success}* ta\n"
        f"❌ Xato: *{failed}* ta\n\n"
        "━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
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
            parse_mode=ParseMode.MARKDOWN
        )


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 ASOSIY FUNKSIYA
# ═══════════════════════════════════════════════════════════════════════════

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlerlar
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.video, handle_video))
    dp.add_handler(MessageHandler(Filters.photo | Filters.document, handle_ad_content))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)

    # Botni ishga tushirish
    logger.info("=" * 60)
    logger.info("🎬 TELEGRAM KINO BOT ISHGA TUSHDI!")
    logger.info("=" * 60)
    logger.info(f"📊 Bazada {len(movies)} ta kino mavjud")
    logger.info(f"👥 Jami foydalanuvchilar: {len(stats['total_users'])}")
    logger.info(f"🚫 Bloklangan: {len(blocked_users)}")
    logger.info("=" * 60)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()