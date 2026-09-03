from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.entities.user import User
from app.entities.player_profile import PlayerProfile
