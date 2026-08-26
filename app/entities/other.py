"""----------------------------"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

# Optional: only needed if/when Apple/Google OAuth login is added
# from fastapi_users_db_sqlalchemy.oauth import SQLAlchemyBaseOAuthAccountTableUUID


"""----------------------------"""
class Device(Base):
    """
    devices
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── push_token string
    ├── platform string
    ├── app_version string
    └── last_seen_at datetime
    """
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    push_token = Column(String, unique=True, nullable=True)
    platform = Column(String, nullable=False)
    app_version = Column(String, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Device(id={self.id}, user_id={self.user_id}, platform={self.platform})>"


"""----------------------------"""
class RefreshToken(Base):
    """
    refresh_tokens
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── device_id UUID, foreign key -> devices.id
    ├── token_hash string, unique, indexed
    ├── expires_at datetime
    ├── revoked_at datetime, nullable
    └── created_at datetime
    """
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked_at is not None})>"


"""----------------------------"""
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

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    level = Column(Integer, nullable=False, default=1)
    xp = Column(Integer, nullable=False, default=0)
    soft_currency = Column(Integer, nullable=False, default=0)
    hard_currency = Column(Integer, nullable=False, default=0)
    avatar_id = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PlayerProfile(user_id={self.user_id}, level={self.level}, xp={self.xp})>"


"""----------------------------"""
class World(Base):
    """
    worlds
    ├── id UUID, primary key
    ├── name string
    └── order_index integer
    """
    __tablename__ = "worlds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<World(id={self.id}, name={self.name})>"


"""----------------------------"""
class Level(Base):
    """
    levels
    ├── id UUID, primary key
    ├── world_id UUID, foreign key -> worlds.id
    ├── name string
    ├── difficulty integer
    └── order_index integer
    """
    __tablename__ = "levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Level(id={self.id}, world_id={self.world_id}, name={self.name})>"


"""----------------------------"""
class LevelProgress(Base):
    """
    level_progress
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── level_id UUID, foreign key -> levels.id
    ├── stars integer
    ├── best_score integer
    ├── attempts integer
    ├── completed_at datetime, nullable
    └── unique(user_id, level_id)
    """
    __tablename__ = "level_progress"
    __table_args__ = (UniqueConstraint("user_id", "level_id", name="uq_level_progress_user_level"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    level_id = Column(UUID(as_uuid=True), ForeignKey("levels.id"), nullable=False, index=True)
    stars = Column(Integer, nullable=False, default=0)
    best_score = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<LevelProgress(user_id={self.user_id}, level_id={self.level_id}, stars={self.stars})>"


"""----------------------------"""
class GameSession(Base):
    """
    game_sessions
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── device_id UUID, foreign key -> devices.id
    ├── level_id UUID, foreign key -> levels.id, nullable
    ├── started_at datetime
    ├── ended_at datetime, nullable
    └── app_version string
    """
    __tablename__ = "game_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    level_id = Column(UUID(as_uuid=True), ForeignKey("levels.id"), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    app_version = Column(String, nullable=False)

    def __repr__(self):
        return f"<GameSession(id={self.id}, user_id={self.user_id})>"


"""----------------------------"""
class Item(Base):
    """
    items
    ├── id UUID, primary key
    ├── name string
    ├── type string
    ├── rarity string
    ├── price_soft integer
    └── price_hard integer
    """
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    rarity = Column(String, nullable=False)
    price_soft = Column(Integer, nullable=True)
    price_hard = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Item(id={self.id}, name={self.name}, rarity={self.rarity})>"


"""----------------------------"""
class Inventory(Base):
    """
    inventory
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── item_id UUID, foreign key -> items.id
    ├── quantity integer
    └── acquired_at datetime
    """
    __tablename__ = "inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    acquired_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Inventory(user_id={self.user_id}, item_id={self.item_id}, quantity={self.quantity})>"


"""----------------------------"""
class Purchase(Base):
    """
    purchases
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── product_id string
    ├── store string
    ├── transaction_id string, unique
    ├── amount_usd float
    ├── status string
    └── purchased_at datetime
    """
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    store = Column(String, nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    amount_usd = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    purchased_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Purchase(id={self.id}, user_id={self.user_id}, status={self.status})>"


"""----------------------------"""
class Leaderboard(Base):
    """
    leaderboards
    ├── id UUID, primary key
    ├── name string
    ├── scope string
    └── reset_period string
    """
    __tablename__ = "leaderboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    reset_period = Column(String, nullable=False)

    def __repr__(self):
        return f"<Leaderboard(id={self.id}, name={self.name})>"


"""----------------------------"""
class LeaderboardEntry(Base):
    """
    leaderboard_entries
    ├── id UUID, primary key
    ├── leaderboard_id UUID, foreign key -> leaderboards.id
    ├── user_id UUID, foreign key -> users.id
    ├── score integer
    ├── recorded_at datetime
    └── unique(leaderboard_id, user_id)
    """
    __tablename__ = "leaderboard_entries"
    __table_args__ = (UniqueConstraint("leaderboard_id", "user_id", name="uq_leaderboard_entry_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leaderboard_id = Column(UUID(as_uuid=True), ForeignKey("leaderboards.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<LeaderboardEntry(leaderboard_id={self.leaderboard_id}, user_id={self.user_id}, score={self.score})>"


"""----------------------------"""
class Achievement(Base):
    """
    achievements
    ├── id UUID, primary key
    ├── name string
    └── criteria string
    """
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    criteria = Column(String, nullable=False)

    def __repr__(self):
        return f"<Achievement(id={self.id}, name={self.name})>"


"""----------------------------"""
class UserAchievement(Base):
    """
    user_achievements
    ├── id UUID, primary key
    ├── user_id UUID, foreign key -> users.id
    ├── achievement_id UUID, foreign key -> achievements.id
    ├── unlocked_at datetime
    └── unique(user_id, achievement_id)
    """
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False, index=True)
    unlocked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"

