import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import BOT_TOKEN, SUBSCRIPTION_PRICES
from database import Database
from payments import PaymentProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()
payment_processor = PaymentProcessor()

# Состояния (FSM)
class OrderStates(StatesGroup):
    waiting_for_order = State()

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    db.add_user(user_id, username, full_name)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("🛒 Купить подписку", callback_data="buy_subscription"),
        InlineKeyboardButton("🗑️ Заказать вынос", callback_data="order_trash"),
        InlineKeyboardButton("📊 Моя подписка", callback_data="my_subscription"),
        InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")
    ]
    keyboard.add(*buttons)
    
    welcome_text = (
        "👋 Добро пожаловать в сервис выноса мусора!\n\n"
        "✅ С подпиской вы можете заказывать вынос мусора:\n"
        "• До 10:00 - вывоз с 10:00 до 14:00\n"
        "• После 10:00 - вывоз с 18:00 до 20:00\n\n"
        "Выберите действие:"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)

# Покупка подписки
@dp.callback_query_handler(lambda c: c.data == 'buy_subscription')
async def show_subscriptions(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for plan, price in SUBSCRIPTION_PRICES.items():
        button_text = f"{plan} - {price} ₽"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"sub_{plan}"))
    
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
    
    await callback.message.edit_text(
        "🎯 Выберите подписку:",
        reply_markup=keyboard
    )
    await callback.answer()

# Обработка выбора подписки
@dp.callback_query_handler(lambda c: c.data.startswith('sub_'))
async def process_subscription(callback: types.CallbackQuery):
    plan = callback.data.replace('sub_', '')
    price = SUBSCRIPTION_PRICES.get(plan)
    
    if price:
        # Создаем платеж
        payment = await payment_processor.create_payment(
            amount=price,
            description=f"Подписка: {plan}",
            user_id=callback.from_user.id
        )
        
        if payment.get('paid'):
            # Обновляем подписку
            days = payment_processor.get_subscription_days(plan)
            db.update_subscription(callback.from_user.id, days)
            
            await callback.message.edit_text(
                f"✅ Оплата прошла успешно!\n"
                f"📅 Подписка '{plan}' активирована\n"
                f"💰 Стоимость: {price} ₽",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")
                )
            )
        else:
            # В реальном проекте здесь будет ссылка на оплату
            await callback.message.edit_text(
                f"Для оплаты подписки '{plan}' на {price} ₽:\n"
                f"1. Перейдите по ссылке (в реальном боте здесь будет ссылка ЮKassa)\n"
                f"2. После оплаты нажмите /start",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("⬅️ Назад", callback_data="buy_subscription")
                )
            )
    
    await callback.answer()

# Заказ выноса мусора
@dp.callback_query_handler(lambda c: c.data == 'order_trash')
async def order_trash(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if not db.check_subscription(user_id):
        await callback.message.edit_text(
            "❌ У вас нет активной подписки!\n"
            "Приобретите подписку для заказа выноса мусора.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🛒 Купить подписку", callback_data="buy_subscription"),
                InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
            )
        )
        return
    
    # Создаем заказ
    interval = db.add_order(user_id)
    
    await callback.message.edit_text(
        f"✅ Заказ создан!\n\n"
        f"📅 Время заказа: {datetime.now().strftime('%H:%M')}\n"
        f"🕐 Интервал вывоза: {interval}\n\n"
        f"Спасибо за заказ!",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")
        )
    )
    await callback.answer()

# Просмотр подписки
@dp.callback_query_handler(lambda c: c.data == 'my_subscription')
async def my_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    has_sub = db.check_subscription(user_id)
    
    if has_sub:
        text = "✅ У вас есть активная подписка!\nВы можете заказывать вынос мусора."
    else:
        text = "❌ У вас нет активной подписки.\nПриобретите подписку для доступа к услугам."
    
    keyboard = InlineKeyboardMarkup()
    if not has_sub:
        keyboard.add(InlineKeyboardButton("🛒 Купить подписку", callback_data="buy_subscription"))
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu"))
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# Просмотр заказов
@dp.callback_query_handler(lambda c: c.data == 'my_orders')
async def my_orders(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    orders = db.get_user_orders(user_id)
    
    if orders:
        orders_text = "📋 Ваши последние заказы:\n\n"
        for order in orders[:5]:  # Показываем 5 последних
            orders_text += f"📅 {order[2]}\n⏰ {order[3]}\nСтатус: {order[4]}\n\n"
    else:
        orders_text = "📭 У вас еще нет заказов."
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
    )
    
    await callback.message.edit_text(orders_text, reply_markup=keyboard)
    await callback.answer()

# Кнопка "Назад"
@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def back_to_menu(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

# Главная функция
async def main():
    logging.info("Бот запущен!")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())