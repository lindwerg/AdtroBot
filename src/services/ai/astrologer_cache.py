"""In-memory cache for astrologer chat conversations."""

import time
from datetime import date
from typing import TypedDict

import structlog

logger = structlog.get_logger()

# Cache TTL: 30 minutes
CONVERSATION_TTL = 1800

# Max messages in history (5 user-assistant pairs)
MAX_HISTORY_LENGTH = 10

# Freemium: 3 questions per day
FREE_DAILY_LIMIT = 3


class ConversationContext(TypedDict):
    """Conversation context stored in memory."""

    messages: list[dict]  # History: [{"role": "user"/"assistant", "content": str}, ...]
    natal_data: dict  # FullNatalChartResult (static)
    transit_data: dict | None  # DailyTransitResult (optional)
    created_at: float  # Timestamp
    last_activity: float  # Last message timestamp


# In-memory conversation cache: user_id -> ConversationContext
_conversations: dict[int, ConversationContext] = {}

# Daily question counter for free users: user_id -> (count, date)
_daily_questions: dict[int, tuple[int, date]] = {}


async def get_conversation(user_id: int) -> ConversationContext | None:
    """Get active conversation for user.

    Args:
        user_id: Telegram user ID

    Returns:
        ConversationContext if exists and not expired, None otherwise
    """
    if user_id not in _conversations:
        return None

    conv = _conversations[user_id]
    age = time.time() - conv["last_activity"]

    # Check TTL
    if age > CONVERSATION_TTL:
        logger.info("conversation_expired", user_id=user_id, age_seconds=int(age))
        del _conversations[user_id]
        return None

    return conv


async def create_conversation(
    user_id: int,
    natal_data: dict,
    transit_data: dict | None = None,
) -> ConversationContext:
    """Create new conversation context.

    Args:
        user_id: Telegram user ID
        natal_data: FullNatalChartResult
        transit_data: DailyTransitResult (optional)

    Returns:
        Created ConversationContext
    """
    now = time.time()
    conv: ConversationContext = {
        "messages": [],
        "natal_data": natal_data,
        "transit_data": transit_data,
        "created_at": now,
        "last_activity": now,
    }
    _conversations[user_id] = conv

    logger.info(
        "conversation_created",
        user_id=user_id,
        has_transit_data=transit_data is not None,
    )
    return conv


async def add_message(user_id: int, role: str, content: str) -> None:
    """Add message to conversation history.

    Trims history to MAX_HISTORY_LENGTH if needed.

    Args:
        user_id: Telegram user ID
        role: "user" or "assistant"
        content: Message text
    """
    conv = await get_conversation(user_id)
    if not conv:
        logger.error("add_message_no_conversation", user_id=user_id)
        return

    # Add message
    conv["messages"].append({"role": role, "content": content})

    # Trim history if too long (keep last N messages)
    if len(conv["messages"]) > MAX_HISTORY_LENGTH:
        conv["messages"] = conv["messages"][-MAX_HISTORY_LENGTH:]

    # Update activity timestamp
    conv["last_activity"] = time.time()

    logger.debug(
        "message_added",
        user_id=user_id,
        role=role,
        history_len=len(conv["messages"]),
    )


async def end_conversation(user_id: int) -> None:
    """End conversation and clear from cache.

    Args:
        user_id: Telegram user ID
    """
    if user_id in _conversations:
        del _conversations[user_id]
        logger.info("conversation_ended", user_id=user_id)


async def check_question_limit(user_id: int, is_premium: bool) -> bool:
    """Check if user can ask another question (freemium limits).

    Premium users: unlimited
    Free users: 3 questions per day

    Args:
        user_id: Telegram user ID
        is_premium: Whether user has premium subscription

    Returns:
        True if user can ask question, False if limit reached
    """
    if is_premium:
        return True

    today = date.today()

    # Get or initialize counter
    if user_id in _daily_questions:
        count, last_date = _daily_questions[user_id]

        # Reset counter if new day
        if last_date != today:
            _daily_questions[user_id] = (0, today)
            count = 0
    else:
        _daily_questions[user_id] = (0, today)
        count = 0

    # Check limit
    if count >= FREE_DAILY_LIMIT:
        logger.info(
            "question_limit_reached",
            user_id=user_id,
            count=count,
            limit=FREE_DAILY_LIMIT,
        )
        return False

    return True


async def increment_question_count(user_id: int) -> None:
    """Increment daily question counter for free user.

    Args:
        user_id: Telegram user ID
    """
    today = date.today()

    if user_id in _daily_questions:
        count, last_date = _daily_questions[user_id]
        if last_date == today:
            _daily_questions[user_id] = (count + 1, today)
        else:
            _daily_questions[user_id] = (1, today)
    else:
        _daily_questions[user_id] = (1, today)

    logger.debug("question_count_incremented", user_id=user_id)


async def get_remaining_questions(user_id: int, is_premium: bool) -> int | None:
    """Get remaining questions for user today.

    Args:
        user_id: Telegram user ID
        is_premium: Whether user has premium

    Returns:
        Number of remaining questions, or None if unlimited (premium)
    """
    if is_premium:
        return None

    today = date.today()

    if user_id in _daily_questions:
        count, last_date = _daily_questions[user_id]
        if last_date != today:
            count = 0
    else:
        count = 0

    return max(0, FREE_DAILY_LIMIT - count)


async def cleanup_expired_conversations() -> int:
    """Remove expired conversations from cache.

    Called periodically by background task or on-demand.

    Returns:
        Number of conversations removed
    """
    now = time.time()
    expired_users = []

    for user_id, conv in _conversations.items():
        age = now - conv["last_activity"]
        if age > CONVERSATION_TTL:
            expired_users.append(user_id)

    for user_id in expired_users:
        del _conversations[user_id]

    if expired_users:
        logger.info(
            "conversations_cleaned_up",
            count=len(expired_users),
            users=expired_users,
        )

    return len(expired_users)
