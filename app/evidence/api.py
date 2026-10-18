"""Evidence endpoints: upload, add a corrected version, list and detail.

nginx serves these under /api/ (frontend/nginx.conf strips the prefix).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from ..access.identity import Actor, current_actor
from ..deps import client_ip, object_store, session_factory
from . import documents
from .intake import IntakeResult, IntakeService
from .models import Document, DocumentVersion
from .storage import ObjectStore

router = APIRouter(tags=["evidence"])
ActorDep = Annotated[Actor, Depends(current_actor)]
SessionsDep = Annotated[sessionmaker[Session], Depends(session_factory)]
StoreDep = Annotated[ObjectStore, Depends(object_store)]


class UploadOut(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    version_no: int
    sha256: str
    size_bytes: int
    media_type: str
    page_count: int


class VersionOut(BaseModel):
    id: uuid.UUID
    version_no: int
    sha256: str
    size_bytes: int
    media_type: str
    page_count: int
    original_name: str
    reason: str | None
    uploaded_by: str
    uploaded_at: datetime
    lock_mode: str
    retain_until: datetime


class DocumentOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    doc_type: str
    title: str
    created_by: str
    created_at: datetime
    versions: list[VersionOut]


def _upload_out(r: IntakeResult) -> UploadOut:
    return UploadOut(document_id=r.document_id, version_id=r.version_id, version_no=r.version_no, sha256=r.sha256,
                     size_bytes=r.size_bytes, media_type=r.media_type, page_count=r.page_count)


def _version_out(v: DocumentVersion) -> VersionOut:
    return VersionOut(id=v.id, version_no=v.version_no, sha256=v.sha256, size_bytes=v.size_bytes,
                      media_type=v.media_type, page_count=v.page_count, original_name=v.original_name,
                      reason=v.reason, uploaded_by=v.uploaded_by, uploaded_at=v.uploaded_at,
                      lock_mode=v.storage_object.lock_mode, retain_until=v.storage_object.retain_until)


def _document_out(d: Document) -> DocumentOut:
    return DocumentOut(id=d.id, case_id=d.case_id, doc_type=d.doc_type, title=d.title, created_by=d.created_by,
                       created_at=d.created_at, versions=[_version_out(v) for v in d.versions])


def _service(request: Request, sf: sessionmaker[Session], store: ObjectStore) -> IntakeService:
    return IntakeService(sf, store, request.app.state.settings)


@router.post("/cases/{case_id}/documents", status_code=201)
def upload_document(case_id: uuid.UUID, request: Request, actor: ActorDep, sf: SessionsDep, store: StoreDep,
                    file: Annotated[UploadFile, File()], doc_type: Annotated[str, Form(max_length=32)],
                    title: Annotated[str, Form(max_length=400)]) -> UploadOut:
    r = _service(request, sf, store).upload_new(actor, case_id, doc_type, title, file.file, file.filename,
                                                client_ip(request))
    return _upload_out(r)


@router.post("/documents/{document_id}/versions", status_code=201)
def add_version(document_id: uuid.UUID, request: Request, actor: ActorDep, sf: SessionsDep, store: StoreDep,
                file: Annotated[UploadFile, File()], reason: Annotated[str, Form(max_length=1000)]) -> UploadOut:
    r = _service(request, sf, store).add_version(actor, document_id, reason, file.file, file.filename,
                                                 client_ip(request))
    return _upload_out(r)


@router.get("/cases/{case_id}/documents")
def list_documents(case_id: uuid.UUID, request: Request, actor: ActorDep, sf: SessionsDep) -> list[DocumentOut]:
    return [_document_out(d) for d in documents.list_documents(sf, actor, case_id, client_ip(request))]


@router.get("/documents/{document_id}")
def get_document(document_id: uuid.UUID, request: Request, actor: ActorDep, sf: SessionsDep) -> DocumentOut:
    return _document_out(documents.get_document(sf, actor, document_id, client_ip(request)))
