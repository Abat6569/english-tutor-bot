from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.db.repositories.achievement_repository import AchievementRepository
from src.infrastructure.db.repositories.mistake_repository import MistakeRepository
from src.infrastructure.db.repositories.user_repository import UserRepository
from src.infrastructure.db.repositories.vocabulary_repository import VocabularyRepository
from src.infrastructure.db.session import get_session
from src.services.gamification.xp_service import level_for_xp

router = Router(name="progress")


@router.message(Command("progress"))
async def cmd_progress(message: Message) -> None:
    assert message.from_user is not None

    async with get_session() as session:
        user = await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username
        )
        vocab_items = await VocabularyRepository(session).recent(message.from_user.id, limit=1000)
        vocab_count = len(vocab_items)
        mistake_counts = await MistakeRepository(session).category_counts(
            message.from_user.id, limit=1000
        )
        achievement_count = await AchievementRepository(session).count(message.from_user.id)

    level = level_for_xp(user.xp)
    xp_into_level = user.xp % 100
    total_mistakes = sum(mistake_counts.values())
    streak_label = "day" if user.streak_days == 1 else "days"

    lines = [
        f"<b>Level {level}</b> — {user.xp} XP ({xp_into_level}/100 to next level)",
        f"🔥 Streak: {user.streak_days} {streak_label}",
        f"🏆 Achievements: {achievement_count}",
        f"📚 Vocabulary saved: {vocab_count}",
        f"📝 Mistakes logged: {total_mistakes}",
    ]
    await message.answer("\n".join(lines))
