# -*- coding: utf-8 -*-
"""
This module provides utilities for securing views in a web application with
authentication and authorization checks.

Functions:
    _require_auth - A decorator for protecting views by requiring
        authentication.
"""
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable

import jwt
from flask import session, redirect, url_for, abort
from agentscope.constants import TOKEN_EXP_TIME


def _require_auth(
    redirect_url: str = "_home",
    fail_with_exception: bool = False,
    secret_key: str = "",
    **decorator_kwargs: Any,
) -> Callable:
    """
    Decorator for view functions that requires user authentication.

    If the user is authenticated by token and user login name, or if the
    request comes from the localhost (127.0.0.1), the decorated view is
    executed. If the user is not authenticated, they are either redirected
    to the given redirect_url, or an exception is raised, depending on the
    fail_with_exception flag.

    Args:
        redirect_url (str): The endpoint to which an unauthenticated user is
            redirected.
        fail_with_exception (bool): If True, raise an exception for
            unauthorized access, otherwise redirect to the redirect_url.
        secret_key (str): The secret key for generate jwt token.
        **decorator_kwargs: Additional keyword arguments passed to the
            decorated view.

    Returns:
        A view function wrapped with authentication check logic.
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            verification_token = session.get("verification_token")
            user_login = session.get("user_login")
            jwt_token = session.get("jwt_token")

            token_dict = decode_jwt(jwt_token, secret_key=secret_key)
            valid_user_login = token_dict["user_login"]
            valid_verification_token = token_dict["verification_token"]

            if (
                verification_token == valid_verification_token
                and user_login == valid_user_login
            ):
                kwargs = {
                    **kwargs,
                    **decorator_kwargs,
                    "token_dict": token_dict,
                }
                return view_func(*args, **kwargs)
            else:
                if fail_with_exception:
                    raise EnvironmentError("Unauthorized access.")
                return redirect(url_for(redirect_url))

        return wrapper

    return decorator


def generate_jwt(
    user_login: str,
    access_token: str,
    verification_token: str,
    secret_key: str,
    version: str = None,
) -> str:
    """
    Generates a JSON Web Token (JWT) with the specified payload.

    Args:
        user_login (str): The user's login or identifier.
        access_token (str): The access token associated with the user.
        verification_token (str): A verification token for additional security.
        secret_key (str): The secret key used to sign the JWT.
        version (str, optional): Optional version of the token.

    Returns:
        str: The encoded JWT as a string.
    """
    payload = {
        "user_login": user_login,
        "access_token": access_token,
        "verification_token": verification_token,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXP_TIME),
    }
    if version:
        payload["version"] = version
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token: str, secret_key: str) -> Any:
    """
    Decodes a JSON Web Token (JWT) using the provided secret key.

    Args:
        token (str): The encoded JWT to decode.
        secret_key (str): The secret key used for decoding the JWT.

    Returns:
        dict: The payload of the decoded token if successful.

    Raises:
        abort: If the token is expired or invalid, a 401 or 403 error is
        raised.
    """

    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401, description="The provided token has expired.")
        return None
    except Exception:
        abort(
            403,
            description="The provided token is invalid. Please log in again.",
        )
        return None
