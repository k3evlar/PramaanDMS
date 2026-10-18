"""Evidence intake: check, hash, store write-once, record (FR-01 to FR-03, FR-06).

Order of work for one upload:
1. Access check: the caller is a member of the case with an uploading role.
2. SHA-256 (and MD5 for the S3 Content-MD5 header) over the exact received bytes, before
   anything else reads the file. The size limit is enforced while reading.
3. Type and limit checks (filetypes.py).
4. Write the original to locked storage under a server-chosen key.
5. One database transaction: document (for a new upload), stored object, version row and
   the custody event. They commit together or not at all.

Storage comes first because a locked object cannot be removed. If step 5 fails, the
object stays in storage with no row pointing at it; a `storage.orphaned` custody event
records its key so an auditor can account for it (D83).

Every refused upload writes an `upload.rejected` event with a reason code (FR-02).
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ..access.identity import UPLOAD_ROLES, Actor
from ..cases.service import require_member
from ..config import Settings
from ..custody.events import record
from ..errors import ApiError
from ..validation import InvalidText, clean_filename, clean_text
from .filetypes import Limits, RejectedFile, inspect
from .models import DOC_TYPES, Document, DocumentVersion, StorageObject
from .storage import ObjectExists, ObjectStore, StorageError, StoredObject, b64

log = logging.getLogger("pramaan.intake")
CHUNK = 1024 * 1024


@dataclass(frozen=True)
class Digest:
    size: int
    sha256: str
    md5_b64: str


@dataclass(frozen=True)
class IntakeResult:
    document_id: uuid.UUID
    version_id: uuid.UUID
    version_no: int
    sha256: str
    size_bytes: int
    media_type: str
    page_count: int


def digest(fp: BinaryIO, max_bytes: int) -> Digest:
    """Hash the stream from the start. Stops reading as soon as the limit is passed."""
    fp.seek(0)
    sha, md5, size = hashlib.sha256(), hashlib.md5(usedforsecurity=False), 0
    while chunk := fp.read(CHUNK):
        size += len(chunk)
        if size > max_bytes:
            raise RejectedFile("too_large", f"The file is larger than {max_bytes // (1024 * 1024)} MB.", 413)
        sha.update(chunk)
        md5.update(chunk)
    return Digest(size, sha.hexdigest(), b64(md5.digest()))


def object_key(document_id: uuid.UUID, version_no: int, sha256: str) -> str:
    # Server-generated only; the uploader's file name is never part of a path (4.4).
    return f"originals/{document_id}/{version_no}/{sha256}"


class IntakeService:
    def __init__(self, sf: sessionmaker[Session], store: ObjectStore, settings: Settings) -> None:
        self.sf, self.store, self.s = sf, store, settings
        self.limits = Limits(settings.max_upload_bytes, settings.max_pages, settings.max_image_pixels)

    # -- refusals -------------------------------------------------------------------------
    def _reject(self, actor: Actor, code: str, client_ip: str | None, *, case_id: uuid.UUID | None = None,
                document_id: uuid.UUID | None = None, extra: dict[str, str] | None = None) -> None:
        try:
            with self.sf() as s, s.begin():
                record(s, "upload.rejected", actor, case_id=case_id, document_id=document_id,
                       client_ip=client_ip, details={"code": code, **(extra or {})})
        except Exception:  # noqa: BLE001 - the refusal itself must still reach the caller
            log.exception("could not record upload.rejected", extra={"code": code})

    def _checked_file(self, actor: Actor, fp: BinaryIO, filename: str, client_ip: str | None,
                      case_id: uuid.UUID, document_id: uuid.UUID | None) -> tuple[Digest, str, int]:
        try:
            d = digest(fp, self.limits.max_bytes)
            info = inspect(fp, d.size, filename, self.limits)
        except RejectedFile as e:
            self._reject(actor, e.code, client_ip, case_id=case_id, document_id=document_id)
            raise ApiError(e.status, e.code, e.message) from None
        return d, info.media_type, info.page_count

    def _access(self, actor: Actor, case_id: uuid.UUID, client_ip: str | None,
                document_id: uuid.UUID | None = None) -> None:
        with self.sf() as s:
            try:
                require_member(s, actor, case_id, UPLOAD_ROLES)
            except ApiError as e:
                known_case = case_id if e.code != "case_not_found" else None
                self._reject(actor, e.code, client_ip, case_id=known_case, document_id=document_id,
                             extra=None if known_case else {"requested_case": str(case_id)})
                raise

    # -- storage then database ------------------------------------------------------------
    def _store(self, key: str, fp: BinaryIO, d: Digest, media_type: str) -> StoredObject:
        retain = datetime.now(timezone.utc) + timedelta(days=self.s.retention_days)
        try:
            return self.store.put_original(key, fp, size=d.size, sha256=d.sha256, md5_b64=d.md5_b64,
                                           media_type=media_type, retain_until=retain)
        except ObjectExists:
            raise ApiError(409, "already_stored", "A stored original already uses this slot. Try again.") from None
        except StorageError:
            log.exception("storage write failed", extra={"key": key})
            raise ApiError(503, "storage_unavailable", "Storage is not available. Nothing was saved.") from None

    def _orphaned(self, actor: Actor, obj: StoredObject, case_id: uuid.UUID, client_ip: str | None) -> None:
        log.error("stored object has no database row", extra={"key": obj.key, "version": obj.version_id})
        try:
            with self.sf() as s, s.begin():
                record(s, "storage.orphaned", actor, case_id=case_id, client_ip=client_ip,
                       details={"bucket": obj.bucket, "object_key": obj.key, "storage_version": obj.version_id,
                                "sha256": obj.sha256})
        except Exception:  # noqa: BLE001 - the server log line above still holds the key
            log.exception("could not record storage.orphaned", extra={"key": obj.key})

    def _rows(self, s: Session, obj: StoredObject, document_id: uuid.UUID, version_no: int, media_type: str,
              pages: int, filename: str, actor: Actor, reason: str | None) -> DocumentVersion:
        so = StorageObject(bucket=obj.bucket, object_key=obj.key, version_id=obj.version_id, sha256=obj.sha256,
                           size_bytes=obj.size, lock_mode=obj.lock_mode, retain_until=obj.retain_until)
        s.add(so)
        s.flush()
        v = DocumentVersion(document_id=document_id, version_no=version_no, sha256=obj.sha256, size_bytes=obj.size,
                            media_type=media_type, page_count=pages, original_name=filename, reason=reason,
                            storage_object_id=so.id, uploaded_by=actor.user_id)
        s.add(v)
        s.flush()
        return v

    # -- public operations ----------------------------------------------------------------
    def upload_new(self, actor: Actor, case_id: uuid.UUID, doc_type: str, title: str, fp: BinaryIO,
                   raw_filename: str | None, client_ip: str | None) -> IntakeResult:
        self._access(actor, case_id, client_ip)
        doc_type = doc_type.upper()
        try:
            if doc_type not in DOC_TYPES:
                raise InvalidText("doc_type must be one of " + ", ".join(DOC_TYPES))
            title = clean_text(title, field="title", max_len=200)
        except InvalidText as e:
            self._reject(actor, "invalid_request", client_ip, case_id=case_id)
            raise ApiError(422, "invalid_request", str(e)) from None
        filename = clean_filename(raw_filename)
        d, media_type, pages = self._checked_file(actor, fp, filename, client_ip, case_id, None)

        document_id = uuid.uuid4()
        obj = self._store(object_key(document_id, 1, d.sha256), fp, d, media_type)
        try:
            with self.sf() as s, s.begin():
                s.add(Document(id=document_id, case_id=case_id, doc_type=doc_type, title=title,
                               created_by=actor.user_id))
                s.flush()
                v = self._rows(s, obj, document_id, 1, media_type, pages, filename, actor, None)
                record(s, "document.uploaded", actor, case_id=case_id, document_id=document_id, version_id=v.id,
                       client_ip=client_ip, details=_event_details(v, obj))
        except Exception:
            self._orphaned(actor, obj, case_id, client_ip)
            raise
        return IntakeResult(document_id, v.id, 1, d.sha256, d.size, media_type, pages)

    def add_version(self, actor: Actor, document_id: uuid.UUID, reason: str, fp: BinaryIO,
                    raw_filename: str | None, client_ip: str | None) -> IntakeResult:
        with self.sf() as s:
            doc = s.get(Document, document_id)
            if doc is None:
                self._reject(actor, "document_not_found", client_ip, extra={"requested_document": str(document_id)})
                raise ApiError(404, "document_not_found", "No such document.")
            case_id = doc.case_id
            latest = s.execute(select(DocumentVersion.version_no, DocumentVersion.sha256)
                               .where(DocumentVersion.document_id == document_id)
                               .order_by(DocumentVersion.version_no.desc()).limit(1)).one()
        self._access(actor, case_id, client_ip, document_id)
        try:
            reason = clean_text(reason, field="reason", max_len=500)
        except InvalidText as e:
            self._reject(actor, "invalid_request", client_ip, case_id=case_id, document_id=document_id)
            raise ApiError(422, "invalid_request", str(e)) from None
        filename = clean_filename(raw_filename)
        d, media_type, pages = self._checked_file(actor, fp, filename, client_ip, case_id, document_id)
        if d.sha256 == latest.sha256:
            self._reject(actor, "same_content", client_ip, case_id=case_id, document_id=document_id)
            raise ApiError(409, "same_content", f"This file is identical to version {latest.version_no}.")

        version_no = latest.version_no + 1
        obj = self._store(object_key(document_id, version_no, d.sha256), fp, d, media_type)
        try:
            with self.sf() as s, s.begin():
                current = s.scalar(select(func.max(DocumentVersion.version_no))
                                   .where(DocumentVersion.document_id == document_id))
                if current != latest.version_no:
                    raise IntegrityError("concurrent version upload", None, Exception("version changed"))
                v = self._rows(s, obj, document_id, version_no, media_type, pages, filename, actor, reason)
                record(s, "document.version_added", actor, case_id=case_id, document_id=document_id,
                       version_id=v.id, reason=reason, client_ip=client_ip, details=_event_details(v, obj))
        except IntegrityError:
            self._orphaned(actor, obj, case_id, client_ip)
            raise ApiError(409, "version_conflict", "Another version was added at the same time. Reload and try again.") from None
        except Exception:
            self._orphaned(actor, obj, case_id, client_ip)
            raise
        return IntakeResult(document_id, v.id, version_no, d.sha256, d.size, media_type, pages)


def _event_details(v: DocumentVersion, obj: StoredObject) -> dict[str, object]:
    # IDs, hashes and metadata only, never content (REQUIREMENTS.md 4.8).
    return {"version_no": v.version_no, "sha256": v.sha256, "size_bytes": v.size_bytes, "media_type": v.media_type,
            "page_count": v.page_count, "bucket": obj.bucket, "object_key": obj.key,
            "storage_version": obj.version_id, "lock_mode": obj.lock_mode,
            "retain_until": obj.retain_until.isoformat()}
