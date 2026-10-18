"""Shared FastAPI dependencies: database sessions, object store, caller details."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from .evidence.storage import ObjectStore


def session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def object_store(request: Request) -> ObjectStore:
    return request.app.state.object_store


def client_ip(request: Request) -> str | None:
    # The direct peer (nginx in the stack). Trusting X-Forwarded-For comes with Phase 22.
    return request.client.host[:45] if request.client else None
