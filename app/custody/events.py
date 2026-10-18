"""Write custody events. Callers pass the session, so an event commits or rolls back
together with the change it describes."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..access.identity import Actor
from ..logs import request_id_var
from .models import EVENT_TYPES, CustodyEvent


def record(session: Session, event_type: str, actor: Actor, *, case_id: uuid.UUID | None = None,
           document_id: uuid.UUID | None = None, version_id: uuid.UUID | None = None,
           reason: str | None = None, client_ip: str | None = None,
           details: dict[str, Any] | None = None) -> CustodyEvent:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown custody event type {event_type!r}")
    event = CustodyEvent(event_type=event_type, actor_id=actor.user_id, actor_role=actor.role,
                         case_id=case_id, document_id=document_id, version_id=version_id,
                         request_id=request_id_var.get(), client_ip=client_ip, reason=reason,
                         details=details or {})
    session.add(event)
    return event
