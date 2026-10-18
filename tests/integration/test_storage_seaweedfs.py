"""Real SeaweedFS: originals cannot be overwritten or deleted (Phase 5 exit criterion 2).

Each run makes a fresh bucket named pramaan-it-<random> with a 1-day COMPLIANCE lock.
Its objects cannot be removed until the lock ends; that is the point of the test. Remove
the seaweeddata volume to clear them on a dev machine.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from botocore.exceptions import ClientError

from app.evidence import storage_init
from app.evidence.storage import ObjectExists, S3ObjectStore, b64

DATA = b"%PDF-1.7 integration original"


@pytest.fixture(scope="module")
def bucket(s3_admin) -> str:  # type: ignore[no-untyped-def]
    name = f"pramaan-it-{uuid.uuid4().hex[:12]}"
    storage_init.ensure_bucket(s3_admin, name, 1)
    return name


def _put(store: S3ObjectStore, key: str, data: bytes):  # type: ignore[no-untyped-def]
    return store.put_original(key, io.BytesIO(data), size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              md5_b64=b64(hashlib.md5(data, usedforsecurity=False).digest()),
                              media_type="application/pdf",
                              retain_until=datetime.now(timezone.utc) + timedelta(days=1))


def test_bucket_has_versioning_and_compliance_lock(s3_admin, bucket: str) -> None:  # type: ignore[no-untyped-def]
    assert s3_admin.get_bucket_versioning(Bucket=bucket)["Status"] == "Enabled"
    rule = s3_admin.get_object_lock_configuration(Bucket=bucket)["ObjectLockConfiguration"]
    assert rule["ObjectLockEnabled"] == "Enabled"
    assert rule["Rule"]["DefaultRetention"]["Mode"] == "COMPLIANCE"


def test_original_is_locked_and_cannot_be_overwritten_or_deleted(s3_app, s3_admin, bucket: str) -> None:  # type: ignore[no-untyped-def]
    store = S3ObjectStore(endpoint="", access_key="", secret_key="", bucket=bucket, client=s3_app)
    key = f"originals/{uuid.uuid4()}/1/{hashlib.sha256(DATA).hexdigest()}"
    obj = _put(store, key, DATA)
    head = s3_admin.head_object(Bucket=bucket, Key=key, VersionId=obj.version_id)
    assert head["ObjectLockMode"] == "COMPLIANCE"

    # 1. The app refuses a second write to the key.
    with pytest.raises(ObjectExists):
        _put(store, key, b"%PDF-1.7 replaced")

    # 2. A raw PUT only adds a newer version; the original version keeps its bytes.
    newer = s3_app.put_object(Bucket=bucket, Key=key, Body=b"%PDF-1.7 replaced")
    assert newer["VersionId"] != obj.version_id
    assert store.read(key, obj.version_id) == DATA

    # 3. Deleting the locked version fails, even for the admin identity.
    for client in (s3_app, s3_admin):
        with pytest.raises(ClientError):
            client.delete_object(Bucket=bucket, Key=key, VersionId=obj.version_id)

    # 4. The lock cannot be shortened or bypassed.
    with pytest.raises(ClientError):
        s3_admin.put_object_retention(Bucket=bucket, Key=key, VersionId=obj.version_id, Retention={
            "Mode": "COMPLIANCE", "RetainUntilDate": datetime.now(timezone.utc) + timedelta(minutes=1)})
    with pytest.raises(ClientError):
        s3_admin.delete_object(Bucket=bucket, Key=key, VersionId=obj.version_id, BypassGovernanceRetention=True)

    # 5. A plain delete only hides the key behind a marker; the version is still there.
    s3_admin.delete_object(Bucket=bucket, Key=key)
    assert store.read(key, obj.version_id) == DATA
