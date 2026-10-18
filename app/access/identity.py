"""Who is calling, and what their role allows (Phase 5 subset of the access matrix).

Real login (password and TOTP) arrives in Phase 16. Until then the API can read a
development identity from two request headers, `X-Pramaan-User` and `X-Pramaan-Role`.
This is switched on only by PRAMAAN_DEV_IDENTITY=true, which the settings refuse outside
the dev and test environments (D82). With it off, every case and document endpoint
answers 401. The header identity is not authentication: anyone who can reach the API can
claim any user, which is why it must never be on in a demo or production run.

Rules here follow docs/SCOPE.md section 2 and REQUIREMENTS.md FR-01, FR-02:
- deny by default; a user sees a case only as a member of it
- only Investigating Officers and Supervisors upload (Court Clerks verify only)
- the role a user acts with in a case is the role they were added with
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import Request

from ..cases.models import ROLES
from ..errors import ApiError

USER_RE = re.compile(r"^[A-Za-z0-9._-]{3,64}$")  # REQUIREMENTS.md 4.1, username rule

CREATE_CASE_ROLES = frozenset({"IO"})
UPLOAD_ROLES = frozenset({"IO", "SUPERVISOR"})
READ_ROLES = frozenset({"IO", "SUPERVISOR", "CLERK"})  # Auditor and Admin see no document data
ADD_MEMBER_ROLES = frozenset({"IO", "SUPERVISOR"})
ADDABLE_ROLES = frozenset({"IO", "SUPERVISOR", "CLERK", "AUDITOR"})


@dataclass(frozen=True)
class Actor:
    user_id: str
    role: str


def current_actor(request: Request) -> Actor:
    if not request.app.state.settings.dev_identity:
        raise ApiError(401, "login_unavailable", "Sign-in is not available in this build yet.")
    user = request.headers.get("x-pramaan-user", "")
    role = request.headers.get("x-pramaan-role", "").upper()
    if not USER_RE.match(user) or role not in ROLES:
        raise ApiError(401, "unauthenticated", "Sign in first.")
    return Actor(user_id=user, role=role)
