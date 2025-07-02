# -*- coding: utf-8 -*-
"""app"""
from typing import Dict
from fastapi import APIRouter

from app.api.deps import SessionDep, AppQueryDeps, CurrentAccount
from app.core.config import settings
from app.exceptions.base import IncorrectParameterException
from app.schemas.app import App, AppQuery
from app.schemas.response import create_success_response
from app.services.app_service import AppService

router = APIRouter(prefix="/apps", tags=["apps"])


@router.post("")
async def create_app(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    session: SessionDep,
    app: App,
) -> Dict:
    """
    Create an application.
    """
    # Ensure that the application name is not empty.
    if not app.name or app.name.strip() == "":
        raise IncorrectParameterException(
            extra_info="Missing required parameter: name",
        )

    app_service = AppService(session)

    # Call the service layer to create an application.
    app_id = app_service.create_app(
        workspace_id=settings.WORKSPACE_ID,
        app=app,
    )

    # Return standardized response structure.
    return create_success_response(
        code="200",
        message="create application successfully.",
        data=app_id,
    )


@router.put("/{app_id}")
async def update_app(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    app_id: str,
    app: App,
    session: SessionDep,
) -> Dict:
    """
    Update an application.
    """
    if not app:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app",
        )

    if not app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app id",
        )

    app.app_id = app_id

    app_service = AppService(session)
    app_service.update_app(app=app, workspace_id=settings.WORKSPACE_ID)

    return create_success_response(
        code="200",
        message="update application successfully",
        data=None,
    )


@router.delete("/{app_id}")
async def delete_app(
    current_account: CurrentAccount,
    app_id: str,
    session: SessionDep,
) -> Dict:
    """
    Delete an application.
    """
    # Parameter validation.
    if not app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app id",
        )

    # Call the service layer.
    app_service = AppService(session)
    app_service.delete_app(
        app_id=app_id,
        workspace_id=settings.WORKSPACE_ID,
        account_id=current_account.account_id,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="delete application successfully",
        data=None,
    )


@router.get("/{app_id}")
async def get_app(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    app_id: str,
    session: SessionDep,
) -> Dict:
    """get app"""
    app_service = AppService(session)

    app = app_service.get_app(
        app_id=app_id,
        workspace_id=settings.WORKSPACE_ID,
    )

    return create_success_response(
        code="200",
        message="get application successfully.",
        data=app.model_dump(exclude_none=True) if app else {},
    )


@router.get("")
async def list_apps(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    query: AppQueryDeps,
    session: SessionDep = None,
) -> Dict:
    """list apps"""
    app_service = AppService(session)

    # Call the service layer to get a paginated list.
    apps_page_result = app_service.list_apps(
        query=query,
        workspace_id=settings.WORKSPACE_ID,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="get application list successfully",
        # Assuming that the return value is a Pydantic model
        data=apps_page_result,
    )


@router.post("/{app_id}/publish")
async def publish_app(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    app_id: str,
    session: SessionDep,
) -> Dict:
    """publish app"""
    # Parameter validation.
    if not app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app id",
        )

    # Call the service layer
    app_service = AppService(session)
    app_service.publish_app(
        app_id=app_id,
        workspace_id=settings.WORKSPACE_ID,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="publish application successfully",
        data=None,
    )


@router.get("/{app_id}/versions")
async def list_app_versions(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    app_id: str,
    session: SessionDep,
) -> Dict:
    """list app versions"""
    # Parameter validation.
    if not app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: app id",
        )

    # Call the service layer
    app_service = AppService(session)
    query = AppQuery(app_id=app_id)
    versions = app_service.list_app_versions(
        query=query,
        workspace_id=settings.WORKSPACE_ID,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="get application versions successfully",
        data=versions,
    )


@router.get("/{app_id}/version/{version}")
async def get_app_version(
    current_account: CurrentAccount,  # pylint: disable=unused-argument
    app_id: str,
    version: str,
    session: SessionDep,
) -> Dict:
    """get app version"""
    # Parameter validation.
    if not app_id or not version:
        raise IncorrectParameterException(
            extra_info="Missing required parameters: appId or version",
        )

    app_service = AppService(session)

    # Call the service layer
    app_version = app_service.get_app_version(
        app_id=app_id,
        version_id=version,
        workspace_id=settings.WORKSPACE_ID,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="get application version successfully",
        data=app_version,
    )


@router.post("/{app_id}/copy")
async def copy_app(
    current_account: CurrentAccount,
    app_id: str,
    session: SessionDep,
) -> Dict:
    """copy app"""
    # Parameter validation.
    if not app_id:
        raise IncorrectParameterException(
            extra_info="Missing required parameter: appId",
        )

    app_service = AppService(session)

    # Call the service layer
    new_app_id = app_service.copy_app(
        app_id=app_id,
        workspace_id=settings.WORKSPACE_ID,
        account_id=current_account.account_id,
    )

    # Return a standardized response.
    return create_success_response(
        code="200",
        message="copy application successfully",
        data=new_app_id,
    )
