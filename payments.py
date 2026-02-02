import uuid
from datetime import datetime, timedelta
import aiohttp
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, SUBSCRIPTION_PRICES

class PaymentProcessor:
    def __init__(self):
        self.base_url = "https://api.yookassa.ru/v3"
        self.auth = aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    
    async def create_payment(self, amount, description, user_id):
        payment_id = str(uuid.uuid4())
        
        # Для демо - эмулируем успешную оплату
        # В реальном проекте используйте API ЮKassa:
        """
        async with aiohttp.ClientSession(auth=self.auth) as session:
            payload = {
                "amount": {"value": amount, "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/your_bot"
                },
                "capture": True,
                "description": description
            }
            
            async with session.post(
                f"{self.base_url}/payments",
                json=payload,
                headers={"Idempotence-Key": payment_id}
            ) as response:
                return await response.json()
        """
        
        # Демо-режим: сразу возвращаем успех
        return {
            "id": payment_id,
            "status": "succeeded",
            "paid": True,
            "amount": {"value": amount}
        }
    
    def get_subscription_days(self, plan):
        """Конвертируем план в дни"""
        plans = {
            "1 день": 1,
            "1 месяц": 30,
            "6 месяцев": 180,
            "12 месяцев": 365
        }
        return plans.get(plan, 0)