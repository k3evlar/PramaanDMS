"""Write-once storage for original files (FR-03, threats T10, T46).

Originals go to an S3 bucket with Object Lock in COMPLIANCE mode and versioning
(SeaweedFS in the stack, D58). Under compliance mode nobody, including the storage
admin, can delete a locked version or shorten its retention until it expires.

What "overwrite fails" means here (D84):
- The app never writes to a key that already exists: it checks first and also sends
  `If-None-Match: *`, so a second write to the same key is refused.
- A raw S3 PUT to the same key, made outside the app, cannot change the stored bytes
  either: versioning keeps the original as its own locked version, and every database
  row points at that exact version ID.

`InMemoryObjectStore` copies these rules for tests without Docker. It is a stand-in, not
proof: the real behaviour is checked by tests/integration/test_storage_seaweedfs.py.
"""

from __future__ import annotations

import base64
import hashlib
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, BinaryIO, Protocol

if TYPE_CHECKING:
    from ..config import Settings

LOCK_MODE = "COMPLIANCE"


class StorageError(RuntimeError):
    """Storage is unreachable or misconfigured. Details go to the server log only."""


class ObjectExists(StorageError):
    """The key already holds an object; originals are never overwritten."""


class ObjectLocked(StorageError):
    """The storage refused to delete or change a locked version."""


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    version_id: str
    sha256: str
    size: int
    lock_mode: str
    retain_until: datetime


class ObjectStore(Protocol):
    bucket: str

    def put_original(self, key: str, fp: BinaryIO, *, size: int, sha256: str, md5_b64: str,
                     media_type: str, retain_until: datetime) -> StoredObject: ...

    def read(self, key: str, version_id: str) -> bytes: ...


def b64(digest: bytes) -> str:
    return base64.b64encode(digest).decode("ascii")


class S3ObjectStore:
    """boto3 client for an S3 service with Object Lock (SeaweedFS in the stack)."""

    def __init__(self, *, endpoint: str, access_key: str, secret_key: str, bucket: str, client=None) -> None:  # type: ignore[no-untyped-def]
        self.bucket = bucket
        if client is None:
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "s3", endpoint_url=endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                region_name="us-east-1",
                config=Config(
                    signature_version="s3v4", s3={"addressing_style": "path"},
                    connect_timeout=3, read_timeout=30, retries={"max_attempts": 2, "mode": "standard"},
                    # Newer boto3 adds CRC checksums by default; S3-compatible servers do not all
                    # accept them. Integrity is covered by Content-MD5 and our own SHA-256 (D86).
                    request_checksum_calculation="when_required",
                    response_checksum_validation="when_required",
                ),
            )
        self._s3 = client

    @classmethod
    def from_settings(cls, s: "Settings") -> "S3ObjectStore":
        return cls(endpoint=str(s.s3_endpoint).rstrip("/"), access_key=s.s3_access_key.get_secret_value(),
                   secret_key=s.s3_secret_key.get_secret_value(), bucket=s.s3_bucket)

    @staticmethod
    def _code(err: Exception) -> str:
        return str(getattr(err, "response", {}).get("Error", {}).get("Code", ""))

    def _exists(self, key: str) -> bool:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if self._code(e) in ("404", "NoSuchKey", "NotFound"):
                return False
            raise StorageError("storage head_object failed") from e
        except BotoCoreError as e:
            raise StorageError("storage unreachable") from e

    def put_original(self, key: str, fp: BinaryIO, *, size: int, sha256: str, md5_b64: str,
                     media_type: str, retain_until: datetime) -> StoredObject:
        from botocore.exceptions import BotoCoreError, ClientError

        if self._exists(key):
            raise ObjectExists(key)
        fp.seek(0)
        try:
            resp = self._s3.put_object(
                Bucket=self.bucket, Key=key, Body=fp, ContentLength=size, ContentType=media_type,
                ContentMD5=md5_b64, IfNoneMatch="*", Metadata={"sha256": sha256},
                ObjectLockMode=LOCK_MODE, ObjectLockRetainUntilDate=retain_until,
            )
        except ClientError as e:
            if self._code(e) in ("PreconditionFailed", "ConditionalRequestConflict"):
                raise ObjectExists(key) from e
            raise StorageError("storage put_object failed") from e
        except BotoCoreError as e:
            raise StorageError("storage unreachable") from e
        version_id = resp.get("VersionId")
        if not version_id or version_id == "null":
            # Without versioning the lock and the version pointer mean nothing: refuse.
            raise StorageError("bucket versioning is not enabled")
        return StoredObject(self.bucket, key, version_id, sha256, size, LOCK_MODE, retain_until)

    def read(self, key: str, version_id: str) -> bytes:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            return self._s3.get_object(Bucket=self.bucket, Key=key, VersionId=version_id)["Body"].read()
        except (ClientError, BotoCoreError) as e:
            raise StorageError("storage get_object failed") from e


@dataclass
class _Version:
    version_id: str
    data: bytes
    retain_until: datetime


class InMemoryObjectStore:
    """Test stand-in with the same write-once rules as the S3 store (see module docstring)."""

    def __init__(self, bucket: str = "pramaan-originals") -> None:
        self.bucket = bucket
        self._objects: dict[str, list[_Version]] = {}
        self._lock = threading.Lock()
        self.fail_next_put = False  # lets tests simulate a storage outage

    def put_original(self, key: str, fp: BinaryIO, *, size: int, sha256: str, md5_b64: str,
                     media_type: str, retain_until: datetime) -> StoredObject:
        fp.seek(0)
        data = fp.read()
        if len(data) != size or b64(hashlib.md5(data, usedforsecurity=False).digest()) != md5_b64:
            raise StorageError("content does not match its length or Content-MD5")
        with self._lock:
            if self.fail_next_put:
                self.fail_next_put = False
                raise StorageError("simulated storage outage")
            if key in self._objects:
                raise ObjectExists(key)
            v = _Version(uuid.uuid4().hex, data, retain_until)
            self._objects[key] = [v]
        return StoredObject(self.bucket, key, v.version_id, sha256, size, LOCK_MODE, retain_until)

    def raw_put(self, key: str, data: bytes) -> str:
        """A PUT that skips the app's checks, as an attacker with S3 write access could send."""
        with self._lock:
            v = _Version(uuid.uuid4().hex, data, datetime.now(timezone.utc))
            self._objects.setdefault(key, []).append(v)
            return v.version_id

    def delete_version(self, key: str, version_id: str) -> None:
        with self._lock:
            for v in self._objects.get(key, []):
                if v.version_id == version_id:
                    if v.retain_until > datetime.now(timezone.utc):
                        raise ObjectLocked(f"{key}@{version_id} is under {LOCK_MODE} retention")
                    self._objects[key].remove(v)
                    return
        raise StorageError("no such version")

    def shorten_retention(self, key: str, version_id: str, until: datetime) -> None:
        with self._lock:
            for v in self._objects.get(key, []):
                if v.version_id == version_id:
                    if until < v.retain_until:
                        raise ObjectLocked("compliance retention cannot be shortened")
                    v.retain_until = until
                    return
        raise StorageError("no such version")

    def read(self, key: str, version_id: str) -> bytes:
        for v in self._objects.get(key, []):
            if v.version_id == version_id:
                return v.data
        raise StorageError("no such version")

    def keys(self) -> list[str]:
        return sorted(self._objects)
