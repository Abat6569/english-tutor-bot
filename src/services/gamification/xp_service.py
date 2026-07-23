from dataclasses import dataclass, field

from src.infrastructure.db.repositories.achievement_repository import AchievementRepository
from src.infrastructure.db.repositories.user_repository import UserRepository

XP_MILESTONES: list[tuple[int, str, str]] = [
    (100, "xp_100", "⭐ 100 XP reached"),
    (500, "xp_500", "⭐⭐ 500 XP reached"),
    (1000, "xp_1000", "⭐⭐⭐ 1000 XP reached"),
]

STREAK_MILESTONES: list[tuple[int, str, str]] = [
    (3, "streak_3", "🔥 3-day streak"),
    (7, "streak_7", "🔥🔥 7-day streak"),
    (30, "streak_30", "🔥🔥🔥 30-day streak"),
]


def level_for_xp(xp: int) -> int:
    return xp // 100 + 1


@dataclass(frozen=True)
class GamificationUpdate:
    xp: int
    level: int
    streak_days: int
    newly_unlocked: list[str] = field(default_factory=list)


class GamificationService:
    def __init__(self, users: UserRepository, achievements: AchievementRepository) -> None:
        self._users = users
        self._achievements = achievements

    async def record_activity(self, user_id: int, xp_gained: int) -> GamificationUpdate:
        user = await self._users.add_xp_and_update_streak(user_id, xp_gained)

        newly_unlocked: list[str] = []
        for threshold, code, label in XP_MILESTONES:
            if user.xp >= threshold and await self._achievements.unlock(user_id, code):
                newly_unlocked.append(label)
        for threshold, code, label in STREAK_MILESTONES:
            if user.streak_days >= threshold and await self._achievements.unlock(user_id, code):
                newly_unlocked.append(label)

        return GamificationUpdate(
            xp=user.xp,
            level=level_for_xp(user.xp),
            streak_days=user.streak_days,
            newly_unlocked=newly_unlocked,
        )
