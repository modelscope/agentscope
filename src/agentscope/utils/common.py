# -*- coding: utf-8 -*-
""" Common utils."""
import base64
import contextlib
import datetime
import hashlib
import json
import os
import random
import re
import secrets
import signal
import socket
import string
import sys
import tempfile
import threading
from typing import Any, Generator, Optional, Union, Tuple, Literal, List
from urllib.parse import urlparse

import psutil
import requests


@contextlib.contextmanager
def timer(seconds: Optional[Union[int, float]] = None) -> Generator:
    """
    A context manager that limits the execution time of a code block to a
    given number of seconds.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py

    Note:
        This function only works in Unix and MainThread,
        since `signal.setitimer` is only available in Unix.

    """
    if (
        seconds is None
        or sys.platform == "win32"
        or threading.currentThread().name  # pylint: disable=W4902
        != "MainThread"
    ):
        yield
        return

    def signal_handler(*args: Any, **kwargs: Any) -> None:
        raise TimeoutError("timed out")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)

    try:
        # Enter the context and execute the code block.
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def create_tempdir() -> Generator:
    """
    A context manager that creates a temporary directory and changes the
    current working directory to it.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py
    """
    with tempfile.TemporaryDirectory() as dirname:
        with _chdir(dirname):
            yield dirname


@contextlib.contextmanager
def _chdir(path: str) -> Generator:
    """
    A context manager that changes the current working directory to the
    given path.
    The implementation of this contextmanager are borrowed from
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py
    """
    if path == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


def _requests_get(
    url: str,
    params: dict,
    headers: Optional[dict] = None,
) -> Union[dict, str]:
    """
    Sends a GET request to the specified URL with the provided query parameters
    and headers. Returns the JSON response as a dictionary.

    This function handles the request, checks for errors, logs exceptions,
        and parses the JSON response.

    Args:
        url (str): The URL to which the GET request is sent.
        params (Dict): A dictionary containing query parameters to be included
            in the request.
        headers (Optional[Dict]): An optional dictionary of HTTP headers to
            send with the request.

    Returns:
        Dict or str:
        If the request is successful, returns a dictionary containing the
        parsed JSON data.
        If the request fails, returns the error string.
    """
    # Make the request
    try:
        # Check if headers are provided, and include them if they are not None
        if headers:
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.get(url, params=params)
        # This will raise an exception for HTTP error codes
        response.raise_for_status()
    except requests.RequestException as e:
        return str(e)
    # Parse the JSON response
    search_results = response.json()
    return search_results


def _if_change_database(sql_query: str) -> bool:
    """Check whether SQL query only contains SELECT query"""
    # Compile the regex pattern outside the function for better performance
    pattern_unsafe_sql = re.compile(
        r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|TRUNCATE|USE)\b",
        re.IGNORECASE,
    )

    # Remove SQL comments
    sql_query = re.sub(r"--.*?$", "", sql_query, flags=re.MULTILINE)
    # Remove /* */ comments
    sql_query = re.sub(r"/\*.*?\*/", "", sql_query, flags=re.DOTALL)
    # Matching non-SELECT statements with regular expressions
    if pattern_unsafe_sql.search(sql_query):
        return False
    return True


def _get_timestamp(
    format_: str = "%Y-%m-%d %H:%M:%S",
    time: datetime.datetime = None,
) -> str:
    """Get current timestamp."""
    if time is None:
        return datetime.datetime.now().strftime(format_)
    else:
        return time.strftime(format_)


def to_openai_dict(item: dict) -> dict:
    """Convert `Msg` to `dict` for OpenAI API."""
    clean_dict = {}

    if "name" in item:
        clean_dict["name"] = item["name"]

    if "role" in item:
        clean_dict["role"] = item["role"]
    else:
        clean_dict["role"] = "assistant"

    if "content" in item:
        clean_dict["content"] = _convert_to_str(item["content"])
    else:
        raise ValueError("The content of the message is missing.")

    return clean_dict


def _find_available_port() -> int:
    """Get an unoccupied socket port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _check_port(port: Optional[int] = None) -> int:
    """Check if the port is available.

    Args:
        port (`int`):
            the port number being checked.

    Returns:
        `int`: the port number that passed the check. If the port is found
        to be occupied, an available port number will be automatically
        returned.
    """
    if port is None:
        new_port = _find_available_port()
        return new_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            if s.connect_ex(("localhost", port)) == 0:
                raise RuntimeError("Port is occupied.")
        except Exception:
            new_port = _find_available_port()
            return new_port
    return port


def _guess_type_by_extension(
    url: str,
) -> Literal["image", "audio", "video", "file"]:
    """Guess the type of the file by its extension."""
    extension = url.split(".")[-1].lower()

    if extension in [
        "bmp",
        "dib",
        "icns",
        "ico",
        "jfif",
        "jpe",
        "jpeg",
        "jpg",
        "j2c",
        "j2k",
        "jp2",
        "jpc",
        "jpf",
        "jpx",
        "apng",
        "png",
        "bw",
        "rgb",
        "rgba",
        "sgi",
        "tif",
        "tiff",
        "webp",
    ]:
        return "image"
    elif extension in [
        "amr",
        "wav",
        "3gp",
        "3gpp",
        "aac",
        "mp3",
        "flac",
        "ogg",
    ]:
        return "audio"
    elif extension in [
        "mp4",
        "webm",
        "mkv",
        "flv",
        "avi",
        "mov",
        "wmv",
        "rmvb",
    ]:
        return "video"
    else:
        return "file"


def _to_openai_image_url(url: str) -> str:
    """Convert an image url to openai format. If the given url is a local
    file, it will be converted to base64 format. Otherwise, it will be
    returned directly.

    Args:
        url (`str`):
            The local or public url of the image.
    """
    # See https://platform.openai.com/docs/guides/vision for details of
    # support image extensions.
    support_image_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
    )

    parsed_url = urlparse(url)

    lower_url = url.lower()

    # Web url
    if not os.path.exists(url) and parsed_url.scheme != "":
        if any(lower_url.endswith(_) for _ in support_image_extensions):
            return url

    # Check if it is a local file
    elif os.path.exists(url) and os.path.isfile(url):
        if any(lower_url.endswith(_) for _ in support_image_extensions):
            with open(url, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode(
                    "utf-8",
                )
            extension = parsed_url.path.lower().split(".")[-1]
            mime_type = f"image/{extension}"
            return f"data:{mime_type};base64,{base64_image}"

    raise TypeError(f"{url} should be end with {support_image_extensions}.")


def _download_file(url: str, path_file: str, max_retries: int = 3) -> bool:
    """Download file from the given url and save it to the given path.

    Args:
        url (`str`):
            The url of the file.
        path_file (`str`):
            The path to save the file.
        max_retries (`int`, defaults to `3`)
            The maximum number of retries when fail to download the file.
    """
    for n_retry in range(1, max_retries + 1):
        response = requests.get(url, stream=True)
        if response.status_code == requests.codes.ok:
            with open(path_file, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return True
        else:
            raise RuntimeError(
                f"Failed to download file from {url} (status code: "
                f"{response.status_code}). Retry {n_retry}/{max_retries}.",
            )
    return False


def _generate_random_code(
    length: int = 6,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
) -> str:
    """Get random code."""
    characters = ""
    if uppercase:
        characters += string.ascii_uppercase
    if lowercase:
        characters += string.ascii_lowercase
    if digits:
        characters += string.digits
    return "".join(secrets.choice(characters) for i in range(length))


def _generate_id_from_seed(seed: str, length: int = 8) -> str:
    """Generate random id from seed str.

    Args:
        seed (`str`): seed string.
        length (`int`): generated id length.
    """
    hasher = hashlib.sha256()
    hasher.update(seed.encode("utf-8"))
    hash_digest = hasher.hexdigest()

    random.seed(hash_digest)
    id_chars = [
        random.choice(string.ascii_letters + string.digits)
        for _ in range(length)
    ]
    return "".join(id_chars)


def _is_web_url(url: str) -> bool:
    """Whether the url is accessible from the Web.

    Args:
        url (`str`):
            The url to check.

    Note:
        This function is not perfect, it only checks if the URL starts with
        common web protocols, e.g., http, https, ftp, oss.
    """
    parsed_url = urlparse(url)
    return parsed_url.scheme in ["http", "https", "ftp", "oss"]


def _is_json_serializable(obj: Any) -> bool:
    """Check if the given object is json serializable."""
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False


def _convert_to_str(content: Any) -> str:
    """Convert the content to string.

    Note:
        For prompt engineering, simply calling `str(content)` or
        `json.dumps(content)` is not enough.

        - For `str(content)`, if `content` is a dictionary, it will turn double
        quotes to single quotes. When this string is fed into prompt, the LLMs
        may learn to use single quotes instead of double quotes (which
        cannot be loaded by `json.loads` API).

        - For `json.dumps(content)`, if `content` is a string, it will add
        double quotes to the string. LLMs may learn to use double quotes to
        wrap strings, which leads to the same issue as `str(content)`.

        To avoid these issues, we use this function to safely convert the
        content to a string used in prompt.

    Args:
        content (`Any`):
            The content to be converted.

    Returns:
        `str`: The converted string.
    """

    if isinstance(content, str):
        return content
    elif isinstance(content, (dict, list, int, float, bool, tuple)):
        return json.dumps(content, ensure_ascii=False)
    else:
        return str(content)


def _join_str_with_comma_and(elements: List[str]) -> str:
    """Return the JSON string with comma, and use " and " between the last two
    elements."""

    if len(elements) == 0:
        return ""
    elif len(elements) == 1:
        return elements[0]
    elif len(elements) == 2:
        return " and ".join(elements)
    else:
        return ", ".join(elements[:-1]) + f", and {elements[-1]}"


class ImportErrorReporter:
    """Used as a placeholder for missing packages.
    When called, an ImportError will be raised, prompting the user to install
    the specified extras requirement.
    """

    def __init__(self, error: ImportError, extras_require: str = None) -> None:
        """Init the ImportErrorReporter.

        Args:
            error (`ImportError`): the original ImportError.
            extras_require (`str`): the extras requirement.
        """
        self.error = error
        self.extras_require = extras_require

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self._raise_import_error()

    def __getattr__(self, name: str) -> Any:
        return self._raise_import_error()

    def __getitem__(self, __key: Any) -> Any:
        return self._raise_import_error()

    def _raise_import_error(self) -> Any:
        """Raise the ImportError"""
        err_msg = f"ImportError occorred: [{self.error.msg}]."
        if self.extras_require is not None:
            err_msg += (
                f" Please install [{self.extras_require}] version"
                " of agentscope."
            )
        raise ImportError(err_msg)


def _hash_string(
    data: str,
    hash_method: Literal["sha256", "md5", "sha1"],
) -> str:
    """Hash the string data."""
    hash_func = getattr(hashlib, hash_method)()
    hash_func.update(data.encode())
    return hash_func.hexdigest()


def _get_process_creation_time() -> datetime.datetime:
    """Get the creation time of the process."""
    pid = os.getpid()
    # Find the process by pid
    current_process = psutil.Process(pid)
    # Obtain the process creation time
    create_time = current_process.create_time()
    # Change the timestamp to a readable format
    return datetime.datetime.fromtimestamp(create_time)


def _is_process_alive(
    pid: int,
    create_time_str: str,
    create_time_format: str = "%Y-%m-%d %H:%M:%S",
    tolerance_seconds: int = 10,
) -> bool:
    """Check if the process is alive by comparing the actual creation time of
    the process with the given creation time.

    Args:
        pid (`int`):
            The process id.
        create_time_str (`str`):
            The given creation time string.
        create_time_format (`str`, defaults to `"%Y-%m-%d %H:%M:%S"`):
            The format of the given creation time string.
        tolerance_seconds (`int`, defaults to `10`):
            The tolerance seconds for comparing the actual creation time with
            the given creation time.

    Returns:
        `bool`: True if the process is alive, False otherwise.
    """
    try:
        # Try to create a process object by pid
        proc = psutil.Process(pid)
        # Obtain the actual creation time of the process
        actual_create_time_timestamp = proc.create_time()

        # Convert the given creation time string to a datetime object
        given_create_time_datetime = datetime.datetime.strptime(
            create_time_str,
            create_time_format,
        )

        # Calculate the time difference between the actual creation time and
        time_difference = abs(
            actual_create_time_timestamp
            - given_create_time_datetime.timestamp(),
        )

        # Compare the actual creation time with the given creation time
        if time_difference <= tolerance_seconds:
            return True

    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        # If the process is not found, access is denied, or the process is a
        # zombie process, return False
        return False

    return False


def _is_windows() -> bool:
    """Check if the system is Windows."""
    return os.name == "nt"


def _map_string_to_color_mark(
    target_str: str,
) -> Tuple[str, str]:
    """Map a string into an index within a given length.

    Args:
        target_str (`str`):
            The string to be mapped.

    Returns:
        `Tuple[str, str]`: A color marker tuple
    """
    color_marks = [
        ("\033[90m", "\033[0m"),
        ("\033[91m", "\033[0m"),
        ("\033[92m", "\033[0m"),
        ("\033[93m", "\033[0m"),
        ("\033[94m", "\033[0m"),
        ("\033[95m", "\033[0m"),
        ("\033[96m", "\033[0m"),
        ("\033[97m", "\033[0m"),
    ]

    hash_value = int(hashlib.sha256(target_str.encode()).hexdigest(), 16)
    index = hash_value % len(color_marks)
    return color_marks[index]


def _generate_new_runtime_id() -> str:
    """Generate a new random runtime id."""
    _RUNTIME_ID_FORMAT = "run_%Y%m%d-%H%M%S_{}"
    return _get_timestamp(_RUNTIME_ID_FORMAT).format(
        _generate_random_code(uppercase=False),
    )
