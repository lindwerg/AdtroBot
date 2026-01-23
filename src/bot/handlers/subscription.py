"""Subscription flow handlers."""

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.callbacks.subscription import SubscriptionCallback
from src.bot.keyboards.subscription import (
    get_cancel_confirmation_keyboard,
    get_plans_keyboard,
)
from src.db.models.user import User
from src.services.payment import (
    PaymentPlan,
    cancel_subscription,
    create_payment,
    get_user_subscription,
)
from src.services.payment.schemas import PLAN_PRICES_STR

logger = structlog.get_logger()

router = Router(name="subscription")

PREMIUM_FEATURES = """
Премиум-подписка открывает:

- 20 раскладов таро в день (вместо 1)
- Детальные гороскопы по сферам жизни
- Персональный прогноз на основе натальной карты
- Кельтский крест (расклад на 10 карт)
- Приоритетная поддержка
"""


async def show_plans(message: Message, session: AsyncSession) -> None:
    """Show subscription plans."""
    # Check if already premium
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.is_premium and user.premium_until:
        until_str = user.premium_until.strftime("%d.%m.%Y")
        await message.answer(
            f"У вас уже есть премиум-подписка до {until_str}\n\n"
            "Хотите продлить?"
        )

    await message.answer(
        PREMIUM_FEATURES + "\n\nВыберите тариф:",
        reply_markup=get_plans_keyboard(),
    )


@router.callback_query(SubscriptionCallback.filter(F.action == "plan"))
async def handle_plan_selection(
    callback: CallbackQuery,
    callback_data: SubscriptionCallback,
    session: AsyncSession,
) -> None:
    """Handle plan selection - create payment and send link."""
    await callback.answer()

    plan = PaymentPlan(callback_data.plan)
    price = PLAN_PRICES_STR[plan]

    plan_names = {
        PaymentPlan.MONTHLY: "Месячная подписка",
        PaymentPlan.YEARLY: "Годовая подписка",
    }

    try:
        # Create payment with method saving for recurring
        payment = await create_payment(
            user_id=callback.from_user.id,
            amount=price,
            description=f"AdtroBot {plan_names[plan]}",
            save_payment_method=True,
            metadata={
                "plan_type": plan.value,
            },
        )

        confirmation_url = payment.confirmation.confirmation_url

        await callback.message.edit_text(
            f"Отлично! Перейдите по ссылке для оплаты:\n\n"
            f"{confirmation_url}\n\n"
            f"После оплаты подписка активируется автоматически."
        )

    except Exception as e:
        # Log full exception details for debugging
        error_details = {
            "type": type(e).__name__,
            "message": str(e),
        }
        # YooKassa exceptions have additional attributes
        if hasattr(e, "code"):
            error_details["code"] = e.code
        if hasattr(e, "description"):
            error_details["description"] = e.description
        if hasattr(e, "parameter"):
            error_details["parameter"] = e.parameter
        if hasattr(e, "__dict__"):
            error_details["attrs"] = str(e.__dict__)

        await logger.aerror(
            "Payment creation failed",
            user_id=callback.from_user.id,
            plan=plan.value,
            amount=price,
            **error_details,
        )
        await callback.message.edit_text(
            "Произошла ошибка при создании платежа. "
            "Попробуйте позже или напишите в поддержку."
        )


@router.callback_query(SubscriptionCallback.filter(F.action == "cancel"))
async def handle_cancel_request(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show cancel confirmation with retention offer."""
    await callback.answer()

    subscription = await get_user_subscription(session, callback.from_user.id)

    if not subscription:
        await callback.message.edit_text("У вас нет активной подписки.")
        return

    until_str = subscription.current_period_end.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"Вы уверены, что хотите отменить подписку?\n\n"
        f"Доступ сохранится до {until_str}.\n\n"
        "Если передумаете — напишите нам, дадим скидку 20%!",
        reply_markup=get_cancel_confirmation_keyboard(),
    )


@router.callback_query(SubscriptionCallback.filter(F.action == "confirm_cancel"))
async def handle_confirm_cancel(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Confirm subscription cancellation."""
    await callback.answer()

    subscription = await cancel_subscription(session, callback.from_user.id)

    if subscription:
        until_str = subscription.current_period_end.strftime("%d.%m.%Y")
        await callback.message.edit_text(
            f"Подписка отменена.\n\n"
            f"Премиум-доступ сохранится до {until_str}.\n"
            f"Мы будем рады видеть вас снова!"
        )
    else:
        await callback.message.edit_text("Подписка не найдена.")


@router.callback_query(SubscriptionCallback.filter(F.action == "keep"))
async def handle_keep_subscription(callback: CallbackQuery) -> None:
    """User decided to keep subscription."""
    await callback.answer("Отлично! Рады, что остаётесь с нами!")
    await callback.message.edit_text(
        "Подписка сохранена. Спасибо, что вы с нами!"
    )
