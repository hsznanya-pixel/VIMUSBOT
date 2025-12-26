from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def main_menu():
    keyboard = [
        ['📦 Заказать вывоз мусора'],
        ['💳 Моя подписка', 'ℹ️ О услуге'],
        ['👤 Контакты']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def subscription_menu():
    keyboard = [
        [
            InlineKeyboardButton("1 день - 100 руб", callback_data='sub_1_day'),
            InlineKeyboardButton("1 месяц - 1000 руб", callback_data='sub_1_month')
        ],
        [
            InlineKeyboardButton("6 месяцев - 5000 руб", callback_data='sub_6_months'),
            InlineKeyboardButton("1 год - 9000 руб", callback_data='sub_1_year')
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_order():
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data='confirm_order'),
            InlineKeyboardButton("❌ Отменить", callback_data='cancel_order')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)