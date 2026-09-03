"""----------------------------"""
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.core import userDBSession
from app.entities.player_profile import PlayerProfile


"""----------------------------"""
async def get_or_create_profile(
    user_id: UUID
    , session: userDBSession
) -> PlayerProfile:
    result = await session.execute(select(PlayerProfile).where(PlayerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = PlayerProfile(
            user_id=user_id
            , level=1
            , xp=0
            , soft_currency=0
            , hard_currency=0
            , avatar_id=None
            , updated_at=datetime.now(timezone.utc)
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

    return profile


async def update_profile(
    user_id: UUID
    , avatar_id: str | None
    , session: userDBSession
) -> PlayerProfile:
    profile = await get_or_create_profile(user_id, session)
    if avatar_id is not None:
        profile.avatar_id = avatar_id
    profile.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(profile)
    return profile
