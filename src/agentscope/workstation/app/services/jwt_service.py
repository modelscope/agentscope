# -*- coding: utf-8 -*-
"""The jwt related services"""
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.cache.cache import Cache
from app.core.config import settings
from app.exceptions.service import InvalidTokenException


class JwtService:
    """Service layer for jwt token."""

    def __init__(self) -> None:
        """Initialize the service layer for jwt token."""
        self.secrret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.jwt_cache = Cache(db=settings.REDIS_DB_JWT)

    def encode(self, payload: dict) -> str:
        return jwt.encode(
            payload=payload,
            key=self.secrret_key,
            algorithm=self.algorithm,
        )

    def decode(self, token: str) -> dict:
        try:
            # Added cache validation logic
            signature = token.split(".")[
                -1
            ]  # Extract the signature part as the cache key.
            cached_payload = self.jwt_cache.get(signature)
            if cached_payload:
                return cached_payload

            # Original decoding logic
            payload = jwt.decode(
                jwt=token,
                key=self.secrret_key,
                algorithms=[self.algorithm],
            )

            # Added cache write logic
            expire_time = payload["exp"]
            current = self.get_current_timestamp()
            if current >= expire_time:
                raise InvalidTokenException()

            timeout = expire_time - current
            self.jwt_cache.set(signature, payload, ex=timeout)
            return payload
        except (InvalidTokenError,):
            raise InvalidTokenException()

    def get_current_timestamp(self) -> int:
        """Get the current UTC time with a second-level timestamp"""
        return int(
            datetime.now(timezone.utc).replace(microsecond=0).timestamp(),
        )


# if __name__ == '__main__':
#     account_id = "agent-ddd"
#     expire_time = datetime.now() + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
#     )
#     print(expire_time)
#     access_payload = {
#         "exp": expire_time,
#         "account_id": str(account_id),
#     }
#     # access_token = JwtService().encode(access_payload)
#     access_token="";
#     print(access_token)
#     print(JwtService().decode(access_token))
