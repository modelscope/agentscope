# -*- coding: utf-8 -*-
"""The model router."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_storage
from ..storage import StorageBase
from ._schema import ListModelsResponse, ListModelsRequest
from ...credential import CredentialFactory
from ...model import ModelCard

model_router = APIRouter(
    prefix="/model",
    tags=["model"],
    responses={404: {"description": "Not found"}},
)

# Metadata synthesized for enabled model IDs that have no built-in card.
# The IDs are known-callable on the user's endpoint; the context/output
# sizes are generous placeholders, not vendor claims.
_DEFAULT_CONTEXT_SIZE = 131_072
_DEFAULT_OUTPUT_SIZE = 16_384


@model_router.get(
    "/",
    response_model=ListModelsResponse,
    summary="List all candidate models under the given credential type",
)
async def list_models(
    body: ListModelsRequest = Depends(),
    user_id: str = Depends(get_current_user_id),
    storage: StorageBase = Depends(get_storage),
) -> ListModelsResponse:
    """Return all candidate models under the given credential type.

    Built-in cards plus, for every credential of this type owned by the
    caller, the model IDs they explicitly enabled there (curated from the
    endpoint's live list). Enabled IDs already covered by a built-in card
    keep the built-in metadata; the rest render with default metadata.

    Args:
        body (ListModelsRequest): The request body.
        user_id (`str`): Injected authenticated user ID.
        storage (`StorageBase`): Injected storage backend.

    Returns:
        `ListModelsResponse`: The response body.
    """
    credential_cls = CredentialFactory.get_credential_class(body.provider)
    if credential_cls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{body.provider}' not found.",
        )

    model_cls = credential_cls.get_chat_model_class()
    models = model_cls.list_models()

    known = {model.name for model in models}
    for record in await storage.list_credentials(user_id):
        if record.data.get("type") != body.provider:
            continue
        for model_id in record.data.get("enabled_models") or []:
            if model_id in known:
                continue
            known.add(model_id)
            models.append(
                ModelCard.from_defaults(
                    name=model_id,
                    parameter_class=model_cls.Parameters,
                    context_size=_DEFAULT_CONTEXT_SIZE,
                    output_size=_DEFAULT_OUTPUT_SIZE,
                ),
            )

    return ListModelsResponse(models=models, total=len(models))
