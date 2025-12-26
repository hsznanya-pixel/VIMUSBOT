import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler, ConversationHandler
)
import config
from database import db
from keyboards import main_menu, subscription_menu, confirm_order

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
ADDRESS, COMMENT, CONFIRM = range(3)

async def start(update: Update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.full_name)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n"
        f"Я бот для заказа услуги вывоза мусора.\n"
        f"Для заказа вам нужна активная подписка.",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text == '📦 Заказать вывоз мусора':
        await order_mess(update, context)
    elif text == '💳 Моя подписка':
        await my_subscription(update, context)
    elif text == 'ℹ️ О услуге':
        await about(update, context)
    elif text == '👤 Контакты':
        await contacts(update, context)

async def order_mess(update: Update, context):
    """Начало оформления заказа"""
    user_id = db.get_user_id(update.effective_user.id)
    
    # Проверяем подписку
    subscription = db.check_subscription(user_id)
    if not subscription:
        await update.message.reply_text(
            "❌ У вас нет активной подписки.\n"
            "Для заказа вывоза мусора необходимо оформить подписку.\n"
            "Используйте команду /subscribe"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Введите адрес вывоза мусора:"
    )
    return ADDRESS

async def get_address(update: Update, context):
    """Получение адреса"""
    context.user_data['address'] = update.message.text
    await update.message.reply_text("✏️ Введите комментарий к заказу (или 'нет'):")
    return COMMENT

async def get_comment(update: Update, context):
    """Получение комментария"""
    context.user_data['comment'] = update.message.text
    
    # Определяем время вывоза
    now = datetime.now().time()
    if now < time(10, 0):
        pickup_time = config.MORNING_SLOT
    else:
        pickup_time = config.EVENING_SLOT
    
    context.user_data['pickup_time'] = pickup_time
    
    order_text = (
        f"📋 Ваш заказ:\n"
        f"📍 Адрес: {context.user_data['address']}\n"
        f"📅 Время вывоза: {pickup_time}\n"
        f"📝 Комментарий: {context.user_data['comment']}\n\n"
        f"Подтвердить заказ?"
    )
    
    await update.message.reply_text(order_text, reply_markup=confirm_order())
    return CONFIRM

async def confirm_order_callback(update: Update, context):
    """Подтверждение заказа"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm_order':
        user_id = db.get_user_id(update.effective_user.id)
        
        # Создаем заказ в БД
        order_id = db.create_order(
            user_id,
            context.user_data['address'],
            context.user_data['comment'],
            context.user_data['pickup_time']
        )
        
        # Отправляем админу
        user = update.effective_user
        admin_text = (
            f"🚨 НОВЫЙ ЗАКАЗ #{order_id}\n"
            f"👤 Клиент: {user.full_name} (@{user.username})\n"
            f"📞 ID: {user.id}\n"
            f"📍 Адрес: {context.user_data['address']}\n"
            f"⏰ Время: {context.user_data['pickup_time']}\n"
            f"📝 Комментарий: {context.user_data['comment']}"
        )
        
        await context.bot.send_message(config.ADMIN_ID, admin_text)
        
        await query.edit_message_text(
            f"✅ Заказ #{order_id} принят!\n"
            f"Вывоз мусора будет в интервал: {context.user_data['pickup_time']}\n\n"
            f"Спасибо за заказ! ♻️"
        )
    else:
        await query.edit_message_text("❌ Заказ отменен")
    
    return ConversationHandler.END

async def subscribe_command(update: Update, context):
    """Оформление подписки"""
    await update.message.reply_text(
        "💰 Выберите тип подписки:",
        reply_markup=subscription_menu()
    )

async def subscription_callback(update: Update, context):
    """Обработка выбора подписки"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('sub_'):
        # Здесь должна быть интеграция с платежной системой
        # Для примера просто активируем подписку
        
        sub_types = {
            'sub_1_day': (1, 10000),
            'sub_1_month': (30, 100000),
            'sub_6_months': (180, 500000),
            'sub_1_year': (365, 900000)
        }
        
        days, price = sub_types[query.data]
        user_id = db.get_user_id(update.effective_user.id)
        
        db.add_subscription(user_id, query.data, price, days)
        
        await query.edit_message_text(
            f"✅ Подписка оформлена на {days} дней!\n"
            f"Теперь вы можете заказывать вывоз мусора."
        )
    else:
        await query.edit_message_text("❌ Операция отменена")

async def my_subscription(update: Update, context):
    """Проверка подписки"""
    user_id = db.get_user_id(update.effective_user.id)
    subscription = db.check_subscription(user_id)
    
    if subscription:
        end_date = subscription[5]  # end_date
        sub_type = subscription[2]  # type
        
        await update.message.reply_text(
            f"✅ У вас активная подписка!\n"
            f"Тип: {sub_type}\n"
            f"Действует до: {end_date}"
        )
    else:
        await update.message.reply_text(
            "❌ У вас нет активной подписки.\n"
            "Используйте /subscribe для оформления"
        )

async def about(update: Update, context):
    """Информация об услуге"""
    text = (
        "♻️ Услуга вывоза мусора\n\n"
        "📅 Режим работы:\n"
        "• Заявки до 10:00 - вывоз с 10:00 до 14:00\n"
        "• Заявки после 10:00 - вывоз с 18:00 до 20:00\n\n"
        "💰 Подписка дает право на:\n"
        "• Регулярный вывоз мусора\n"
        "• Приоритетное обслуживание\n"
        "• Отслеживание статуса заявок"
    )
    await update.message.reply_text(text)

async def contacts(update: Update, context):
    """Контакты"""
    text = (
        "📞 Контакты:\n\n"
        "Телефон: +7 (XXX) XXX-XX-XX\n"
        "Email: info@musor.ru\n"
        "Адрес: г. Москва, ул. Примерная, д. 1\n\n"
        "⏰ Часы работы:\n"
        "Пн-Пт: 8:00-20:00\n"
        "Сб: 9:00-18:00\n"
        "Вс: выходной"
    )
    await update.message.reply_text(text)

async def cancel(update: Update, context):
    """Отмена операции"""
    await update.message.reply_text("❌ Операция отменена", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ConversationHandler для заказа
    order_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['📦 Заказать вывоз мусора']), order_mess)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            CONFIRM: [CallbackQueryHandler(confirm_order_callback)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("mysub", my_subscription))
    application.add_handler(order_conv)
    application.add_handler(CallbackQueryHandler(subscription_callback, pattern='^sub_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()