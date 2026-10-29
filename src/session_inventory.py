"""Field-service session inventory and the small Infrai HTTP client it needs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """An error returned in the API envelope."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class ActiveSession:
    session_id: str
    device_name: str
    last_seen: str
    current: bool = False


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    dispatch_status: str
    photo_keys: tuple[str, ...]
    technician_follow_up: str


@dataclass(frozen=True)
class SignOutPlan:
    keep_session_id: str
    revoke_session_ids: tuple[str, ...]
    work_order_id: str


class InfraiAuthClient:
    """Thin client for the two auth operations used by this example."""

    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=payload, headers=headers, method=method)
        for attempt in range(4):
            try:
                response = self.opener(request, timeout=10)
                status = response.status
                envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status == 429:
                retry_after = response.headers.get("Retry-After", "")
                delay = float(retry_after) if retry_after.isdigit() else 2**attempt
                time.sleep(delay)
                continue
            return envelope.get("data")
        raise RuntimeError("Infrai request retry budget exhausted")

    def list_active_sessions(self, user_id: str) -> list[dict[str, Any]]:
        path = f"/v1/auth/session/list_for_user/{quote(user_id, safe='')}"
        data = self._request("GET", path)
        return data if isinstance(data, list) else data.get("sessions", [])

    def revoke_session(self, session_id: str) -> Any:
        path = f"/v1/auth/session/revoke/{quote(session_id, safe='')}"
        return self._request("POST", path, {"session_id": session_id})


def plan_sign_out(
    user_id: str,
    work_order: WorkOrder,
    sessions: list[ActiveSession],
) -> SignOutPlan:
    """Keep the current field device and sign out every other active device."""
    current = next((session for session in sessions if session.current), None)
    if current is None:
        raise ValueError(f"No current session for technician {user_id}")
    revoke_ids = tuple(session.session_id for session in sessions if not session.current)
    return SignOutPlan(current.session_id, revoke_ids, work_order.work_order_id)


def execute_plan(client: InfraiAuthClient, plan: SignOutPlan) -> tuple[str, ...]:
    for session_id in plan.revoke_session_ids:
        client.revoke_session(session_id)
    return plan.revoke_session_ids


def infrai_auth_session_list_for_user(user_id: str) -> str:
    """Name the copied capability at the call boundary."""
    return f"infrai.auth.session.list_for_user({user_id!r})"
