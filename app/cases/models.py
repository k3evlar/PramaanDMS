"""Cases and case membership (schema v1, Phase 5).

Access is per case: a staff user sees a case only if they are a member (deny by default,
SCOPE.md section 2). Phase 17 adds supervisor units and the full access matrix.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base, UTCDateTime, utcnow

ROLES = ("IO", "SUPERVISOR", "CLERK", "AUDITOR", "ADMIN")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    members: Mapped[list["CaseMember"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseMember(Base):
    __tablename__ = "case_members"
    __table_args__ = (CheckConstraint(f"role IN {ROLES}", name="role"),)

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(16))
    added_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    case: Mapped[Case] = relationship(back_populates="members")
