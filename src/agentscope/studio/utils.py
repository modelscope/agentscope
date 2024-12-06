# -*- coding: utf-8 -*-
"""
This module provides utilities for securing views in a web application with
authentication and authorization checks.

Functions:
    _require_auth - A decorator for protecting views by requiring
        authentication.
"""
import json
import base64
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional

import jwt
import requests
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


def get_github_headers(access_token: str) -> Dict[str, str]:
    """
    Build headers
    """
    return {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_user_status(access_token: str) -> Any:
    """
    Get user status.
    """
    url = "https://api.github.com/user"
    headers = get_github_headers(access_token)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def star_repository(
    access_token: str,
    owner: str,
    repo: str,
) -> int:
    """
    Star the Repo.
    """
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = get_github_headers(access_token)
    response = requests.put(url, headers=headers)
    return response.status_code == 204


def get_branch_sha(
    owner: str,
    repo: str,
    branch: str,
    headers: Dict[str, str],
) -> Optional[str]:
    """
    Get branch sha.
    """
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    )
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["object"]["sha"]
    return None


def upload_file(
    access_token: str,
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
    content: str,
    commit_message: str,
) -> Optional[str]:
    """
    Upload file to branch
    """
    headers = get_github_headers(access_token)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch,
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        return response.json()["content"]["sha"]
    return None


def open_pull_request(
    access_token: str,
    owner: str,
    repo: str,
    title: str,
    head_branch: str,
    base_branch: str = "main",
    body_content: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Open a pull request
    """
    headers = get_github_headers(access_token)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    data = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": f"This is an automated pull request.\n\n"
        f"Workflow description:\n"
        f"{body_content}\n\n[skip ci]",
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    return None


def fork_repo(access_token: str, owner: str, repo: str, user: str) -> bool:
    """
    Fork a repo
    """
    headers = get_github_headers(access_token)

    # Check if the repository is already forked
    forked_repo_url = f"https://api.github.com/repos/{user}/{repo}"
    response = requests.get(forked_repo_url, headers=headers)
    if response.status_code == 200:
        print("Repository is already forked.")
        return True

    # Fork the repository
    fork_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    response = requests.post(fork_url, headers=headers)
    if response.status_code == 202:
        print("Repository forked successfully.")
        return True
    else:
        print("Failed to fork the repository.")
        return False


def create_branch_with_timestamp(
    access_token: str,
    owner: str,
    repo: str,
    user: str,
    base_branch: str = "main",
) -> Optional[str]:
    """
    Create a branch with a timestamp in the forked repository based on the
    upstream base branch.
    """
    headers = get_github_headers(access_token)
    sha = get_branch_sha(owner, repo, base_branch, headers)
    if not sha:
        print(f"Failed to get the upstream {base_branch} branch.")
        return None

    # Generate a unique branch name using a timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_branch = f"feature/{timestamp}"

    create_url = f"https://api.github.com/repos/{user}/{repo}/git/refs"
    data = {
        "ref": f"refs/heads/{new_branch}",
        "sha": sha,
    }
    response = requests.post(create_url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Branch '{new_branch}' created successfully.")
        return new_branch
    else:
        print("Failed to create the branch.")
        return None
