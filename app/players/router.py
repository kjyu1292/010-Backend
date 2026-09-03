"""----------------------------"""
from fastapi import APIRouter

from app.database.core import userDBSession
from app.auth.service import CurrentUser

from app.players import service
from app.players.model import PlayerProfileResponse, PlayerProfileUpdate


"""----------------------------"""
router = APIRouter(prefix="/players", tags=["players"])


"""----------------------------"""
@router.get("/me", response_model = PlayerProfileResponse)
async def get_my_profile(
    current_user: CurrentUser
    , session: userDBSession
):
    return await service.get_or_create_profile(current_user.id, session)


@router.patch("/me", response_model = PlayerProfileResponse)
async def update_my_profile(
    payload: PlayerProfileUpdate
    , current_user: CurrentUser
    , session: userDBSession
):
    return await service.update_profile(current_user.id, payload.avatar_id, session)
