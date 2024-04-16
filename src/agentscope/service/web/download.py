# -*- coding: utf-8 -*-
"""Download file from URL."""
import os

import requests
from tqdm import tqdm

from agentscope.service import ServiceResponse, ServiceExecStatus


def download_from_url(
    url: str,
    filepath: str,
    timeout: int = 120,
    retries: int = 3,
) -> ServiceResponse:
    """Download file from the given url to the specified location.

    Args:
        url (`str`):
            The URL of the file to download.
        filepath (`str`):
            The path to save the downloaded file.
        timeout (`int`, defaults to `120`):
            The timeout for the download request.
        retries (`int`, defaults to `3`):
            The number of retries for the download request.

    Returns:
        `ServiceResponse`: A `ServiceResponse` object that contains execution
        results or error message.
    """

    # Check if the target file exists already
    if os.path.exists(filepath):
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=f"The file {filepath} already exists.",
        )

    # Download the file
    try:
        session = requests.Session()
        response = session.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        file_size = int(response.headers.get("content-length", 0))
        chunk_size = 1024 * 32  # 32 KB
        progress_bar = tqdm(total=file_size, unit="iB", unit_scale=True)

        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                progress_bar.update(len(chunk))
                file.write(chunk)
        progress_bar.close()

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content={
                "url": url,
                "saved_file_path": filepath,
            },
        )
    except requests.exceptions.RequestException as e:
        if retries > 0:
            # remove the incomplete file
            if os.path.exists(filepath):
                os.remove(filepath)
            # retry the download
            return download_from_url(url, filepath, timeout, retries - 1)
        else:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Failed to download file from {url}: {str(e)}",
            )
