import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Цены подписок (в копейках)
PRICES = {
    '1_day': 10000,      # 100 рублей
    '1_month': 100000,   # 1000 рублей
    '6_months': 500000,  # 5000 рублей
    '1_year': 900000     # 9000 рублей
}

# Временные интервалы
MORNING_SLOT = "10:00-14:00"
EVENING_SLOT = "18:00-20:00"
ORDER_DEADLINE = 10  # время до 10:00