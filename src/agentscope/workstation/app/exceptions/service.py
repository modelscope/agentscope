# -*- coding: utf-8 -*-
"""The services exceptions"""

from .base import (
    NotFoundException,
    AlreadyExistsException,
    AccessDeniedException,
    IncorrectParameterException,
    InvalidException,
    ValidationError,
    InternalServerError,
)


class AuthSchemaNotFoundException(NotFoundException):
    """The authorization schema not found exception"""

    message = "Authorization schema not found"


class AuthCredentialNotFoundException(NotFoundException):
    """The authorization credential not found exception"""

    message = "Authorization credential not found"


class UserNotFoundException(NotFoundException):
    """The user not found exception"""

    message = "User not found"


class AccountNotFoundException(NotFoundException):
    """The account not found exception"""

    message = "Account not found"


class ModelNotFoundException(NotFoundException):
    """The model not found exception"""

    message = "Model not found"


class ToolNotFoundException(NotFoundException):
    """The tool not found exception"""

    message = "Tool not found"


class ProjectNotFoundException(NotFoundException):
    """The project not found exception"""

    message = "Project not found"


class GithubRepositoryNotFoundException(NotFoundException):
    """The Github repository not found exception"""

    message = "Github repository not found"


class OauthProviderNotFoundException(NotFoundException):
    """The oauth provider not found exception"""

    message = "Oauth provider not found"


class AuthSchemaAlreadyExistsException(AlreadyExistsException):
    """The authorization schema already exists exception"""

    message = "Authorization schema already exists"


class AuthCredentialAlreadyExistsException(AlreadyExistsException):
    """The authorization credential already exists exception"""

    message = "Authorization credential already exists"


class EmailAlreadyExistsException(AlreadyExistsException):
    """The email already exists exception"""

    message = "Email already exists"


class UserAlreadyExistsException(AlreadyExistsException):
    """The user already exists exception"""

    message = "User already exists"


class AccountAlreadyExistsException(AlreadyExistsException):
    """The account already exists exception"""

    message = "Account already exists"


class UserEmailAlreadyExistsException(AlreadyExistsException):
    """The user email already exists exception"""

    message = "User email already exists"


class ModelAlreadyExistsException(AlreadyExistsException):
    """The model already exists exception"""

    message = "Model already exists"


class ToolAlreadyExistsException(AlreadyExistsException):
    """The tool already exists exception"""

    message = "Tool already exists"


class ProjectAlreadyExistsException(AlreadyExistsException):
    """The project already exists exception"""

    message = "Project already exists"


class AuthSchemaAccessDeniedException(AccessDeniedException):
    """The authorization schema access denied exception"""

    message = "Authorization schema access denied"


class AuthCredentialAccessDeniedException(AccessDeniedException):
    """The authorization credential access denied exception"""

    message = "Authorization credential access denied"


class UserAccessDeniedException(AccessDeniedException):
    """The user access denied exception"""

    message = "User access denied"


class ModelAccessDeniedException(AccessDeniedException):
    """The model access denied exception"""

    message = "Model access denied"


class ToolAccessDeniedException(AccessDeniedException):
    """The tool access denied exception"""

    message = "Tool access denied"


class ProjectAccessDeniedException(AccessDeniedException):
    """The project access denied exception"""

    message = "Project access denied"


class IncorrectEmailException(IncorrectParameterException):
    """The incorrect email exception"""

    message = "Incorrect email"


class IncorrectPasswordException(IncorrectParameterException):
    """The incorrect password exception"""

    message = "Incorrect password"


class IncorrectEmailVerificationCodeException(IncorrectParameterException):
    """The incorrect email verification code exception"""

    message = "Incorrect email verification code"


class InvalidTokenException(InvalidException):
    """The invalid token exception"""

    message = "Invalid token"


class JsonSchemaValidationException(ValidationError):
    """The JSON schema validation exception"""

    message = "JSON schema validation error"


class KnowledgeBaseAccessDeniedException(AccessDeniedException):
    """The knowledge base permission exception"""

    message = "Knowledge base access denied"


class KnowledgeBaseNotFoundException(NotFoundException):
    """The knowledge base not found exception"""

    message = "Knowledge base not found"


class DocumentNotFoundException(NotFoundException):
    """The document not found exception"""

    message = "Document not found"


class DocumentAlreadyExistsException(AlreadyExistsException):
    """The document already exists exception"""

    message = "Document already exists"


class StarGithubRepoException(InternalServerError):
    """The star github repo exception"""

    message = "Failed to star github repo"


class PasswordNotSetException(InternalServerError):
    """The password not set exception"""

    message = "User has not set a password, no need to reset."


class EmailSMTPException(InternalServerError):
    """The STMP exception while sending email"""

    message = "STMP error"


class EmailTimeoutException(InternalServerError):
    """Timeout exception while sending email"""

    message = "Timeout while sending email"


class EmailUnexpectedException(InternalServerError):
    """Unexpecte exception while sending email"""

    message = "Unexpecte exception while sending email"


class ElasticsearchException(InternalServerError):
    """Elasticsearch exception"""

    message = "Elasticsearch search failed"


class CreateAppException(InternalServerError):
    """App exception"""

    message = "Application create failed"


class AppNotFoundException(NotFoundException):
    """The app not found exception"""

    message = "Application not found"


class UpdateAppException(InternalServerError):
    """App exception"""

    message = "Application update failed"


class DeleteAppException(InternalServerError):
    """App exception"""

    message = "Application delete failed"


class AppVersionNotFoundException(NotFoundException):
    """The app version not found exception"""

    message = "Application version not found"


class PublishAppException(InternalServerError):
    """App exception"""

    message = "Application publish failed"


class CopyAppException(InternalServerError):
    """App exception"""

    message = "Application copy failed"


class ProviderNotFoundException(NotFoundException):
    """The provider not found exception"""

    message = "Provider not found"


class ProviderAlreadyExistsException(AlreadyExistsException):
    """The provider already exists exception"""

    message = "Provider already exists"


class ApiKeyNotFoundException(NotFoundException):
    """Api key not found exception"""

    message = "ApiKey not found"
