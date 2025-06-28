# -*- coding: utf-8 -*-
import uuid

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from app.api.deps import CurrentAccount, SessionDep
from app.schemas.file import FileInfo
from app.schemas.response import create_response
from app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
def upload_file(
    session: SessionDep,
    current_account: CurrentAccount,
    file: UploadFile = File(..., alias="files"),
    category: str = "default",
) -> dict:
    """Upload files"""
    file_service = FileService(session=session)
    file_info = file_service.upload_file(
        account_id=current_account.account_id,
        category=category,
        file=file,
    )
    return create_response(
        code="200",
        message="Update file successfully.",
        data=[FileInfo.model_validate(file_info)],
    )


@router.get("/download/{file_id}")
def load_file(
    session: SessionDep,
    current_account: CurrentAccount,
    file_id: uuid.UUID,
) -> FileResponse:
    """Download file"""
    file_service = FileService(session=session)
    file = file_service.get(
        file_id,
    )

    return FileResponse(
        path=file.storage_path,
        filename=file.filename,
        media_type=file.mime_type,
    )
