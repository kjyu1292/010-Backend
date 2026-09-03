from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from app.database import Base

class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    Inherited from SQLAlchemyBaseUserTableUUID:
    users
    ├── id              UUID, primary key
    ├── email           string, unique
    ├── hashed_password string
    ├── is_active       boolean
    ├── is_superuser    boolean
    └── is_verified     boolean
    """
    __tablename__ = "users"

    """
    Additional columns
    """
    display_name = Column(String, unique = True, nullable = False)
    platform = Column(String, unique = False, nullable = False)
    status = Column(Integer, unique = False, nullable = False)
    created_at = Column(DateTime(timezone = True), unique = False, nullable = False
                        , default = lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone = True), unique = False, nullable = False
                        , default = lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"""<User(
            ...
        )>"""

