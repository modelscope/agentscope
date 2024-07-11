# -*- coding: utf-8 -*-
"""TripAdvisor APIs for searching and retrieving location information."""

from typing import List, Any, Dict

import requests

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus


def get_tripadvisor_location_photos(
    api_key: str,
    location_id: str,
    language: str = "en",
) -> ServiceResponse:
    """
    Get photos for a specific location using
    the TripAdvisor API and return the largest one.

    Args:
        api_key (`str`):
            Your TripAdvisor API key.
        location_id (`str`):
            The location ID for the desired location.
        language (`str`, optional):
            The language for the response. Defaults to 'en'.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is a dictionary containing the largest photo information
        or error information, which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = get_tripadvisor_location_photos(
                "your_api_key", "12345", "en"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content['largest_photo'])
    """

    def find_largest_photo(photos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the photo with the largest
        dimensions from the list of photos."""
        largest_photo_info = {}
        max_area = 0

        for item in photos:
            for image_info in item["images"].values():
                height = image_info["height"]
                width = image_info["width"]
                area = height * width

                if area > max_area:
                    max_area = area
                    largest_photo_info = {
                        "url": image_info["url"],
                        "height": height,
                        "width": width,
                        "caption": item.get("caption", ""),
                        "album": item.get("album", ""),
                        "published_date": item.get("published_date", ""),
                        "id": item.get("id", ""),
                        "source": item.get("source", {}),
                        "user": item.get("user", {}),
                    }

        return largest_photo_info

    url = (
        f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/"
        f"photos?language={language}&key={api_key}"
    )
    headers = {
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            largest_photo = find_largest_photo(data["data"])
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content={"largest_photo": largest_photo},
            )
        error_detail = (
            response.json()
            .get("error", {})
            .get("message", f"HTTP Error: {response.status_code}")
        )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": error_detail},
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def search_tripadvisor(
    api_key: str,
    query: str,
    language: str = "en",
) -> ServiceResponse:
    """
    Search for locations using the TripAdvisor API.

    Args:
        api_key (`str`):
            Your TripAdvisor API key.
        query (`str`):
            The search query.
        language (`str`, optional):
            The language for the response. Defaults to 'en'.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is the JSON response from TripAdvisor API or error
        information, which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = search_tripadvisor("your_api_key", "Paris", "en")
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content)
    """
    url = (
        f"https://api.content.tripadvisor.com/api/v1/location/search?"
        f"searchQuery={query}&language={language}&key={api_key}"
    )
    headers = {
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=response.json(),
            )
        error_detail = (
            response.json()
            .get("error", {})
            .get("message", f"HTTP Error: {response.status_code}")
        )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": error_detail},
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )


def get_tripadvisor_location_details(
    api_key: str,
    location_id: str,
    language: str = "en",
    currency: str = "USD",
) -> ServiceResponse:
    """
    Get details for a specific location using the TripAdvisor API.

    Args:
        api_key (`str`):
            Your TripAdvisor API key.
        location_id (`str`):
            The location ID for the desired location.
        language (`str`, optional):
            The language for the response. Defaults to 'en'.
        currency (`str`, optional):
            The currency for the response. Defaults to 'USD'.

    Returns:
        `ServiceResponse`: A dictionary with two variables: `status` and
        `content`. The `status` variable is from the ServiceExecStatus enum,
        and `content` is the JSON response from TripAdvisor API or error
        information, which depends on the `status` variable.

    Example:
        .. code-block:: python

            result = get_tripadvisor_location_details(
                "your_api_key", "12345", "en", "EUR"
            )
            if result.status == ServiceExecStatus.SUCCESS:
                print(result.content)
    """
    url = (
        f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/"
        f"details?language={language}&currency={currency}&key={api_key}"
    )
    headers = {
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=response.json(),
            )
        error_detail = (
            response.json()
            .get("error", {})
            .get("message", f"HTTP Error: {response.status_code}")
        )
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": error_detail},
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content={"error": str(e)},
        )
