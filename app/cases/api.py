"""Case endpoints: create, list mine, add a member. nginx serves these under /api/."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from ..access.identity import Actor, current_actor
from ..deps import client_ip, session_factory
from . import service

router = APIRouter(prefix="/cases", tags=["cases"])
ActorDep = Annotated[Actor, Depends(current_actor)]
SessionsDep = Annotated[sessionmaker[Session], Depends(session_factory)]


class CaseIn(BaseModel):
    title: str = Field(min_length=1, max_length=400)


class CaseOut(BaseModel):
    id: uuid.UUID
    case_number: str
    title: str
    created_at: datetime
    your_role: str


class MemberIn(BaseModel):
    user_id: str = Field(min_length=3, max_length=64)
    role: str = Field(min_length=2, max_length=16)


class MemberOut(BaseModel):
    case_id: uuid.UUID
    user_id: str
    role: str


@router.post("", status_code=201)
def create_case(body: CaseIn, request: Request, actor: ActorDep, sf: SessionsDep) -> CaseOut:
    c = service.create_case(sf, actor, body.title, client_ip(request))
    return CaseOut(id=c.id, case_number=c.case_number, title=c.title, created_at=c.created_at, your_role=actor.role)


@router.get("")
def list_cases(actor: ActorDep, sf: SessionsDep) -> list[CaseOut]:
    return [CaseOut(id=c.id, case_number=c.case_number, title=c.title, created_at=c.created_at, your_role=role)
            for c, role in service.list_cases(sf, actor)]


@router.post("/{case_id}/members", status_code=201)
def add_member(case_id: uuid.UUID, body: MemberIn, request: Request, actor: ActorDep, sf: SessionsDep) -> MemberOut:
    m = service.add_member(sf, actor, case_id, body.user_id, body.role, client_ip(request))
    return MemberOut(case_id=m.case_id, user_id=m.user_id, role=m.role)
