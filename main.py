import telebot
from telebot import types
from datetime import datetime
import config

bot = telebot.TeleBot(config.BOT_TOKEN)

laundry_queue = {
    "4": [],
    "6": []
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    button_floor4 = types.InlineKeyboardButton("🏢 4 поверх", callback_data="floor4")
    button_floor6 = types.InlineKeyboardButton("🏢 6 поверх", callback_data="floor6")
    button_view_queue = types.InlineKeyboardButton("📝 Подивитись чергу", callback_data="view_queue")
    markup.add(button_floor4, button_floor6, button_view_queue)

    bot.send_message(message.chat.id, "👋 Привіт! Це бот для бронювання пральних машин. Оберіть дію:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['floor4', 'floor6'])
def choose_floor(call):
    floor = call.data[-1]
    markup = types.InlineKeyboardMarkup()
    button_machine1 = types.InlineKeyboardButton("▫️Пралка №1", callback_data=f"machine1_{floor}")
    button_machine2 = types.InlineKeyboardButton("▫️Пралка №2", callback_data=f"machine2_{floor}")
    markup.add(button_machine1, button_machine2)

    bot.send_message(call.message.chat.id, f"📌Ви обрали {floor}-й поверх. Виберіть пральну машину:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('machine'))
def choose_machine(call):
    data = call.data.split('_')
    machine = data[0][-1]
    floor = data[1]
    bot.send_message(call.message.chat.id, f"📌Ви обрали {machine}-у пральну машину на {floor}-му поверсі. Введіть номер своєї кімнати.")
    bot.register_next_step_handler(call.message, process_room, floor=floor, machine=machine)

def process_room(message, floor, machine):
    room = message.text
    username = message.from_user.username
    time_now = datetime.now().strftime("%d-%m-%Y %H:%M")

    laundry_queue[floor].append({
        "room": room,
        "username": username,
        "time": time_now,
        "machine": machine
    })

    markup = types.InlineKeyboardMarkup()
    button_view_queue = types.InlineKeyboardButton("📝 Подивитись чергу", callback_data="view_queue")
    button_remove = types.InlineKeyboardButton("❌ Видалити себе з черги", callback_data=f"remove_{floor}")
    markup.add(button_view_queue, button_remove)

    bot.send_message(message.chat.id,
                     f"✅Вас додано до черги на {floor}-му поверсі, Пралка №{machine}. Ваш нікнейм: @{username}, кімната: {room}, 🕒час: {time_now}",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'view_queue')
def show_queue(call):
    queue_text = ""

    for floor, queue in laundry_queue.items():
        if queue:
            queue_text += f"\n⬇️ Черга на {floor}-му поверсі:\n"
            queue_text += "\n".join(
                [f"{idx + 1}. ▫️Кімната: {entry['room']}, @{entry['username']}, Пралка №{entry['machine']}, 🕒Час: {entry['time']}"
                 for idx, entry in enumerate(queue)])
        else:
            queue_text += f"\n⬇️ Черга на {floor}-му поверсі порожня.\n"

    bot.send_message(call.message.chat.id, queue_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
def remove_from_queue(call):
    floor = call.data.split('_')[1]
    username = call.from_user.username

    for entry in laundry_queue[floor]:
        if entry['username'] == username:
            laundry_queue[floor].remove(entry)
            bot.send_message(call.message.chat.id, "❌ Вас видалено з черги.")
            return

    bot.send_message(call.message.chat.id, "⚠️ Вас немає у черзі.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def mark_done(call):
    floor = call.data.split('_')[1]
    username = call.from_user.username

    bot.send_message(call.message.chat.id, "⚠️ Вас немає у черзі.")

bot.polling()
