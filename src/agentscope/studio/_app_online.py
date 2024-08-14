# -*- coding: utf-8 -*-
"""The Web Server of the AgentScope Workstation Online Version."""
import ipaddress
import json
import os
import secrets
import tempfile
from typing import Tuple, Any
from datetime import timedelta

import requests
import oss2
from loguru import logger
from flask import (
    Flask,
    Response,
    request,
    redirect,
    session,
    url_for,
    render_template,
    jsonify,
    make_response,
)
from flask_babel import Babel, refresh
from dotenv import load_dotenv

from agentscope.constants import EXPIRATION_SECONDS, FILE_SIZE_LIMIT
from agentscope.studio.utils import _require_auth, generate_jwt
from agentscope.studio._app import (
    _convert_config_to_py,
    _read_examples,
    _save_workflow,
    _delete_workflow,
    _list_workflows,
    _load_workflow,
)

_app = Flask(__name__)
_app.config["BABEL_DEFAULT_LOCALE"] = "en"

babel = Babel(_app)


def is_ip(address: str) -> bool:
    """
    Check whether the IP is the domain or not.
    """
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def get_locale() -> str:
    """
    Get current language type.
    """
    cookie = request.cookies.get("locale")
    if cookie in ["zh", "en"]:
        return cookie
    return request.accept_languages.best_match(
        _app.config.get("BABEL_DEFAULT_LOCALE"),
    )


babel.init_app(_app, locale_selector=get_locale)

load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(24)
_app.config["SECRET_KEY"] = SECRET_KEY
_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
_app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
if os.getenv("LOCAL_WORKSTATION", "false").lower() == "true":
    LOCAL_WORKSTATION = True
    IP = "127.0.0.1"
    COPILOT_IP = "127.0.0.1"
else:
    LOCAL_WORKSTATION = False
    IP = os.getenv("IP", "127.0.0.1")
    COPILOT_IP = os.getenv("COPILOT_IP", "127.0.0.1")

PORT = os.getenv("PORT", "8080")
COPILOT_PORT = os.getenv("COPILOT_PORT", "8081")

if not is_ip(IP):
    PORT = ""
if not is_ip(COPILOT_IP):
    COPILOT_PORT = ""

CLIENT_ID = os.getenv("CLIENT_ID")
OWNER = os.getenv("OWNER")
REPO = os.getenv("REPO")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

required_envs = {
    "OSS_ACCESS_KEY_ID": OSS_ACCESS_KEY_ID,
    "OSS_ACCESS_KEY_SECRET": OSS_ACCESS_KEY_SECRET,
    "CLIENT_SECRET": CLIENT_SECRET,
}

for key, value in required_envs.items():
    if not value:
        logger.warning(f"{key} is not set on envs!")


def get_oss_config() -> Tuple:
    """
    Obtain oss related configs.
    """
    return (
        OSS_ACCESS_KEY_ID,
        OSS_ACCESS_KEY_SECRET,
        OSS_ENDPOINT,
        OSS_BUCKET_NAME,
    )


def upload_to_oss(
    bucket: str,
    local_file_path: str,
    oss_file_path: str,
    is_private: bool = False,
) -> str:
    """
    Upload content to oss.
    """
    bucket.put_object_from_file(oss_file_path, local_file_path)
    if not is_private:
        bucket.put_object_acl(oss_file_path, oss2.OBJECT_ACL_PUBLIC_READ)
    file_url = (
        f"https://{bucket.bucket_name}"
        f".{bucket.endpoint.replace('http://', '')}/{oss_file_path}"
    )
    return file_url


def generate_verification_token() -> str:
    """
    Generate token.
    """
    return secrets.token_urlsafe()


def star_repository(access_token: str) -> int:
    """
    Star the Repo.
    """
    url = f"https://api.github.com/user/starred/{OWNER}/{REPO}"
    headers = {
        "Authorization": f"token {access_token}",
        "Content-Length": "0",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.put(url, headers=headers)
    return response.status_code == 204


def get_user_status(access_token: str) -> Any:
    """
    Get user status.
    """
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


@_app.route("/")
def _home() -> str:
    """
    Render the login page.
    """
    if LOCAL_WORKSTATION:
        session["verification_token"] = "verification_token"
        session["user_login"] = "local_user"
        session["jwt_token"] = generate_jwt(
            user_login="local_user",
            access_token="access_token",
            verification_token="verification_token",
            secret_key=SECRET_KEY,
            version="online",
        )
    return render_template("login.html", client_id=CLIENT_ID, ip=IP, port=PORT)


@_app.route("/oauth/callback")
def oauth_callback() -> str:
    """
    Github oauth callback.
    """
    code = request.args.get("code")
    if not code:
        return "Error: Code not found."

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        },
    ).json()

    access_token = token_response.get("access_token")
    user_status = get_user_status(access_token)
    if not access_token or not user_status:
        return (
            "Error: Access token not found or failed to fetch user "
            "information."
        )

    user_login = user_status.get("login")

    if star_repository(access_token=access_token):
        verification_token = generate_verification_token()
        # Used for compare with `verification_token` in `jwt_token`
        session["verification_token"] = verification_token
        session["user_login"] = user_login
        session["jwt_token"] = generate_jwt(
            user_login=user_login,
            access_token=access_token,
            verification_token=verification_token,
            secret_key=SECRET_KEY,
            version="online",
        )

        return redirect(
            url_for(
                "_workstation_online",
            ),
        )
    else:
        return "Error: Unable to star the repository."


@_app.route("/workstation")
@_require_auth(secret_key=SECRET_KEY)
def _workstation_online(**kwargs: Any) -> str:
    """Render the workstation page."""
    return render_template("workstation.html", **kwargs)


@_app.route("/upload-to-oss", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _upload_file_to_oss_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Upload content to oss bucket.
    """

    def write_and_upload(ct: str, user: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as tmp_file:
            tmp_file.write(ct)
            tmp_file.flush()
            ak_id, ak_secret, endpoint, bucket_name = get_oss_config()

            auth = oss2.Auth(ak_id, ak_secret)
            bucket = oss2.Bucket(auth, endpoint, bucket_name)

            file_key = f"modelscope_user/{user}_config.json"

            upload_to_oss(
                bucket,
                tmp_file.name,
                file_key,
                is_private=True,
            )

        public_url = bucket.sign_url(
            "GET",
            file_key,
            EXPIRATION_SECONDS,
            slash_safe=True,
        )
        return public_url

    content = request.json.get("data")
    user_login = session.get("user_login", "local_user")

    workflow_json = json.dumps(content, ensure_ascii=False, indent=4)
    if len(workflow_json.encode("utf-8")) > FILE_SIZE_LIMIT:
        return jsonify(
            {
                "message": f"The workflow data size exceeds "
                f"{FILE_SIZE_LIMIT/(1024*1024)} MB limit",
            },
        )

    config_url = write_and_upload(content, user_login)
    return jsonify(config_url=config_url)


@_app.route("/convert-to-py", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _online_convert_config_to_py(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Convert json config to python code and send back.
    """
    return _convert_config_to_py()


@_app.route("/read-examples", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _read_examples_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Read tutorial examples from local file.
    """
    return _read_examples()


@_app.route("/save-workflow", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _save_workflow_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Save the workflow JSON data to the local user folder.
    """
    return _save_workflow()


@_app.route("/delete-workflow", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _delete_workflow_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Deletes a workflow JSON file from the user folder.
    """
    return _delete_workflow()


@_app.route("/list-workflows", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _list_workflows_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Get all workflow JSON files in the user folder.
    """
    return _list_workflows()


@_app.route("/load-workflow", methods=["POST"])
@_require_auth(fail_with_exception=True, secret_key=SECRET_KEY)
def _load_workflow_online(**kwargs: Any) -> Response:
    # pylint: disable=unused-argument
    """
    Reads and returns workflow data from the specified JSON file.
    """
    return _load_workflow()


@_app.route("/set_locale")
def set_locale() -> Response:
    """
    Switch language.
    """
    lang = request.args.get("language")
    response = make_response(jsonify(message=lang))
    if lang == "en":
        refresh()
        response.set_cookie("locale", "en")
        return response

    if lang == "zh":
        refresh()
        response.set_cookie("locale", "zh")
        return response

    return jsonify({"data": "success"})


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number. Using default port {PORT}.")

    _app.run(host="0.0.0.0", port=PORT)
