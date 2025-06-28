# -*- coding: utf-8 -*-
# mypy: disable-error-code=misc
import secrets
import os
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Union, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def find_env_file(max_levels: int = 3) -> str:
    current_path = os.getcwd()
    levels_checked = 0

    while levels_checked <= max_levels:
        for env_file in [".env", ".env.example"]:
            potential_path = os.path.join(current_path, env_file)
            if os.path.isfile(potential_path):
                return potential_path
            # Move up one directory level
            new_path = os.path.dirname(current_path)
            # If we've reached the root directory, break
            if new_path == current_path:
                break
            current_path = new_path
            levels_checked += 1

    # If we exit the loop without having found the file
    raise FileNotFoundError(
        f".env file not found within {max_levels} levels of {os.getcwd()}.",
    )


def parse_cors(v: Any) -> Union[list[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list):
        return v
    raise ValueError(v)


def find_project_root() -> str:
    current_path = Path(__file__)
    while current_path != current_path.parent:
        if (current_path / "frontend").exists():
            return str(current_path)
        current_path = current_path.parent
    raise FileNotFoundError("Project root not found.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/console/v1"

    LOGIN_METHOD: str = "preset_account"
    UPLOAD_METHOD: str = "file"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"

    REFRESH_SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    EMAIL_CODE_TOKEN_EXPIRE_MINUTES: int = 5
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # Logger related
    LOG_FILE: str = "./logs/app.log"
    LOG_FORMAT: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10"
    LOG_ELASTICSEARCH_URL: Optional[str] = "http://localhost:9200"
    LOG_ELASTICSEARCH_INDEX: Optional[str] = "agentscope_index"

    LOCAL_STORAGE_DIR: str = "~/.as/local_storage"
    # Oauth related
    # GITHUB_CLIENT_ID: str
    # GITHUB_CLIENT_SECRET: str
    # GOOGLE_CLIENT_ID: str
    # GOOGLE_CLIENT_SECRET: str
    # REPO_OWNER: str
    # REPO_NAME: str

    # Redis
    REDIS_SERVER: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_CELERY: int = 1
    REDIS_DB_FASTAPI_LIMITER: int = 2
    REDIS_DB_WORKFLOW: int = 3
    REDIS_DB_APP: int = 4
    REDIS_DB_JWT: int = 5
    REDIS_DB_MEMORY: int = 6
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = "redis_password"

    BACKEND_CORS_ORIGINS: Annotated[
        Union[list[AnyUrl], str],
        BeforeValidator(parse_cors),
    ] = []

    @computed_field
    @property  # type: ignore[prop-decorator]
    def all_cors_origins(self) -> list[str]:
        return [
            str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS
        ] + [
            self.FRONTEND_HOST,
        ]

    PROJECT_NAME: str = "AgentScope Workstation"
    SENTRY_DSN: Optional[HttpUrl] = None

    # Mysql config
    MYSQL_HOST: str = "localhost"
    MYSQL_USER: str = "agentscope"
    MYSQL_PASSWORD: str = "Agentscope123"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "agentscope"

    @computed_field
    @property  # type: ignore[prop-decorator]
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 25
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field
    @property  # type: ignore[prop-decorator]
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # TODO: update type to EmailStr when sqlmodel supports it
    EMAIL_TEST_USER: str = "test@example.com"
    # TODO: update type to EmailStr when sqlmodel supports it
    FIRST_SUPERUSER: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    WORKSPACE_ID: str = "1"

    def _check_default_secret(
        self,
        var_name: str,
        value: Optional[str] = None,
    ) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD",
            self.FIRST_SUPERUSER_PASSWORD,
        )

        return self


settings = Settings()  # type: ignore
