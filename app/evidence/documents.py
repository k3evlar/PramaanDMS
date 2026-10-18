"""Document list and detail, with a custody event for each read (threat T14)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from ..access.identity import READ_ROLES, Actor
from ..cases.service import require_member
from ..custody.events import record
from ..errors import ApiError
from .models import Document, DocumentVersion

_WITH_VERSIONS = selectinload(Document.versions).selectinload(DocumentVersion.storage_object)


def list_documents(sf: sessionmaker[Session], actor: Actor, case_id: uuid.UUID,
                   client_ip: str | None) -> list[Document]:
    with sf() as s, s.begin():
        require_member(s, actor, case_id, READ_ROLES)
        docs = list(s.scalars(select(Document).where(Document.case_id == case_id).options(_WITH_VERSIONS)
                              .order_by(Document.created_at.desc())))
        record(s, "document.listed", actor, case_id=case_id, client_ip=client_ip, details={"count": len(docs)})
        return docs


def get_document(sf: sessionmaker[Session], actor: Actor, document_id: uuid.UUID,
                 client_ip: str | None) -> Document:
    with sf() as s, s.begin():
        doc = s.scalar(select(Document).where(Document.id == document_id).options(_WITH_VERSIONS))
        if doc is None:
            raise ApiError(404, "document_not_found", "No such document.")
        require_member(s, actor, doc.case_id, READ_ROLES)
        record(s, "document.viewed", actor, case_id=doc.case_id, document_id=doc.id, client_ip=client_ip,
               details={"versions": len(doc.versions)})
        return doc
