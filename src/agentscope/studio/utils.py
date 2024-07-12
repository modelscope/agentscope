# -*- coding: utf-8 -*-
"""
This module provides utilities for securing views in a web application with
authentication and authorization checks.

Functions:
    require_auth - A decorator for protecting views by requiring
        authentication.
"""
from functools import wraps
from flask import request, session, redirect, url_for


def require_auth(
    redirect_url: str = "_home",
    fail_with_exception: bool = False,
    ip: str = "",
    **decorator_kwargs,
):
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
        ip (str): The request IP address to check against '127.0.0.1' for
            bypass.
        **decorator_kwargs: Additional keyword arguments passed to the
            decorated view.

    Returns:
        A view function wrapped with authentication check logic.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            token_query = request.args.get("token", "")
            user_login = request.args.get("user_login", "")
            token_session = session.get("verification_token")
            valid_user_login = session.get("user_login")

            if (
                token_query
                and token_query == token_session
                and user_login == valid_user_login
            ) or ip == "127.0.0.1":
                kwargs = {
                    **kwargs,
                    **decorator_kwargs,
                    "token_query": token_query,
                    "user_login": user_login,
                }
                if ip:
                    kwargs["ip"] = ip
                return view_func(*args, **kwargs)
            else:
                if fail_with_exception:
                    raise EnvironmentError("Unauthorized access.")
                return redirect(url_for(redirect_url))

        return wrapper

    return decorator
