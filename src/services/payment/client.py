"""Async wrapper for YooKassa SDK."""
import asyncio
import uuid

import structlog
from yookassa import Configuration, Payment as YooPayment

from src.config import settings

logger = structlog.get_logger()


# Configure YooKassa on module load
def _configure_yookassa():
    if settings.yookassa_shop_id and settings.yookassa_secret_key:
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key


_configure_yookassa()


async def create_payment(
    user_id: int,
    amount: str,
    description: str,
    save_payment_method: bool = False,
    metadata: dict | None = None,
) -> dict:
    """
    Create payment with redirect confirmation.

    Args:
        user_id: Telegram user ID for metadata
        amount: Amount as string (e.g., "299.00")
        description: Payment description
        save_payment_method: Whether to save card for recurring
        metadata: Additional metadata

    Returns:
        YooKassa Payment object as dict
    """
    idempotency_key = str(uuid.uuid4())

    payment_data = {
        "amount": {"value": amount, "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": settings.yookassa_return_url,
        },
        "capture": True,
        "save_payment_method": save_payment_method,
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            **(metadata or {}),
        },
    }

    def _create():
        return YooPayment.create(payment_data, idempotency_key)

    await logger.ainfo(
        "Creating payment",
        user_id=user_id,
        amount=amount,
        save_method=save_payment_method,
    )

    result = await asyncio.to_thread(_create)
    return result


async def create_recurring_payment(
    payment_method_id: str,
    user_id: int,
    subscription_id: int,
    amount: str,
    description: str,
) -> dict:
    """
    Create recurring payment using saved payment method.

    Args:
        payment_method_id: Saved payment method ID
        user_id: User ID
        subscription_id: Subscription ID
        amount: Amount as string
        description: Payment description

    Returns:
        YooKassa Payment object as dict
    """
    idempotency_key = str(uuid.uuid4())

    payment_data = {
        "amount": {"value": amount, "currency": "RUB"},
        "capture": True,
        "payment_method_id": payment_method_id,
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "subscription_id": str(subscription_id),
            "type": "recurring",
        },
    }

    def _create():
        return YooPayment.create(payment_data, idempotency_key)

    await logger.ainfo(
        "Creating recurring payment",
        user_id=user_id,
        subscription_id=subscription_id,
        amount=amount,
    )

    result = await asyncio.to_thread(_create)
    return result


async def cancel_recurring(payment_method_id: str) -> bool:
    """
    Cancel recurring payments by invalidating payment method.

    Note: YooKassa doesn't have explicit cancel - we just stop using
    the payment_method_id and clear it from our DB.

    Returns:
        True (always succeeds - we just stop using it)
    """
    await logger.ainfo("Recurring cancelled", payment_method_id=payment_method_id[:8])
    return True
