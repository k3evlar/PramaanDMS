"""Custody events (schema v1, Phase 5).

One row per action on evidence: uploads, rejected uploads, views. Rows are append-only:
the migration revokes UPDATE and DELETE on this table from the app role (threat T14,
T16). Phase 20 adds the Merkle transparency log over these events.

Events hold IDs, hashes and metadata only, never document content (REQUIREMENTS.md 4.8).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Identity, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, JSONType, UTCDateTime, utcnow

EVENT_TYPES = ("case.created", "case.member_added", "document.uploaded", "document.version_added", "document.viewed",
               "document.listed", "upload.rejected", "storage.orphaned")


class CustodyEvent(Base):
    __tablename__ = "custody_events"

    # BIGINT identity on PostgreSQL; plain INTEGER on SQLite, which only auto-increments that type.
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), Identity(always=False),
                                    primary_key=True)
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    actor_id: Mapped[str] = mapped_column(String(64))
    actor_role: Mapped[str] = mapped_column(String(16))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id"), nullable=True, index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("document_versions.id"), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

