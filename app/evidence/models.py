"""Documents, versions, stored objects, fingerprints and verdicts (schema v1, Phase 5).

Originals are never changed: a correction is a new version (FR-06), and each version
points to one write-once stored object. Fingerprint and verdict rows are created here so
later phases (7, 8, 15) only add data, not tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base, JSONType, UTCDateTime, utcnow

DOC_TYPES = ("FIR", "STATEMENT", "CHARGESHEET")
MEDIA_TYPES = ("application/pdf", "image/png", "image/jpeg", "image/tiff")
# Verdict and severity names locked before Phase 2 (D49): enforced by the database too.
VERDICTS = ("Identical", "Equivalent", "Tampered", "Inconclusive", "Not supported")
SEVERITIES = ("Major", "Minor", "None")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (CheckConstraint(f"doc_type IN {DOC_TYPES}", name="doc_type"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(200))
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document",
                                                             order_by="DocumentVersion.version_no")


class StorageObject(Base):
    __tablename__ = "storage_objects"
    __table_args__ = (UniqueConstraint("bucket", "object_key", name="bucket_key"),
                      CheckConstraint("length(sha256) = 64", name="sha256_length"),
                      CheckConstraint("size_bytes > 0", name="size_positive"))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    bucket: Mapped[str] = mapped_column(String(63))
    object_key: Mapped[str] = mapped_column(String(512))
    version_id: Mapped[str] = mapped_column(String(128))  # storage version that holds the bytes
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    lock_mode: Mapped[str] = mapped_column(String(16))
    retain_until: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_no", name="document_version"),
                      CheckConstraint("version_no >= 1", name="version_positive"),
                      CheckConstraint(f"media_type IN {MEDIA_TYPES}", name="media_type"),
                      CheckConstraint("length(sha256) = 64", name="sha256_length"))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    media_type: Mapped[str] = mapped_column(String(32))
    page_count: Mapped[int] = mapped_column(Integer)
    # The uploader's file name is kept only as display metadata (cleaned, never used as a path).
    original_name: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)  # why a correction was uploaded
    storage_object_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("storage_objects.id"), unique=True)
    uploaded_by: Mapped[str] = mapped_column(String(64))
    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    document: Mapped[Document] = relationship(back_populates="versions")
    storage_object: Mapped[StorageObject] = relationship()


class Fingerprint(Base):
    """Legal Hash fingerprint record of one version (filled from Phase 7)."""

    __tablename__ = "fingerprints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    record: Mapped[dict[str, Any]] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Verdict(Base):
    """A verification result against one version (filled from Phase 8)."""

    __tablename__ = "verdicts"
    __table_args__ = (CheckConstraint(f"verdict IN {VERDICTS}", name="verdict"),
                      CheckConstraint(f"severity IN {SEVERITIES}", name="severity"),
                      CheckConstraint("(verdict = 'Tampered') = (severity <> 'None')", name="severity_matches_verdict"))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"), index=True)
    candidate_sha256: Mapped[str] = mapped_column(String(64))
    verdict: Mapped[str] = mapped_column(String(16))
    severity: Mapped[str] = mapped_column(String(8))
    record: Mapped[dict[str, Any]] = mapped_column(JSONType)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
