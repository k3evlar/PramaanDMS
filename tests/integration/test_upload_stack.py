"""Full upload through the running stack: browser port, nginx, API, PostgreSQL, SeaweedFS.

Phase 5 exit criterion 1. It leaves one test case and one locked original in the dev
stack, with the title "Integration test".
"""

from __future__ import annotations

import hashlib
import uuid

import httpx
import pytest

from tests.app import samples

HEADERS = {"X-Pramaan-User": "it.officer", "X-Pramaan-Role": "IO"}


@pytest.fixture(scope="module")
def base(dotenv: dict[str, str]) -> str:
    return f"http://127.0.0.1:{dotenv.get('PRAMAAN_HTTP_PORT', '8080')}/api"


def test_upload_end_to_end_stores_sha256_and_a_locked_original(base: str, dotenv, s3_admin) -> None:  # type: ignore[no-untyped-def]
    with httpx.Client(base_url=base, headers=HEADERS, timeout=30) as http:
        case = http.post("/cases", json={"title": "Integration test"})
        assert case.status_code == 201, case.text
        data = samples.pdf(2)
        up = http.post(f"/cases/{case.json()['id']}/documents", data={"doc_type": "FIR", "title": "Integration test"},
                       files={"file": ("fir.pdf", data, "application/pdf")})
        assert up.status_code == 201, up.text
        body = up.json()
        assert body["sha256"] == hashlib.sha256(data).hexdigest()

        detail = http.get(f"/documents/{body['document_id']}").json()
        assert detail["versions"][0]["sha256"] == body["sha256"]
        assert detail["versions"][0]["lock_mode"] == "COMPLIANCE"

        bad = http.post(f"/cases/{case.json()['id']}/documents", data={"doc_type": "FIR", "title": "x"},
                        files={"file": ("fir.pdf", b"not a pdf", "application/pdf")})
        assert bad.status_code == 415

    bucket = dotenv.get("PRAMAAN_S3_BUCKET", "pramaan-originals")
    key = f"originals/{body['document_id']}/1/{body['sha256']}"
    versions = s3_admin.list_object_versions(Bucket=bucket, Prefix=key)["Versions"]
    assert len(versions) == 1
    head = s3_admin.head_object(Bucket=bucket, Key=key, VersionId=versions[0]["VersionId"])
    assert head["ObjectLockMode"] == "COMPLIANCE" and head["Metadata"]["sha256"] == body["sha256"]
    assert uuid.UUID(body["version_id"])
