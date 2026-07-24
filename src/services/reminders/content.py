import random

from src.infrastructure.db.models.user import User
from src.services.gamification.xp_service import level_for_xp

DAILY_PROMPTS = [
    "Haven't heard from you today. Got five minutes to practice? Send me a voice message.",
    "Quick reminder: today's practice is still open. A short voice message keeps the streak alive.",
    "Your English is waiting on you. Send a voice message whenever you're ready.",
]


def build_daily_message(user: User) -> str:
    text = random.choice(DAILY_PROMPTS)
    if user.streak_days > 0:
        text += f"\n🔥 Current streak: {user.streak_days} day(s) — don't lose it."
    return text


def build_weekly_message(user: User, new_vocab: int, mistakes_logged: int) -> str:
    lines = [
        "<b>Weekly recap</b>",
        f"🔥 Streak: {user.streak_days} day(s)",
        f"⭐ Level {level_for_xp(user.xp)} — {user.xp} XP total",
        f"📚 New vocabulary this week: {new_vocab}",
        f"📝 Mistakes logged this week: {mistakes_logged}",
    ]
    if new_vocab == 0 and mistakes_logged == 0:
        lines.append("\nQuiet week — send a voice message to get back into it.")
    return "\n".join(lines)


def build_monthly_message(user: User, achievement_count: int) -> str:
    lines = [
        "<b>Monthly check-in</b>",
        f"⭐ Level {level_for_xp(user.xp)} — {user.xp} XP total",
        f"🔥 Current streak: {user.streak_days} day(s)",
        f"🏆 Achievements unlocked: {achievement_count}",
        f"Target level: {user.target_level} (currently {user.current_level})",
    ]
    return "\n".join(lines)
