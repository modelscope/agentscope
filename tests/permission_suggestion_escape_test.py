# -*- coding: utf-8 -*-
"""Test cases for glob escaping in Write/Edit permission suggestions.

``generate_suggestions`` builds a glob pattern by appending ``/**`` to the
parent directory of the invoked path. That parent is a literal filesystem
path, so any character fnmatch treats as a pattern metacharacter (``[``,
``?``, ``*``) must be escaped first — otherwise the approved rule neither
covers the invocation it was generated from, nor stays inside that
directory.
"""
import unittest
from typing import Any, List
from unittest.async_case import IsolatedAsyncioTestCase

from agentscope.permission import (
    PermissionBehavior,
    PermissionContext,
    PermissionEngine,
    PermissionMode,
    PermissionRule,
)
from agentscope.tool import Edit, Write


BRACKETED_PATH = "/tmp/probe/reports [2024]/out.csv"
SIBLING_PATH = "/tmp/probe/reports 2/a.py"
PLAIN_PATH = "/tmp/probe/reports/out.csv"


def _dumped(rules: List[PermissionRule]) -> List[dict[str, Any]]:
    """Serialize permission rules for whole-structure comparison.

    Args:
        rules (`List[PermissionRule]`):
            The rules to serialize

    Returns:
        `List[dict]`:
            Each rule as a dictionary
    """
    return [rule.model_dump() for rule in rules]


class WriteSuggestionRoundTripTest(IsolatedAsyncioTestCase):
    """An approved Write suggestion must cover the call it came from."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.tool = Write()

    async def test_plain_parent_dir_suggestion(self) -> None:
        """Test the suggestion for a path without metacharacters."""
        suggestions = await self.tool.generate_suggestions(
            {"file_path": PLAIN_PATH, "content": "x"},
        )

        self.assertEqual(
            _dumped(suggestions),
            _dumped(
                [
                    PermissionRule(
                        tool_name="Write",
                        rule_content="/tmp/probe/reports/**",
                        behavior=PermissionBehavior.ALLOW,
                        source="suggested",
                    ),
                ],
            ),
        )

    async def test_bracketed_parent_dir_suggestion(self) -> None:
        """Test the suggestion escapes a bracketed parent directory."""
        suggestions = await self.tool.generate_suggestions(
            {"file_path": BRACKETED_PATH, "content": "x"},
        )

        self.assertEqual(
            _dumped(suggestions),
            _dumped(
                [
                    PermissionRule(
                        tool_name="Write",
                        rule_content="/tmp/probe/reports [[]2024]/**",
                        behavior=PermissionBehavior.ALLOW,
                        source="suggested",
                    ),
                ],
            ),
        )

    async def test_approved_suggestion_covers_original_call(
        self,
    ) -> None:
        """Test that approving the suggestion allows the same call."""
        tool_input = {"file_path": BRACKETED_PATH, "content": "x"}
        engine = PermissionEngine(
            PermissionContext(mode=PermissionMode.DEFAULT),
        )

        first = await engine.check_permission(self.tool, tool_input)
        self.assertEqual(first.behavior, PermissionBehavior.ASK)
        self.assertGreater(len(first.suggested_rules), 0)

        for rule in first.suggested_rules:
            engine.add_rule(rule)

        second = await engine.check_permission(self.tool, tool_input)
        self.assertEqual(second.behavior, PermissionBehavior.ALLOW)

    async def test_suggestion_does_not_grant_sibling_directory(
        self,
    ) -> None:
        """Test the rule stays inside the directory it names."""
        suggestions = await self.tool.generate_suggestions(
            {"file_path": BRACKETED_PATH, "content": "x"},
        )

        matched = await self.tool.match_rule(
            suggestions[0].rule_content,
            {"file_path": SIBLING_PATH},
        )
        self.assertFalse(matched)

    async def asyncTearDown(self) -> None:
        """Clean up test fixtures."""
        self.tool = None


class EditSuggestionRoundTripTest(IsolatedAsyncioTestCase):
    """An approved Edit suggestion must cover the call it came from."""

    async def asyncSetUp(self) -> None:
        """Set up test fixtures."""
        self.tool = Edit()

    async def test_approved_suggestion_covers_original_call(
        self,
    ) -> None:
        """Test that approving the suggestion allows the same call."""
        tool_input = {
            "file_path": BRACKETED_PATH,
            "old_string": "a",
            "new_string": "b",
        }
        engine = PermissionEngine(
            PermissionContext(mode=PermissionMode.DEFAULT),
        )

        first = await engine.check_permission(self.tool, tool_input)
        self.assertEqual(first.behavior, PermissionBehavior.ASK)
        self.assertGreater(len(first.suggested_rules), 0)

        for rule in first.suggested_rules:
            engine.add_rule(rule)

        second = await engine.check_permission(self.tool, tool_input)
        self.assertEqual(second.behavior, PermissionBehavior.ALLOW)

    async def test_suggestion_does_not_grant_sibling_directory(
        self,
    ) -> None:
        """Test the rule stays inside the directory it names."""
        suggestions = await self.tool.generate_suggestions(
            {"file_path": BRACKETED_PATH},
        )

        matched = await self.tool.match_rule(
            suggestions[0].rule_content,
            {"file_path": SIBLING_PATH},
        )
        self.assertFalse(matched)

    async def asyncTearDown(self) -> None:
        """Clean up test fixtures."""
        self.tool = None


if __name__ == "__main__":
    unittest.main()
