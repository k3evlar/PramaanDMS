"""Case creation, membership and the per-case access check."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ..access.identity import ADD_MEMBER_ROLES, ADDABLE_ROLES, CREATE_CASE_ROLES, USER_RE, Actor
from ..custody.events import record
from ..errors import ApiError
from ..validation import InvalidText, clean_text
from .models import Case, CaseMember


def new_case_number() -> str:
    # Server-generated (REQUIREMENTS.md 4.1). The FIR number itself lives in the documents.
    return f"PRM-{datetime.now(timezone.utc).year}-{secrets.token_hex(4).upper()}"


def require_member(s: Session, actor: Actor, case_id: uuid.UUID, allowed: frozenset[str]) -> Case:
    """Deny by default: the case must exist, the actor must be a member with the role they
    act as, and that role must be allowed for the action."""
    case = s.get(Case, case_id)
    if case is None:
        raise ApiError(404, "case_not_found", "No such case.")
    member = s.get(CaseMember, (case_id, actor.user_id))
    if member is None or member.role != actor.role:
        raise ApiError(403, "not_a_member", "You are not a member of this case.")
    if actor.role not in allowed:
        raise ApiError(403, "role_not_allowed", "Your role cannot do this.")
    return case


def create_case(sf: sessionmaker[Session], actor: Actor, title: str, client_ip: str | None) -> Case:
    if actor.role not in CREATE_CASE_ROLES:
        raise ApiError(403, "role_not_allowed", "Only an Investigating Officer can create a case.")
    try:
        title = clean_text(title, field="title", max_len=200)
    except InvalidText as e:
        raise ApiError(422, "invalid_request", str(e)) from None
    for _ in range(3):
        try:
            with sf() as s, s.begin():
                case = Case(case_number=new_case_number(), title=title, created_by=actor.user_id)
                case.members.append(CaseMember(user_id=actor.user_id, role=actor.role))
                s.add(case)
                s.flush()
                record(s, "case.created", actor, case_id=case.id, client_ip=client_ip,
                       details={"case_number": case.case_number})
            return case
        except IntegrityError:  # case number collision (32 random bits): try a new one
            continue
    raise ApiError(503, "try_again", "Could not create the case. Try again.")


def list_cases(sf: sessionmaker[Session], actor: Actor) -> list[tuple[Case, str]]:
    with sf() as s:
        rows = s.execute(select(Case, CaseMember.role).join(CaseMember)
                         .where(CaseMember.user_id == actor.user_id, CaseMember.role == actor.role)
                         .order_by(Case.created_at.desc())).all()
        return [(c, r) for c, r in rows]


def add_member(sf: sessionmaker[Session], actor: Actor, case_id: uuid.UUID, user_id: str, role: str,
               client_ip: str | None) -> CaseMember:
    role = role.upper()
    if not USER_RE.match(user_id):
        raise ApiError(422, "invalid_request", "user_id must be 3 to 64 letters, digits, dot, hyphen or underscore.")
    if role not in ADDABLE_ROLES:
        raise ApiError(422, "invalid_request", "role must be one of " + ", ".join(sorted(ADDABLE_ROLES)) + ".")
    with sf() as s, s.begin():
        require_member(s, actor, case_id, ADD_MEMBER_ROLES)
        if s.get(CaseMember, (case_id, user_id)) is not None:
            raise ApiError(409, "already_a_member", "That user is already a member of this case.")
        member = CaseMember(case_id=case_id, user_id=user_id, role=role)
        s.add(member)
        record(s, "case.member_added", actor, case_id=case_id, client_ip=client_ip,
               details={"user_id": user_id, "role": role})
    return member
