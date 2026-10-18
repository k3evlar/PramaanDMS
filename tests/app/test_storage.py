"""Write-once storage rules.

Two kinds of test here, both without Docker:
- the in-memory stand-in obeys the same rules the real bucket must obey;
- the S3 client sends exactly the requests that make SeaweedFS lock each original
  (checked with botocore's Stubber, which compares every request with what we expect).
Whether SeaweedFS really refuses overwrite and delete is checked against the running
service in tests/integration/test_storage_seaweedfs.py.
"""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta, timezone

import boto3
import pytest
from botocore.config import Config
from botocore.stub import ANY, Stubber

from app.evidence import storage_init
from app.evidence.storage import (InMemoryObjectStore, ObjectExists, ObjectLocked, S3ObjectStore, StorageError,
                                  b64)

DATA = b"%PDF-1.7 sample bytes"
SHA = hashlib.sha256(DATA).hexdigest()
MD5 = b64(hashlib.md5(DATA, usedforsecurity=False).digest())
UNTIL = datetime.now(timezone.utc) + timedelta(days=30)
KEY = f"originals/doc/1/{SHA}"


def put(store, key: str = KEY, data: bytes = DATA):  # type: ignore[no-untyped-def]
    return store.put_original(key, io.BytesIO(data), size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              md5_b64=b64(hashlib.md5(data, usedforsecurity=False).digest()),
                              media_type="application/pdf", retain_until=UNTIL)


# ---- in-memory stand-in ----------------------------------------------------------------

def test_fake_store_keeps_the_original_and_refuses_overwrite_and_delete() -> None:
    store = InMemoryObjectStore()
    obj = put(store)
    assert store.read(KEY, obj.version_id) == DATA and obj.lock_mode == "COMPLIANCE"
    with pytest.raises(ObjectExists):  # the app path never writes to a used key
        put(store, data=b"%PDF-1.7 changed")
    store.raw_put(KEY, b"%PDF-1.7 changed")  # a raw S3 PUT only adds a newer version
    assert store.read(KEY, obj.version_id) == DATA
    with pytest.raises(ObjectLocked):
        store.delete_version(KEY, obj.version_id)
    with pytest.raises(ObjectLocked):
        store.shorten_retention(KEY, obj.version_id, UNTIL - timedelta(days=1))
    assert store.read(KEY, obj.version_id) == DATA


def test_fake_store_allows_delete_only_after_retention_and_checks_md5() -> None:
    store = InMemoryObjectStore()
    vid = store.raw_put("k", b"x")  # retention already over
    store.delete_version("k", vid)
    with pytest.raises(StorageError):
        store.put_original("k2", io.BytesIO(DATA), size=len(DATA), sha256=SHA, md5_b64=b64(b"\x00" * 16),
                           media_type="application/pdf", retain_until=UNTIL)


# ---- real S3 client, stubbed transport --------------------------------------------------

def _client():  # type: ignore[no-untyped-def]
    return boto3.client("s3", endpoint_url="http://s3.invalid:8333", region_name="us-east-1",
                        aws_access_key_id="PRMTESTACCESSKEY0001", aws_secret_access_key="t3st-only-value-0123456789abcdef",
                        config=Config(s3={"addressing_style": "path"}, request_checksum_calculation="when_required",
                                      response_checksum_validation="when_required"))


def _store():  # type: ignore[no-untyped-def]
    c = _client()
    return S3ObjectStore(endpoint="", access_key="", secret_key="", bucket="pramaan-originals", client=c), Stubber(c)


def test_s3_put_sends_compliance_lock_md5_and_if_none_match() -> None:
    store, stub = _store()
    stub.add_client_error("head_object", service_error_code="404", http_status_code=404,
                          expected_params={"Bucket": "pramaan-originals", "Key": KEY})
    stub.add_response("put_object", {"VersionId": "v-1"}, expected_params={
        "Bucket": "pramaan-originals", "Key": KEY, "Body": ANY, "ContentLength": len(DATA),
        "ContentType": "application/pdf", "ContentMD5": MD5, "IfNoneMatch": "*", "Metadata": {"sha256": SHA},
        "ObjectLockMode": "COMPLIANCE", "ObjectLockRetainUntilDate": UNTIL})
    with stub:
        obj = put(store)
    stub.assert_no_pending_responses()
    assert (obj.version_id, obj.sha256, obj.lock_mode) == ("v-1", SHA, "COMPLIANCE")


def test_s3_existing_key_is_refused_without_any_write() -> None:
    store, stub = _store()
    stub.add_response("head_object", {"ContentLength": 5}, {"Bucket": "pramaan-originals", "Key": KEY})
    with stub, pytest.raises(ObjectExists):
        put(store)  # a put_object call here would fail the stub: none is queued


def test_s3_conditional_write_conflict_is_an_overwrite_refusal() -> None:
    store, stub = _store()
    stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
    stub.add_client_error("put_object", service_error_code="PreconditionFailed", http_status_code=412)
    with stub, pytest.raises(ObjectExists):
        put(store)


@pytest.mark.parametrize("version", [None, "null"])
def test_s3_without_versioning_is_refused(version: str | None) -> None:
    store, stub = _store()
    stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
    stub.add_response("put_object", {} if version is None else {"VersionId": version})
    with stub, pytest.raises(StorageError, match="versioning"):
        put(store)


def test_s3_errors_become_storage_errors() -> None:
    store, stub = _store()
    stub.add_client_error("head_object", service_error_code="AccessDenied", http_status_code=403)
    with stub, pytest.raises(StorageError) as e:
        put(store)
    assert not isinstance(e.value, ObjectExists)


# ---- bucket setup (storage-init) -------------------------------------------------------

LOCKED = {"ObjectLockConfiguration": {"ObjectLockEnabled": "Enabled",
                                      "Rule": {"DefaultRetention": {"Mode": "COMPLIANCE", "Days": 30}}}}


def _init_ok(stub: Stubber, bucket: str, created: bool) -> None:
    if created:
        stub.add_client_error("head_bucket", service_error_code="404", http_status_code=404)
        stub.add_response("create_bucket", {}, {"Bucket": bucket, "ObjectLockEnabledForBucket": True})
    else:
        stub.add_response("head_bucket", {}, {"Bucket": bucket})
    stub.add_response("put_bucket_versioning", {}, {"Bucket": bucket, "VersioningConfiguration": {"Status": "Enabled"}})
    stub.add_response("get_object_lock_configuration", {"ObjectLockConfiguration": {"ObjectLockEnabled": "Enabled"}})
    stub.add_response("put_object_lock_configuration", {}, {"Bucket": bucket, "ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled", "Rule": {"DefaultRetention": {"Mode": "COMPLIANCE", "Days": 30}}}})
    stub.add_response("get_bucket_versioning", {"Status": "Enabled"})


@pytest.mark.parametrize("created", [True, False])
def test_storage_init_creates_a_locked_versioned_bucket_and_reads_it_back(created: bool) -> None:
    c = _client()
    stub = Stubber(c)
    _init_ok(stub, "pramaan-originals", created)
    stub.add_response("get_object_lock_configuration", LOCKED)
    with stub:
        storage_init.ensure_bucket(c, "pramaan-originals", 30)
    stub.assert_no_pending_responses()


def test_storage_init_refuses_an_existing_bucket_without_object_lock() -> None:
    c = _client()
    stub = Stubber(c)
    stub.add_response("head_bucket", {})
    stub.add_response("put_bucket_versioning", {})
    stub.add_client_error("get_object_lock_configuration", service_error_code="ObjectLockConfigurationNotFoundError",
                          http_status_code=404)
    with stub, pytest.raises(storage_init.InitError, match="no Object Lock"):
        storage_init.ensure_bucket(c, "pramaan-originals", 30)


def test_storage_init_fails_when_settings_do_not_stick() -> None:
    c = _client()
    stub = Stubber(c)
    _init_ok(stub, "pramaan-originals", False)
    stub.add_response("get_object_lock_configuration", {"ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled", "Rule": {"DefaultRetention": {"Mode": "GOVERNANCE", "Days": 30}}}})
    with stub, pytest.raises(storage_init.InitError, match="did not stick"):
        storage_init.ensure_bucket(c, "pramaan-originals", 30)


def test_storage_init_refuses_placeholders_and_bad_input(monkeypatch: pytest.MonkeyPatch,
                                                          capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PRAMAAN_S3_ENDPOINT", "http://s3.invalid:8333")
    monkeypatch.setenv("PRAMAAN_S3_ADMIN_ACCESS_KEY", "change-me")
    monkeypatch.setenv("PRAMAAN_S3_ADMIN_SECRET_KEY", "change-me")
    assert storage_init.main() == 1
    assert "change-me" in capsys.readouterr().err
    monkeypatch.setenv("PRAMAAN_RETENTION_DAYS", "0")
    assert storage_init.main() == 1
    with pytest.raises(storage_init.InitError, match="not valid"):
        storage_init.ensure_bucket(_client(), "Bad_Bucket", 30)
