
from app.db.base import TimestampMixin, Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class Teams(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

