"""
Test data factories using Faker and factory_boy.

Generates realistic test data for User, TarotSpread, and Payment models.
Uses Russian locale for user-facing data.
"""

import random
from datetime import date, datetime, time, timedelta, timezone

import factory
from faker import Faker

# Russian locale for realistic test data
fake = Faker("ru_RU")

# All zodiac signs
ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

# Spread types
SPREAD_TYPES = ["three_card", "celtic_cross"]

# Major and minor arcana card IDs
MAJOR_ARCANA = [f"ar{i:02d}" for i in range(22)]
MINOR_ARCANA = [
    f"{suit}{num:02d}"
    for suit in ["wa", "cu", "sw", "pe"]  # wands, cups, swords, pentacles
    for num in range(1, 15)
]
ALL_CARDS = MAJOR_ARCANA + MINOR_ARCANA


class UserFactory(factory.Factory):
    """
    Factory for generating User model data.

    Usage:
        user_data = UserFactory()
        user_data = UserFactory(is_premium=True)
        user_data = UserFactory(zodiac_sign="leo")
    """

    class Meta:
        model = dict

    telegram_id = factory.LazyFunction(lambda: random.randint(100000000, 999999999))
    username = factory.LazyFunction(lambda: f"test_{fake.user_name()}")

    # Birth data
    birth_date = factory.LazyFunction(
        lambda: fake.date_of_birth(minimum_age=18, maximum_age=80)
    )
    zodiac_sign = factory.LazyFunction(lambda: random.choice(ZODIAC_SIGNS))

    # Birth location for natal chart
    birth_time = factory.LazyFunction(
        lambda: time(random.randint(0, 23), random.randint(0, 59))
    )
    birth_city = factory.LazyFunction(lambda: fake.city())
    birth_lat = factory.LazyFunction(lambda: float(fake.latitude()))
    birth_lon = factory.LazyFunction(lambda: float(fake.longitude()))

    # Notification settings
    timezone = "Europe/Moscow"
    notification_hour = factory.LazyFunction(lambda: random.randint(6, 22))
    notifications_enabled = factory.LazyFunction(lambda: random.choice([True, False]))

    # Premium status - default non-premium
    is_premium = False
    premium_until = None
    daily_spread_limit = 1

    # Tarot counters
    tarot_spread_count = 0
    spread_reset_date = factory.LazyFunction(lambda: date.today())

    @classmethod
    def premium(cls, **kwargs):
        """Create a premium user with active subscription."""
        return cls(
            is_premium=True,
            premium_until=datetime.now(timezone.utc) + timedelta(days=30),
            daily_spread_limit=20,
            **kwargs
        )

    @classmethod
    def with_zodiac(cls, sign: str, **kwargs):
        """Create a user with specific zodiac sign."""
        return cls(zodiac_sign=sign, **kwargs)


class TarotSpreadFactory(factory.Factory):
    """
    Factory for generating TarotSpread model data.

    Usage:
        spread_data = TarotSpreadFactory()
        spread_data = TarotSpreadFactory(spread_type="celtic_cross")
    """

    class Meta:
        model = dict

    user_id = factory.LazyFunction(lambda: random.randint(1, 1000))
    spread_type = factory.LazyFunction(lambda: random.choice(SPREAD_TYPES))
    question = factory.LazyFunction(lambda: fake.sentence(nb_words=10))

    @factory.lazy_attribute
    def cards(self):
        """Generate cards based on spread type."""
        if self.spread_type == "three_card":
            num_cards = 3
        else:  # celtic_cross
            num_cards = 10

        selected_cards = random.sample(ALL_CARDS, num_cards)
        return [
            {
                "card_id": card,
                "reversed": random.choice([True, False]),
                "position": i + 1
            }
            for i, card in enumerate(selected_cards)
        ]

    interpretation = factory.LazyFunction(
        lambda: fake.paragraph(nb_sentences=5)
    )
    created_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
    )


class PaymentFactory(factory.Factory):
    """
    Factory for generating Payment model data.

    Usage:
        payment_data = PaymentFactory()
        payment_data = PaymentFactory(status="succeeded", amount=29900)
    """

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"pay_{fake.uuid4()[:12]}")
    user_id = factory.LazyFunction(lambda: random.randint(1, 1000))
    subscription_id = None

    # Amount in kopeks (299.00 RUB = 29900 kopeks)
    amount = 29900
    currency = "RUB"
    status = "pending"

    is_recurring = False
    description = factory.LazyFunction(
        lambda: random.choice([
            "Премиум подписка на 1 месяц",
            "Детальный натальный гороскоп",
            "Premium subscription - 1 month",
        ])
    )

    webhook_processed = False
    created_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc)
    )
    paid_at = None

    @classmethod
    def succeeded(cls, **kwargs):
        """Create a successful payment."""
        return cls(
            status="succeeded",
            webhook_processed=True,
            paid_at=datetime.now(timezone.utc),
            **kwargs
        )

    @classmethod
    def for_subscription(cls, subscription_id: int, **kwargs):
        """Create a payment linked to a subscription."""
        return cls(
            subscription_id=subscription_id,
            description="Премиум подписка на 1 месяц",
            **kwargs
        )
