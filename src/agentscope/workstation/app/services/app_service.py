# -*- coding: utf-8 -*-
"""Module for App related functions."""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel
from sqlmodel import Session, desc

from app.dao.app_dao import AppDAO
from app.dao.app_version_dao import AppVersionDAO
from app.exceptions.service import (
    CreateAppException,
    AppNotFoundException,
    DeleteAppException,
    AppVersionNotFoundException,
    PublishAppException,
    CopyAppException,
    UpdateAppException,
)
from app.models.app import (
    AppEntity,
    CommonConstants,
    AppStatus,
    AppVersionEntity,
    AppType,
    AppComponentType,
)
from app.schemas.app import App, AppQuery
from app.schemas.common import PaginationParams


class AppService:
    """App service class."""

    def __init__(self, session: Session):
        self.app_dao = AppDAO(session=session)
        self.app_version_dao = AppVersionDAO(session)
        self.session = session

    def create_app(self, app: App, workspace_id: str = None) -> str:
        """Create an application.

        Args:
            app: Application information.
            workspace_id: Workspace ID.

        Returns:
            Application ID.
        """
        try:
            app_id = str(uuid.uuid4()).replace("-", "")

            # Insert application
            entity = AppEntity(
                **app.model_dump(),
            )
            entity.app_id = app_id
            entity.status = AppStatus.DRAFT
            entity.creator = ""
            entity.modifier = ""
            entity.workspace_id = workspace_id
            self.app_dao.create(entity)

            # Insert application version
            version_entity = AppVersionEntity(
                **app.model_dump(),
            )
            if isinstance(app.config, BaseModel):
                app_config = json.dumps(
                    app.config.model_dump(
                        exclude_none=True,
                    ),
                    ensure_ascii=False,
                )
            else:
                app_config = (
                    json.dumps(app.config, ensure_ascii=False)
                    if (app.config)
                    else ""
                )

            version_entity.app_id = app_id
            version_entity.status = AppStatus.DRAFT
            version_entity.version = CommonConstants.APP_INIT_VERSION
            version_entity.workspace_id = workspace_id
            version_entity.creator = ""
            version_entity.modifier = ""
            version_entity.config = app_config
            self.app_version_dao.create(version_entity)

            return app_id
        except Exception as e:
            # Roll back the transaction (implementation needed based on
            # actual transaction management).
            self.session.rollback()
            raise CreateAppException() from e

    def update_app(self, app: App, workspace_id: str) -> Optional[str]:
        """Update an application.

        Args:
            app: Application information.
            workspace_id: Workspace ID.

        Returns:
            Application ID.
        """
        try:
            # Get the existing application entity.
            if not app.app_id:
                raise AppNotFoundException()
            original_app = self.get_app(
                app.app_id,
                workspace_id,
            )  # type: ignore
            if not original_app:
                raise AppNotFoundException()

            # Preserve the original state and initialize the version entity.
            status = original_app.status
            latest_version = original_app.latestVersion

            # Handle version upgrade for the published state.
            if status == AppStatus.PUBLISHED:
                status = AppStatus.PUBLISHED_EDITING
                # Copy the published version to create a new version.
                published_version = original_app.publishedVersion
                new_version = AppVersionEntity(
                    **published_version.model_dump(),
                )
                if not published_version.version:
                    published_version.version = "1"
                new_version.version = str(int(published_version.version) + 1)
                new_version.status = AppStatus.DRAFT
                new_version.config = (
                    json.dumps(app.config)
                    if app.config
                    else published_version.config
                )
                self.app_version_dao.create(new_version)
                latest_version = new_version
            else:
                # Update the existing draft version.
                if app.config:
                    if isinstance(app.config, BaseModel):
                        latest_version.config = json.dumps(
                            app.config.model_dump(),
                            ensure_ascii=False,
                        )
                    else:
                        latest_version.config = json.dumps(
                            app.config,
                            ensure_ascii=False,
                        )
                latest_version.gmt_modified = datetime.now()
                self.app_version_dao.update(
                    id=latest_version.id,  # type: ignore
                    obj_data=latest_version.model_dump(),
                    change_update_time=False,
                )

            # Update the application metadata.
            if app.name:
                original_app.name = app.name
            if app.description:
                original_app.description = app.description

            original_app.status = status
            original_app.latestVersion = latest_version
            original_app.gmt_modified = datetime.now()

            entity = AppEntity(**original_app.model_dump())
            self.app_dao.update(
                id=entity.id,  # type: ignore
                obj_data=entity.model_dump(),
                change_update_time=False,
            )

            return app.app_id
        except Exception as e:
            self.session.rollback()
            raise UpdateAppException(f"Update app failed: {str(e)}") from e

    def delete_app(
        self,
        app_id: str,
        workspace_id: str,
        account_id: str = None,
    ) -> None:
        """Delete an application.

        Args:
            app_id: Application ID.
            workspace_id: Workspace ID.
            account_id: Account ID.

        Raises:
            AppNotFoundException: Application not found.
            DeleteAppException: Delete application failed.
        """
        try:
            # get application
            app = self.get_app(app_id, workspace_id)
            if not app:
                raise AppNotFoundException()

            # soft delete application versions
            query_expression = [
                AppVersionEntity.app_id == app_id,
                AppVersionEntity.status != AppStatus.DELETED,
            ]
            update_data = {
                AppVersionEntity.status.name: AppStatus.DELETED,
                AppVersionEntity.gmt_modified.name: datetime.now(),
                AppVersionEntity.modifier.name: account_id,
            }
            self.app_version_dao.update_by_where_conditions(
                *query_expression,
                obj_data=update_data,
            )

            # Update application entity to deleted status
            app.status = AppStatus.DELETED
            app.gmt_modified = datetime.now()
            app.modifier = account_id

            entity = AppEntity(**app.model_dump())
            entity.status = AppStatus.DELETED
            entity.gmt_modified = datetime.now()
            entity.modifier = account_id
            self.app_dao.update(
                app.id,  # type: ignore
                obj_data=entity,
                change_update_time=False,
            )
        except Exception as e:
            self.session.rollback()
            raise DeleteAppException(f"Delete app failed: {str(e)}") from e

    def get_app(self, app_id: str, workspace_id: str = None) -> Optional[App]:
        """Get an application.

        Args:
            app_id: Application ID.
            workspace_id: Workspace ID.

        Returns:
            Application entity.
        """
        try:
            app_request = [
                AppEntity.app_id == app_id,
                AppEntity.workspace_id == workspace_id,
                AppEntity.status != AppStatus.DELETED,
            ]
            app = self.app_dao.get_first_by_where_conditions(*app_request)

            if not app:
                return None

            application = App(**app.model_dump())

            app_version_request = [
                AppVersionEntity.app_id == app_id,
                AppVersionEntity.status != AppStatus.DELETED,
            ]
            app_version_order_by = [
                desc(AppVersionEntity.id),
            ]
            app_version_list = (
                self.app_version_dao.get_all_by_where_conditions_and_order_by(
                    *app_version_request,
                    order_by=app_version_order_by,
                )
            )

            if app_version_list:
                application.latestVersion = app_version_list[0]
                for version in app_version_list:
                    if version.status == AppStatus.PUBLISHED:
                        application.publishedVersion = version
                        break

            application.config = (
                json.loads(
                    application.latestVersion.config,
                )
                if application.latestVersion
                and application.latestVersion.config
                else {}
            )
            application.pub_config = (
                json.loads(
                    application.publishedVersion.config,
                )
                if application.publishedVersion
                and application.publishedVersion.config
                else {}
            )
            return application
        except Exception as e:
            # Roll back the transaction (implementation needed based on
            # actual transaction management).
            self.session.rollback()
            raise CreateAppException() from e

    def list_apps(
        self,
        query: AppQuery,
        workspace_id: str = None,
    ) -> Dict[str, Any]:
        """List apps"""
        # Construct the basic query.
        query_conditions = [
            AppEntity.workspace_id == workspace_id,
            AppEntity.status != AppStatus.DELETED,
        ]

        # Add filtering conditions.
        if query.name:
            query_conditions.append(AppEntity.name.like(f"%{query.name}%"))
        if query.type:
            query_conditions.append(AppEntity.type == query.type)

        # Retrieve the total count and paginated data.
        total = self.app_dao.count_by_where_conditions(*query_conditions)

        order_by = [desc(AppEntity.gmt_modified)]

        pagination = PaginationParams(page=query.current, page_size=query.size)
        entities = self.app_dao.paginate_by_conditions(
            *query_conditions,
            order_by=order_by,
            pagination=pagination,
        )

        # Convert the DTO (Data Transfer Object).
        apps = (
            [_to_application_dto(entity) for entity in entities]
            if entities
            else []
        )

        return {
            "current": query.current,
            "size": query.size,
            "total": total,
            "records": apps,
        }

    def publish_app(self, app_id: str, workspace_id: str) -> None:
        """Publish an application."""
        try:
            # get application
            app = self.get_app(app_id, workspace_id)
            if not app:
                raise AppNotFoundException()

            # Query the latest version.
            version_query = [
                AppVersionEntity.app_id == app_id,
                AppVersionEntity.workspace_id == workspace_id,
                AppVersionEntity.status != AppStatus.DELETED,
            ]
            version_entity = (
                self.app_version_dao.get_first_by_where_conditions(
                    *version_query,
                    order_by=[desc(AppVersionEntity.id)],
                )
            )

            if not version_entity:
                raise AppVersionNotFoundException()

            # Update the version status.
            version_entity.status = AppStatus.PUBLISHED
            version_entity.gmt_modified = datetime.now()
            self.app_version_dao.update(
                version_entity.id,  # type: ignore
                version_entity.model_dump(),
                change_update_time=False,
            )

            # Update application status.
            entity = AppEntity(**app.model_dump())
            entity.status = AppStatus.PUBLISHED
            entity.gmt_modified = datetime.now()
            entity.id = app.id

            self.app_dao.update(
                app.id,  # type: ignore
                entity.model_dump(),
                change_update_time=False,
            )
        except Exception as e:
            self.session.rollback()
            raise PublishAppException() from e

    def list_app_versions(self, query: AppQuery, workspace_id: str) -> dict:
        """List application versions."""
        # Construct basic query conditions.
        query_conditions = [
            AppVersionEntity.app_id == query.app_id,
            AppVersionEntity.workspace_id == workspace_id,
            AppVersionEntity.status != AppStatus.DELETED,
        ]

        # Obtain total count and paginated data.
        total = self.app_version_dao.count_by_where_conditions(
            *query_conditions,
        )

        # Sorting conditions.
        order_by = [desc(AppVersionEntity.gmt_modified)]

        # Paginated query.
        pagination = PaginationParams(page=query.current, page_size=query.size)
        entities = self.app_version_dao.paginate_by_conditions(
            *query_conditions,
            order_by=order_by,
            pagination=pagination,
        )

        # Convert DTO object.
        versions = (
            [_to_application_version_dto(entity) for entity in entities]
            if entities
            else []
        )

        return {
            "current": query.current,
            "size": query.size,
            "total": total,
            "records": versions,
        }

    def get_app_version(
        self,
        app_id: str,
        version_id: str,
        workspace_id: str = None,
    ) -> Optional[Dict]:
        """Get an application version."""
        # Query the latest version.
        if version_id == "latest":
            query_conditions = [
                AppVersionEntity.app_id == app_id,
                AppVersionEntity.workspace_id == workspace_id,
                AppVersionEntity.status != AppStatus.DELETED,
            ]
            order_by = [desc(AppVersionEntity.id)]
            latest_version = (
                self.app_version_dao.get_first_by_where_conditions(
                    *query_conditions,
                    order_by=order_by,
                )
            )
            if not latest_version:
                raise AppVersionNotFoundException()
            return _to_application_version_dto(latest_version)

        # Query the recently released version.
        if version_id == "lastPublished":
            query_conditions = [
                AppVersionEntity.app_id == app_id,
                AppVersionEntity.workspace_id == workspace_id,
                AppVersionEntity.status == AppStatus.PUBLISHED,
            ]
            order_by = [desc(AppVersionEntity.id)]
            published_version = (
                self.app_version_dao.get_first_by_where_conditions(
                    *query_conditions,
                    order_by=order_by,
                )
            )
            if not published_version:
                raise AppVersionNotFoundException()
            return _to_application_version_dto(published_version)

        # Query the specified version.
        query_conditions = [
            AppVersionEntity.app_id == app_id,
            AppVersionEntity.version == version_id,
            AppVersionEntity.workspace_id == workspace_id,
            AppVersionEntity.status != AppStatus.DELETED,
        ]
        version_entity = self.app_version_dao.get_first_by_where_conditions(
            *query_conditions,
        )
        if not version_entity:
            raise AppVersionNotFoundException()
        return _to_application_version_dto(version_entity)

    def get_application_published(
        self,
        type: int = None,  # pylint: disable=refined-builtin
        app_name: str = None,
        codes: List[str] = None,
        workspace_id: str = None,
    ) -> List[int]:
        """Get the published application ID list."""
        # Build query conditions
        query_conditions = [
            AppEntity.workspace_id == workspace_id,
            AppEntity.status == AppStatus.PUBLISHED,
        ]

        # Exclude specified codes
        if codes:
            query_conditions.append(AppEntity.app_id.in_(codes))

        # Type filter
        if type:
            if type == AppComponentType.WORKFLOW.value:
                query_conditions.append(AppEntity.type == AppType.WORKFLOW)
            elif type == AppComponentType.AGENT.value:
                query_conditions.append(AppEntity.type == AppType.BASIC)

        # Fuzzy name search
        if app_name:
            query_conditions.append(AppEntity.name.ilike(f"%{app_name}%"))

        # Execute query
        application_entities = (
            self.app_dao.get_all_by_where_conditions_and_order_by(
                *query_conditions,
            )
        )

        # Retain the maximum ID by app_id
        id_map = {}
        for entity in application_entities:
            existing_id = id_map.get(entity.app_id)
            # passing the test entity that is not a valid entity
            if entity.id is None:
                continue
            if existing_id is None or entity.id > existing_id:
                id_map[entity.app_id] = entity.id

        return list(id_map.values())  # type: ignore

    def get_application_published_and_not_component_list(
        self,
        request: AppQuery,
        codes: List[str] = None,
        ids: List[int] = None,
    ) -> dict:
        """Get application published and not component list"""
        # Build basic query conditions
        query_conditions = [
            AppEntity.workspace_id == request.workspace_id,
            AppEntity.status == AppStatus.PUBLISHED,
        ]

        # Exclude specified codes
        if codes:
            query_conditions.append(~AppEntity.app_id.in_(codes))

        # Type filter
        if request.type:
            if request.type == AppComponentType.WORKFLOW.value:
                query_conditions.append(AppEntity.type == AppType.WORKFLOW)
            elif request.type == AppComponentType.AGENT.value:
                query_conditions.append(AppEntity.type == AppType.BASIC)

        # Fuzzy name search
        if request.app_name:
            query_conditions.append(
                AppEntity.name.ilike(f"%{request.app_name}%"),
            )

        # ID list filtering
        if ids:
            query_conditions.append(AppEntity.id.in_(ids))

        # Get total and paginated data
        total = self.app_dao.count_by_where_conditions(*query_conditions)

        # Sorting criteria
        order_by = [desc(AppEntity.gmt_create)]

        # Pagination query
        pagination = PaginationParams(
            page=request.current,
            page_size=request.size,
        )
        entities = self.app_dao.paginate_by_conditions(
            *query_conditions,
            order_by=order_by,
            pagination=pagination,
        )

        # Convert DTO objects
        apps = (
            [_to_application_dto(entity) for entity in entities]
            if entities
            else []
        )

        return {
            "current": request.current,
            "size": request.size,
            "total": total,
            "records": apps,
        }

    def copy_app(self, app_id: str, workspace_id: str, account_id: str) -> str:
        """Copy application"""
        try:
            # Obtain original application information
            source_app = self.get_app(app_id, workspace_id)
            if not source_app:
                raise AppNotFoundException()

            # Generate a new application ID
            new_app_id = str(uuid.uuid4()).replace("-", "")

            # Copy application basic information
            new_entity = AppEntity(
                **source_app.model_dump(),
            )
            new_entity.id = None
            new_entity.app_id = new_app_id
            new_entity.name = (
                f"{source_app.name}_copy_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            new_entity.status = AppStatus.DRAFT
            new_entity.gmt_create = datetime.now()
            new_entity.gmt_modified = datetime.now()
            new_entity.creator = account_id
            new_entity.modifier = account_id
            self.app_dao.create(new_entity.model_dump())

            # Copy the latest version
            if source_app.latestVersion:
                new_version = AppVersionEntity(
                    **source_app.model_dump(),
                )
                new_version.id = None
                new_version.app_id = new_app_id
                new_version.status = AppStatus.DRAFT
                new_version.version = CommonConstants.APP_INIT_VERSION
                new_version.gmt_create = datetime.now()
                new_version.gmt_modified = datetime.now()
                new_version.creator = account_id
                new_version.modifier = account_id
                self.app_version_dao.create(new_version.model_dump())

            return new_app_id
        except Exception as e:
            self.session.rollback()
            raise CopyAppException(f"Copy app failed: {str(e)}") from e


def _to_application_version_dto(entity: AppVersionEntity) -> Optional[Dict]:
    """Convert AppVersionEntity to AppVersionDTO"""
    if not entity:
        return None

    return {
        **entity.model_dump(),
        "config": json.loads(entity.config) if entity.config else None,
    }


def _to_application_dto(entity: AppEntity) -> Optional[App]:
    """Convert AppEntity to AppDTO"""
    if not entity:
        return None

    # Copy basic attributes
    app = App(
        **entity.model_dump(exclude={"latestVersion", "publishedVersion"}),
    )

    # # Processing the latest version configuration
    # if entity.latest_version and entity.latest_version.config:
    #     app.config_str = entity.latest_version.config
    #     app.config = json.loads(entity.latest_version.config) if
    #     entity.latest_version.config else None
    #
    # # Handling published version configurations
    # if entity.published_version and entity.published_version.config:
    #     app.pub_config_str = entity.published_version.config
    #     app.pub_config = json.loads(entity.published_version.config) if
    #     entity.published_version.config else None

    return app
