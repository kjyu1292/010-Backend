from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

from app.database import Base

class PlayerProfile(Base):
    """
    player_profiles
    ├── user_id UUID, primary key, foreign key -> users.id
    ├── level integer
    ├── xp integer
    ├── soft_currency integer
    ├── hard_currency integer
    ├── avatar_id string
    └── updated_at datetime
    """
    __tablename__ = "player_profiles"

    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), primary_key = True)
    level = Column(Integer, nullable = False, default = 1)
    xp = Column(Integer, nullable = False, default = 0)
    soft_currency = Column(Integer, nullable = False, default = 0)
    hard_currency = Column(Integer, nullable = False, default = 0)
    avatar_id = Column(String, nullable = True)
    updated_at = Column(DateTime(timezone = True), nullable = False, default = lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PlayerProfile(user_id={self.user_id}, level={self.level}, xp={self.xp})>"

