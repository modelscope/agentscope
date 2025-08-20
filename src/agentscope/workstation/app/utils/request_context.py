# -*- coding: utf-8 -*-
"""request context"""
import uuid
from contextvars import ContextVar
from typing import Optional, Tuple, Any, Dict
from fastapi import Request

from app.services.jwt_service import JwtService
from user_agents import parse


def parse_user_agent(user_agent_string: str) -> Dict[str, str]:
    """Parse the user agent string and return a dictionary with details."""
    try:
        user_agent = parse(user_agent_string)
        return {
            "browser": f"{user_agent.browser.family} "
            f"{user_agent.browser.version_string}",
            "os": f"{user_agent.os.family} {user_agent.os.version_string}",
            "device": f"{user_agent.device.family}",
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc,
        }
    except Exception:
        return {
            "raw_user_agent": user_agent_string,
        }


def get_ip_address(request: Request) -> str:
    """Get the client's IP address from the request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def get_request_id_from_header(request: Request) -> Optional[str]:
    """Extract request ID from headers."""
    HEADERS = {
        "X-Request-ID",
        "Request-ID",
        "X-Correlation-ID",
        "Correlation-ID",
    }
    for header in HEADERS:
        if header in request.headers:
            return request.headers[header]
    return None


def get_authorization_scheme_param(
    authorization_header_value: Optional[str],
) -> Tuple[str, str]:
    """Extract the authorization scheme and parameter from an
    authorization header."""
    if not authorization_header_value:
        return "", ""
    scheme, _, param = authorization_header_value.partition(" ")
    return scheme, param


def get_token(request: Request) -> Optional[str]:
    """Get the token from the request."""
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        return None
    return param


class RequestContext:
    """Request context."""

    # Define ContextVars
    request_id: str = "no_request_id"
    user_id: str = "no_user_id"
    tenant_id: str = "no_tenant_id"
    ip_address: str = "no_ip_address"
    user_agent: str = "no_user_agent"
    browser_info: dict = {}

    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        """Create a RequestContext from a request."""
        instance = cls()
        instance.request_id = get_request_id_from_header(request) or str(
            uuid.uuid4(),
        )
        token = get_token(request)
        if token:
            payload = JwtService().decode(token) or {}
            instance.user_id = payload.get("user_id", "no_user_id")
            instance.tenant_id = payload.get(
                "tenant_id",
                instance.user_id,
            )  # Assuming tenant_id can alternate

        instance.ip_address = get_ip_address(request)
        instance.user_agent = request.headers.get(
            "User-Agent",
            "Unknown User Agent",
        )
        instance.browser_info = parse_user_agent(instance.user_agent)

        return instance

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RequestContext to a dictionary."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "browser_info": self.browser_info,
        }


request_context_var: ContextVar[RequestContext] = ContextVar(
    "request_context",
    default=RequestContext(),
)
