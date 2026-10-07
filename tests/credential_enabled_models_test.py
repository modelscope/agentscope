# -*- coding: utf-8 -*-
"""Per-credential enabled-model tests — catalog merging, schema hygiene
and user isolation, all offline."""
import tempfile
from typing import Any
from unittest import IsolatedAsyncioTestCase

import fakeredis.aioredis
from fastapi.testclient import TestClient

from agentscope.app import create_app
from agentscope.app.message_bus import RedisMessageBus
from agentscope.app.storage import RedisStorage
from agentscope.app.workspace_manager import LocalWorkspaceManager


def _fake_backends() -> tuple:
    """Build a fakeredis-backed storage and message bus."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    class _Storage(RedisStorage):
        async def __aenter__(self) -> Any:
            self._client = redis
            return self

        async def aclose(self) -> None:
            self._client = None

    class _Bus(RedisMessageBus):
        async def __aenter__(self) -> Any:
            self._client = redis
            return self

        async def aclose(self) -> None:
            self._client = None

    return _Storage(), _Bus()


class EnabledModelsTest(IsolatedAsyncioTestCase):
    """Enabled-model curation flows on a fully started app."""

    def setUp(self) -> None:
        """Start an app with the knowledge base feature left disabled."""
        # pylint: disable=consider-using-with
        workdir = self.enterContext(tempfile.TemporaryDirectory())
        storage, bus = _fake_backends()
        app = create_app(
            storage=storage,
            message_bus=bus,
            workspace_manager=LocalWorkspaceManager(workdir),
            enable_index_worker=False,
        )
        self._client = self.enterContext(TestClient(app))

    def _create_credential(
        self,
        user: str,
        data: dict,
    ) -> str:
        """Create a credential through the API and return its id."""
        response = self._client.post(
            "/credential/",
            headers={"X-User-ID": user},
            json={"data": data},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["credential_id"]

    def _catalog_names(self, user: str, provider: str) -> list[str]:
        """Fetch the model catalog for ``provider`` as ``user``."""
        body = self._client.get(
            "/model/",
            params={"provider": provider},
            headers={"X-User-ID": user},
        ).json()
        return [model["name"] for model in body["models"]]

    def test_enabled_models_merge_into_catalog(self) -> None:
        """Enabled IDs appear in the type's catalog with default metadata."""
        self._create_credential("alice", {
            "type": "openai_credential",
            "name": "demo",
            "api_key": "sk-test",
            "enabled_models": ["curated-b", "curated-a"],
        })

        names = self._catalog_names("alice", "openai_credential")

        self.assertIn("curated-a", names)
        self.assertIn("curated-b", names)
        # Built-in cards survive the merge.
        self.assertIn("gpt-4.1-mini", names)

    def test_builtin_card_not_duplicated(self) -> None:
        """An enabled ID covered by a built-in card stays a single entry."""
        self._create_credential("alice", {
            "type": "openai_credential",
            "name": "demo",
            "api_key": "sk-test",
            "enabled_models": ["gpt-4.1-mini"],
        })

        names = self._catalog_names("alice", "openai_credential")

        self.assertEqual(names.count("gpt-4.1-mini"), 1)

    def test_user_isolation(self) -> None:
        """One user's enabled models never leak into another's catalog."""
        self._create_credential("bob", {
            "type": "openai_credential",
            "name": "bob-relay",
            "api_key": "sk-bob",
            "enabled_models": ["bob-only-model"],
        })

        names = self._catalog_names("alice", "openai_credential")

        self.assertNotIn("bob-only-model", names)

    def test_provider_isolation(self) -> None:
        """Enabled models on one credential type don't reach another."""
        self._create_credential("alice", {
            "type": "openai_credential",
            "name": "demo",
            "api_key": "sk-test",
            "enabled_models": ["openai-only-model"],
        })

        names = self._catalog_names("alice", "dashscope_credential")

        self.assertNotIn("openai-only-model", names)

    def test_schemas_exclude_enabled_models(self) -> None:
        """The curation field is kept out of the credential form schemas."""
        schemas = self._client.get(
            "/credential/schemas",
            headers={"X-User-ID": "alice"},
        ).json()["schemas"]

        for schema in schemas:
            self.assertNotIn("enabled_models", schema.get("properties", {}))

    def test_catalog_requires_user_id(self) -> None:
        """The merged catalog endpoint is not exempt from X-User-ID."""
        response = self._client.get(
            "/model/",
            params={"provider": "openai_credential"},
        )

        self.assertEqual(response.status_code, 422)
