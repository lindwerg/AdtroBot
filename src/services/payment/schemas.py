"""Payment schemas and constants."""
from enum import Enum


class PaymentPlan(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


# Prices in kopeks
PLAN_PRICES = {
    PaymentPlan.MONTHLY: 29900,  # 299.00 RUB
    PaymentPlan.YEARLY: 249900,  # 2499.00 RUB
}

# Prices as strings for YooKassa API
PLAN_PRICES_STR = {
    PaymentPlan.MONTHLY: "299.00",
    PaymentPlan.YEARLY: "2499.00",
}

# Subscription duration in days
PLAN_DURATION_DAYS = {
    PaymentPlan.MONTHLY: 30,
    PaymentPlan.YEARLY: 365,
}

TRIAL_DAYS = 3
