"""Evidence intake through the HTTP API (SQLite in memory and the in-memory locked store).

Each rule is tested both ways: the allowed case succeeds and the refused case fails with
the right status, writes an `upload.rejected` event, and stores nothing.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlalchemy import func, select

from app.custody.models import CustodyEvent
from app.evidence.intake import IntakeService
from app.evidence.models import Document, DocumentVersion, StorageObject

from . import samples
from .conftest import Api

IO = ("io.sharma", "IO")


@pytest.fixture
def api(make_api) -> Api:  # type: ignore[no-untyped-def]
    return make_api()


def new_case(api: Api, user: tuple[str, str] = IO) -> str:
    r = api.client.post("/cases", json={"title": "Theft at Station Road"}, headers=api.as_user(*user))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def add(api: Api, case_id: str, user_id: str, role: str, by: tuple[str, str] = IO) -> None:
    r = api.client.post(f"/cases/{case_id}/members", json={"user_id": user_id, "role": role}, headers=api.as_user(*by))
    assert r.status_code == 201, r.text


def upload(api: Api, case_id: str, data: bytes, name: str = "fir.pdf", user: tuple[str, str] = IO,
           doc_type: str = "FIR"):  # type: ignore[no-untyped-def]
    return api.client.post(f"/cases/{case_id}/documents", headers=api.as_user(*user),
                           data={"doc_type": doc_type, "title": "FIR 12/2026"},
                           files={"file": (name, data, "application/octet-stream")})


def count(api: Api, model) -> int:  # type: ignore[no-untyped-def]
    with api.sf() as s:
        return s.scalar(select(func.count()).select_from(model))


def rejected_codes(api: Api) -> list[str]:
    return [e.details["code"] for e in api.events("upload.rejected")]


# ---- the main path ---------------------------------------------------------------------

def test_upload_stores_exact_bytes_with_matching_sha256_and_one_custody_event(api: Api) -> None:
    case_id = new_case(api)
    data = samples.pdf(2)
    r = upload(api, case_id, data)
    assert r.status_code == 201, r.text
    body = r.json()
    local = hashlib.sha256(data).hexdigest()
    assert body["sha256"] == local and body["size_bytes"] == len(data)
    assert (body["media_type"], body["page_count"], body["version_no"]) == ("application/pdf", 2, 1)

    with api.sf() as s:
        v = s.get(DocumentVersion, uuid.UUID(body["version_id"]))
        assert v is not None and v.sha256 == local
        obj = s.get(StorageObject, v.storage_object_id)
        assert obj is not None and obj.sha256 == local and obj.lock_mode == "COMPLIANCE"
        assert obj.object_key == f"originals/{body['document_id']}/1/{local}"
        stored = api.store.read(obj.object_key, obj.version_id)
    assert hashlib.sha256(stored).hexdigest() == local and stored == data

    events = api.events("document.uploaded")
    assert len(events) == 1
    e = events[0]
    assert (e.actor_id, e.actor_role, str(e.document_id), str(e.version_id)) == (
        "io.sharma", "IO", body["document_id"], body["version_id"])
    assert e.details["sha256"] == local and e.details["storage_version"] == obj.version_id
    assert e.request_id and r.headers["X-Request-ID"] == e.request_id


@pytest.mark.parametrize("data, name, media", [
    (samples.png(), "scan.png", "image/png"),
    (samples.jpeg(), "photo.jpg", "image/jpeg"),
    (samples.tiff(frames=2), "scan.tiff", "image/tiff"),
], ids=["png", "jpeg", "tiff"])
def test_each_allowed_image_type_uploads(api: Api, data: bytes, name: str, media: str) -> None:
    r = upload(api, new_case(api), data, name, doc_type="statement")
    assert r.status_code == 201, r.text
    assert r.json()["media_type"] == media and r.json()["sha256"] == hashlib.sha256(data).hexdigest()


def test_one_event_per_upload(api: Api) -> None:
    case_id = new_case(api)
    for i in range(3):
        assert upload(api, case_id, samples.png(colour=("red", "green", "blue")[i]), "p.png").status_code == 201
    assert len(api.events("document.uploaded")) == 3 == count(api, DocumentVersion)


def test_file_name_is_display_only_and_never_a_path(api: Api) -> None:
    r = upload(api, new_case(api), samples.pdf(), "../../etc/passwd.pdf")
    assert r.status_code == 201
    with api.sf() as s:
        v = s.get(DocumentVersion, uuid.UUID(r.json()["version_id"]))
        assert v is not None and v.original_name == "passwd.pdf"
    assert all("passwd" not in k and ".." not in k for k in api.store.keys())


# ---- refused files ---------------------------------------------------------------------

def test_wrong_file_type_is_rejected_logged_and_not_stored(api: Api) -> None:
    case_id = new_case(api)
    r = upload(api, case_id, b"<html>not a pdf</html>", "fir.pdf")
    assert r.status_code == 415 and r.json()["error"] == "unsupported_type"
    r = upload(api, case_id, samples.png(), "fir.pdf")
    assert r.status_code == 422 and r.json()["error"] == "extension_mismatch"
    assert rejected_codes(api) == ["unsupported_type", "extension_mismatch"]
    assert api.store.keys() == [] and count(api, Document) == 0


def test_oversized_file_is_rejected_logged_and_not_stored(make_api) -> None:  # type: ignore[no-untyped-def]
    api = make_api(max_upload_bytes=64 * 1024)
    case_id = new_case(api)
    ok = samples.pdf()
    assert upload(api, case_id, ok + b"\x00" * (64 * 1024 - len(ok))).status_code == 201  # exactly at the limit
    r = upload(api, case_id, ok + b"\x00" * (64 * 1024 - len(ok) + 1))  # one byte over
    assert r.status_code == 413 and r.json()["error"] == "too_large"
    assert rejected_codes(api) == ["too_large"] and len(api.store.keys()) == 1


def test_body_far_over_the_limit_is_cut_off_before_parsing(make_api) -> None:  # type: ignore[no-untyped-def]
    api = make_api(max_upload_bytes=64 * 1024)
    case_id = new_case(api)
    huge = b"%PDF-" + b"\x00" * (200 * 1024)
    r = upload(api, case_id, huge)
    assert r.status_code == 413 and r.json()["error"] == "too_large"

    def chunks():  # type: ignore[no-untyped-def]
        for _ in range(50):
            yield b"\x00" * 8192  # no Content-Length: counted while streaming
    r = api.client.post(f"/cases/{case_id}/documents", headers={**api.as_user(*IO), "Content-Type":
                        "multipart/form-data; boundary=x"}, content=chunks())
    assert r.status_code == 413
    assert api.store.keys() == []


def test_malformed_and_page_limit_files_are_rejected(api: Api) -> None:
    case_id = new_case(api)
    assert upload(api, case_id, b"%PDF-1.7\nbroken" * 20).json()["error"] == "malformed"
    assert upload(api, case_id, samples.pdf(4)).json()["error"] == "too_many_pages"
    assert rejected_codes(api) == ["malformed", "too_many_pages"] and api.store.keys() == []


# ---- who may upload --------------------------------------------------------------------

@pytest.mark.parametrize("role", ["CLERK", "AUDITOR"])
def test_members_without_upload_role_are_refused_and_logged(api: Api, role: str) -> None:
    case_id = new_case(api)
    add(api, case_id, "member.x", role)
    r = upload(api, case_id, samples.pdf(), user=("member.x", role))
    assert r.status_code == 403 and r.json()["error"] == "role_not_allowed"
    e = api.events("upload.rejected")[0]
    assert (e.actor_role, e.details["code"], str(e.case_id)) == (role, "role_not_allowed", case_id)
    assert api.store.keys() == []


def test_supervisor_member_can_upload(api: Api) -> None:
    case_id = new_case(api)
    add(api, case_id, "sho.rao", "SUPERVISOR")
    assert upload(api, case_id, samples.pdf(), user=("sho.rao", "SUPERVISOR")).status_code == 201


def test_non_members_admins_and_role_mismatch_are_refused(api: Api) -> None:
    case_id = new_case(api)
    add(api, case_id, "clerk.k", "CLERK")
    cases = [(("io.other", "IO"), 403, "not_a_member"),
             (("admin.a", "ADMIN"), 403, "not_a_member"),
             (("clerk.k", "IO"), 403, "not_a_member")]  # added as a clerk, claims IO
    for user, status, code in cases:
        r = upload(api, case_id, samples.pdf(), user=user)
        assert (r.status_code, r.json()["error"]) == (status, code), user
    r = upload(api, str(uuid.uuid4()), samples.pdf())
    assert r.status_code == 404
    assert rejected_codes(api) == ["not_a_member"] * 3 + ["case_not_found"]
    assert api.store.keys() == []


def test_identity_is_required_and_dev_identity_can_be_off(make_api) -> None:  # type: ignore[no-untyped-def]
    api = make_api()
    assert api.client.get("/cases").status_code == 401
    assert api.client.get("/cases", headers={"X-Pramaan-User": "io.sharma", "X-Pramaan-Role": "BOSS"}).status_code == 401
    assert api.client.get("/cases", headers={"X-Pramaan-User": "x", "X-Pramaan-Role": "IO"}).status_code == 401
    off = make_api(dev_identity=False)
    r = off.client.get("/cases", headers=off.as_user(*IO))
    assert r.status_code == 401 and r.json()["error"] == "login_unavailable"


def test_only_an_io_creates_cases(api: Api) -> None:
    for role in ("SUPERVISOR", "CLERK", "AUDITOR", "ADMIN"):
        r = api.client.post("/cases", json={"title": "x"}, headers=api.as_user("someone", role))
        assert r.status_code == 403, role
    assert len(api.events("case.created")) == 0
    new_case(api)
    assert len(api.events("case.created")) == 1


# ---- corrections are new versions (FR-06) ---------------------------------------------

def version(api: Api, doc_id: str, data: bytes, reason: str = "Corrected page 2 typo", name: str = "fir.pdf",
            user: tuple[str, str] = IO):  # type: ignore[no-untyped-def]
    return api.client.post(f"/documents/{doc_id}/versions", headers=api.as_user(*user), data={"reason": reason},
                           files={"file": (name, data, "application/pdf")})


def test_correction_creates_version_2_and_version_1_is_unchanged(api: Api) -> None:
    case_id = new_case(api)
    v1_data, v2_data = samples.pdf(1), samples.pdf(2)
    first = upload(api, case_id, v1_data).json()
    r = version(api, first["document_id"], v2_data)
    assert r.status_code == 201, r.text
    second = r.json()
    assert second["version_no"] == 2 and second["document_id"] == first["document_id"]

    with api.sf() as s:
        v1 = s.get(DocumentVersion, uuid.UUID(first["version_id"]))
        assert v1 is not None
        o1 = s.get(StorageObject, v1.storage_object_id)
        assert o1 is not None and v1.sha256 == hashlib.sha256(v1_data).hexdigest()
    assert api.store.read(o1.object_key, o1.version_id) == v1_data
    e = api.events("document.version_added")
    assert len(e) == 1 and e[0].reason == "Corrected page 2 typo"

    detail = api.client.get(f"/documents/{first['document_id']}", headers=api.as_user(*IO)).json()
    assert [v["version_no"] for v in detail["versions"]] == [1, 2]
    assert detail["versions"][0]["sha256"] == first["sha256"]


def test_correction_needs_a_reason_new_content_and_an_uploader(api: Api) -> None:
    case_id = new_case(api)
    add(api, case_id, "clerk.k", "CLERK")
    data = samples.pdf()
    doc_id = upload(api, case_id, data).json()["document_id"]
    assert version(api, doc_id, samples.pdf(2), reason="  \x00 ").status_code == 422
    r = version(api, doc_id, data)
    assert r.status_code == 409 and r.json()["error"] == "same_content"
    assert version(api, doc_id, samples.pdf(2), user=("clerk.k", "CLERK")).status_code == 403
    assert version(api, str(uuid.uuid4()), samples.pdf(2)).status_code == 404
    assert rejected_codes(api) == ["invalid_request", "same_content", "role_not_allowed", "document_not_found"]
    assert count(api, DocumentVersion) == 1


# ---- list and detail -------------------------------------------------------------------

def test_list_and_detail_for_members_with_custody_events(api: Api) -> None:
    case_id = new_case(api)
    add(api, case_id, "clerk.k", "CLERK")
    add(api, case_id, "aud.m", "AUDITOR")
    doc_id = upload(api, case_id, samples.pdf()).json()["document_id"]

    for user in (IO, ("clerk.k", "CLERK")):
        listed = api.client.get(f"/cases/{case_id}/documents", headers=api.as_user(*user))
        assert listed.status_code == 200 and [d["id"] for d in listed.json()] == [doc_id]
        detail = api.client.get(f"/documents/{doc_id}", headers=api.as_user(*user))
        assert detail.status_code == 200 and detail.json()["versions"][0]["lock_mode"] == "COMPLIANCE"
    assert len(api.events("document.listed")) == 2 and len(api.events("document.viewed")) == 2

    # Auditors see custody records, not document data (SCOPE.md 2); outsiders see nothing.
    assert api.client.get(f"/documents/{doc_id}", headers=api.as_user("aud.m", "AUDITOR")).status_code == 403
    assert api.client.get(f"/documents/{doc_id}", headers=api.as_user("io.other", "IO")).status_code == 403
    assert api.client.get(f"/cases/{case_id}/documents", headers=api.as_user("io.other", "IO")).status_code == 403
    assert api.client.get(f"/documents/{uuid.uuid4()}", headers=api.as_user(*IO)).status_code == 404
    assert len(api.events("document.viewed")) == 2  # refused reads did not count as views

    mine = api.client.get("/cases", headers=api.as_user(*IO)).json()
    assert [c["id"] for c in mine] == [case_id] and mine[0]["case_number"].startswith("PRM-")
    assert api.client.get("/cases", headers=api.as_user("io.other", "IO")).json() == []


# ---- failures between storage and database --------------------------------------------

def test_storage_outage_saves_nothing(api: Api) -> None:
    case_id = new_case(api)
    api.store.fail_next_put = True
    r = upload(api, case_id, samples.pdf())
    assert r.status_code == 503 and r.json()["error"] == "storage_unavailable"
    assert count(api, Document) == 0 and len(api.events("document.uploaded")) == 0


def test_database_failure_after_storage_records_the_orphaned_object(api: Api, monkeypatch: pytest.MonkeyPatch) -> None:
    case_id = new_case(api)

    def broken(*a, **k):  # type: ignore[no-untyped-def]
        raise RuntimeError("database went away")
    monkeypatch.setattr(IntakeService, "_rows", broken)
    r = upload(api, case_id, samples.pdf())
    assert r.status_code == 500 and r.json()["error"] == "internal_error" and "database" not in r.text
    assert count(api, Document) == 0 and count(api, DocumentVersion) == 0  # rolled back together
    orphan = api.events("storage.orphaned")
    assert len(orphan) == 1 and orphan[0].details["object_key"] == api.store.keys()[0]


def test_errors_do_not_echo_submitted_values(api: Api) -> None:
    case_id = new_case(api)
    r = api.client.post(f"/cases/{case_id}/documents", headers=api.as_user(*IO),
                        data={"doc_type": "<script>secret-title</script>", "title": "t"},
                        files={"file": ("a.pdf", samples.pdf(), "application/pdf")})
    assert r.status_code == 422 and "secret-title" not in r.text
    with api.sf() as s:
        assert s.scalar(select(func.count()).select_from(CustodyEvent)
                        .where(CustodyEvent.event_type == "upload.rejected")) == 1
