import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import threading
import time
import signal
import sys

TOKEN = '7772958291:AAFNsMM94FrPpa3VDalbCdzu_DX1euSk_WE'
bot = telebot.TeleBot(TOKEN)

CHANNELS = [
    '@+LReJflzWOR00MDU6',
    '@+brkwd5YZY8tiNWVi',
    '@+wm0r3qnxLcA4M2U6',
    '@+nvM6U9acy7g4ZDUy',
    '@+hbceh-QB_HE1MjAy'
]

CHANNEL_LINKS = [
    'https://t.me/+LReJflzWOR00MDU6',
    'https://t.me/+brkwd5YZY8tiNWVi',
    'https://t.me/+wm0r3qnxLcA4M2U6',
    'https://t.me/+nvM6U9acy7g4ZDUy',
    'https://t.me/+hbceh-QB_HE1MjAy'
]

CHANNEL_NAMES = [
    'КАНАЛ #1', 'КАНАЛ #2', 'КАНАЛ #3', 'КАНАЛ #4', 'КАНАЛ #5'
]

pending_users = {}
failed_once = {}
user_stars = {}
running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Остановка...")
    running = False
    bot.stop_polling()
    sys.exit(0)


def get_user_first_name(user):
    if user.first_name:
        return user.first_name
    if user.username:
        return user.username
    return "Друг"


def is_subscribed(user_id):
    for i, channel in enumerate(CHANNELS):
        try:
            time.sleep(0.3)
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                print(f"❌ Не подписан на {CHANNEL_NAMES[i]}")
                return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки {CHANNEL_NAMES[i]}: {e}")
            return None
    print(f"✅ Пользователь {user_id} подписан на все 5 каналов")
    return True


def send_delayed_stars(chat_id, user_id):
    if not running:
        return
    delay = 56 * 3600
    print(f"⏳ Звезды для {user_id} через {delay} секунд...")
    time.sleep(delay)
    if not running or user_id not in pending_users:
        return

    stars_amount = user_stars.get(user_id, 15)
    del pending_users[user_id]
    del user_stars[user_id]

    text = (
        f"🎁 **ПОДАРОК ГОТОВ!**\n\n"
        f"✨ **На твой счет зачисленно {stars_amount} звезд!**\n\n"
        f"⭐ **Твой баланс увеличен на {stars_amount} звезд**\n\n"
        "✅ Проверь свой профиль Telegram Stars!\n"
        "💎 Звезды готовы к использованию!"
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📱 Поделиться подарком", callback_data="share"))
    try:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        print(f"⚠️ Ошибка отправки звезд: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    if not running:
        return

    user_id = message.from_user.id
    failed_once.pop(user_id, None)
    pending_users.pop(user_id, None)
    user_stars.pop(user_id, None)

    first_name = get_user_first_name(message.from_user)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✨ 15 звезд", callback_data="stars_15"))
    markup.add(InlineKeyboardButton("⭐ 50 звезд", callback_data="stars_50"))
    markup.add(InlineKeyboardButton("🌟 150 звезд", callback_data="stars_150"))
    markup.add(InlineKeyboardButton("💎 300 звезд", callback_data="stars_300"))

    text = (
        f"👋 {first_name}, привет!\n\n"
        "Это бот для получения бесплатных звёзд в Telegram!\n\n"
        "🎁 Нажми на кнопку ниже, выбрав количество звёзд 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if not running:
        return

    user_id = call.from_user.id
    chat_id = call.message.chat.id
    first_name = get_user_first_name(call.from_user)

    bot.answer_callback_query(call.id)

    if call.data.startswith("stars_"):
        stars_amount = int(call.data.split("_")[1])
        user_stars[user_id] = stars_amount

        markup = InlineKeyboardMarkup()
        for name, link in zip(CHANNEL_NAMES, CHANNEL_LINKS):
            markup.row(InlineKeyboardButton(name, url=link))
        markup.add(InlineKeyboardButton("✅ ГОТОВО", callback_data="check_ready"))

        text = (
            f"✨ Отлично! Ты выбрал {stars_amount} звезд!\n\n"
            "Поддержи наших партнёров — благодаря им ты получишь подарок!\n\n"
            "📢 Вот ссылки на каналы (кнопки ниже ведут туда же):\n\n"
            f"🔗 КАНАЛ #1: {CHANNEL_LINKS[0]}\n"
            f"🔗 КАНАЛ #2: {CHANNEL_LINKS[1]}\n"
            f"🔗 КАНАЛ #3: {CHANNEL_LINKS[2]}\n"
            f"🔗 КАНАЛ #4: {CHANNEL_LINKS[3]}\n"
            f"🔗 КАНАЛ #5: {CHANNEL_LINKS[4]}\n\n"
            "⚠️ Если Телеграм выдал ошибку при переходе, подожди 3–5 секунд и попробуй снова.\n\n"
            f"✅ После этого нажми «ГОТОВО» чтобы получить свои {stars_amount} звезд! 👇"
        )

        bot.edit_message_text(
            text,
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            disable_web_page_preview=True
        )

    elif call.data == "check_ready":
        if failed_once.get(user_id):
            stars_amount = user_stars.get(user_id, 15)
            text = (
                f"✨ Отлично! Видим твою подписку на каналы.\n\n"
                f"⏳ Ожидай **56 часов** — за это время мы зачислим "
                f"{stars_amount} звезд на твой счет!\n\n"
                "Такое время ожидания, потому что сейчас много запросов."
            )
            bot.edit_message_text(
                text,
                chat_id,
                call.message.message_id,
                parse_mode='Markdown'
            )

            pending_users[user_id] = chat_id
            t = threading.Thread(target=send_delayed_stars, args=(chat_id, user_id))
            t.daemon = True
            t.start()
            return

        result = is_subscribed(user_id)

        if result is None or result is False:
            failed_once[user_id] = True

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 ПОДПИСАТЬСЯ", callback_data="get_stars_channels"))

            stars_amount = user_stars.get(user_id, 15)
            text = (
                f"{first_name}, упс... кажется мы не видим подписку на какой то из каналов"
            )

            bot.edit_message_text(
                text,
                chat_id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            return

        if result is True:
            stars_amount = user_stars.get(user_id, 15)
            text = (
                f"✨ Отлично! Видим твою подписку на каналы.\n\n"
                f"⏳ Ожидай **56 часов** — за это время мы зачислим "
                f"{stars_amount} звезд на твой счет!\n\n"
                "Такое время ожидания, потому что сейчас много запросов."
            )
            bot.edit_message_text(
                text,
                chat_id,
                call.message.message_id,
                parse_mode='Markdown'
            )

            pending_users[user_id] = chat_id
            t = threading.Thread(target=send_delayed_stars, args=(chat_id, user_id))
            t.daemon = True
            t.start()

    elif call.data == "get_stars_channels":
        stars_amount = user_stars.get(user_id, 15)
        markup = InlineKeyboardMarkup()
        for name, link in zip(CHANNEL_NAMES, CHANNEL_LINKS):
            markup.row(InlineKeyboardButton(name, url=link))
        markup.add(InlineKeyboardButton("✅ ГОТОВО", callback_data="check_ready"))

        text = (
            f"✨ Получи свои {stars_amount} звезд!\n\n"
            "Поддержи наших партнёров — благодаря им ты получишь подарок!\n\n"
            "📢 Вот ссылки на каналы (кнопки ниже ведут туда же):\n\n"
            f"🔗 КАНАЛ #1: {CHANNEL_LINKS[0]}\n"
            f"🔗 КАНАЛ #2: {CHANNEL_LINKS[1]}\n"
            f"🔗 КАНАЛ #3: {CHANNEL_LINKS[2]}\n"
            f"🔗 КАНАЛ #4: {CHANNEL_LINKS[3]}\n"
            f"🔗 КАНАЛ #5: {CHANNEL_LINKS[4]}\n\n"
            f"✅ После подписки нажми «ГОТОВО» чтобы получить {stars_amount} звезд!"
        )

        bot.edit_message_text(
            text,
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            disable_web_page_preview=True
        )

    elif call.data == "share":
        stars_amount = user_stars.get(user_id, 15)
        share_text = (
            f"Я получил {stars_amount} Telegram Stars!\n"
            "✨ Проверь и ты → @messsagemeterrobot"
        )
        try:
            bot.send_message(chat_id, share_text)
        except Exception as e:
            print(f"⚠️ Ошибка при отправке share-сообщения: {e}")


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 Бот Telegram Stars запущен!")
    print("📱 Тест: @messsagemeterrobot → /start")
    print(f"📢 Каналов: {len(CHANNELS)}")
    print("🛑 Ctrl+C для остановки")

    try:
        bot.infinity_polling(none_stop=True, interval=1, timeout=30)
    except KeyboardInterrupt:
        running = False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        running = False
        print("🔄 Бот остановлен")


if __name__ == '__main__':
    main()
