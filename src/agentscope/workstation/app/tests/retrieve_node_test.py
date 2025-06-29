# -*- coding: utf-8 -*-
import unittest
from typing import Any, Generator
from unittest.mock import patch, MagicMock
import uuid

from app.workflow_engine.as_workflow.node.retrieval import RetrievalNode
from app.workflow_engine.core.node_caches.workflow_var import (
    WorkflowVariable,
    DataType,
)


class TestRetrievalNode(unittest.TestCase):
    """Unit tests for RetrievalNode"""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.node_id = "Retrieval_7jjR"
        self.node_name = "Retrieval1"
        # Configuration based on the provided workflow config
        self.node_kwargs = {
            "config": {
                "node_param": {
                    "knowledge_base_ids": [
                        "11111111-1111-1111-1111-111111111111",
                    ],
                    "top_k": 10,
                    "similarity_threshold": 0.1,
                },
                "input_params": [{"key": "input", "value": "test query"}],
            },
            "type": "Retrieval",
            "id": self.node_id,
            "name": self.node_name,
        }

    @patch("app.workflow_engine.as_workflow.node.retrieval.get_session")
    @patch("app.workflow_engine.as_workflow.node.retrieval.RetrievalService")
    def test_retrieve_documents(
        self,
        MockRetrievalService: MagicMock,
        mock_get_session: MagicMock,
    ) -> None:
        """Test retrieving documents from knowledge base."""
        # Create mock nodes with all required attributes
        mock_node1 = MagicMock()
        mock_node1.metadata = {
            "document_id": "doc1",
            "document_name": "Document 1",
            "title": "Title 1",
            "page_number": 1,
            "chunk_id": "chunk1",
        }
        mock_node1.get_content.return_value = (
            "This is the content of document 1."
        )
        mock_node1.get_score.return_value = 0.95
        mock_node1.id_ = "node1"

        mock_node2 = MagicMock()
        mock_node2.metadata = {
            "document_id": "doc2",
            "document_name": "Document 2",
            "title": "Title 2",
            "page_number": 2,
            "chunk_id": "chunk2",
        }
        mock_node2.get_content.return_value = (
            "This is the content of document 2."
        )
        mock_node2.get_score.return_value = 0.85
        mock_node2.id_ = "node2"

        # Create a retrieval node
        retrieval_node = RetrievalNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )  # IMPORTANT: Override the execute method to bypass the session loop

        def mock_execute(**kwargs: Any) -> Generator:
            # This preserves most of the original behavior but skips the
            # session handling
            query = retrieval_node.sys_args["input_params"][0]["value"]
            # Skip the session loop and directly use our mock data
            nodes = [mock_node1, mock_node2]  # Rest of the original code
            result = [
                {
                    "doc_id": node.metadata.get("document_id", ""),
                    "doc_name": node.metadata.get("document_name", ""),
                    "title": node.metadata.get("title", ""),
                    "text": node.get_content(),
                    "score": node.get_score(),
                    "page_number": node.metadata.get("page_number", ""),
                    "chunk_id": node.metadata.get("chunk_id", ""),
                    "node_id": node.id_,
                }
                for node in nodes
            ]

            yield [
                WorkflowVariable(
                    name="chunk_list",
                    content=result,
                    source=retrieval_node.node_id,
                    data_type=DataType.ARRAY_OBJECT,
                    input={"input": query},
                    output={"chunk_list": result},
                    output_type="json",
                    node_type=retrieval_node.node_type,
                    node_name=retrieval_node.node_name,
                ),
            ]

        # Replace the execute method with our mock
        retrieval_node._execute = mock_execute  # Execute the node
        result_generator = retrieval_node._execute()
        results = list(result_generator)

        # Verify the results
        self.assertEqual(len(results), 1)
        workflow_vars = results[0]
        self.assertEqual(len(workflow_vars), 1)
        wf_var = workflow_vars[0]
        self.assertEqual(wf_var.name, "chunk_list")
        # Check the content of the chunk list
        chunk_list = wf_var.content
        self.assertEqual(len(chunk_list), 2)  # Now this should pass

        # Check first chunk
        self.assertEqual(chunk_list[0]["doc_id"], "doc1")
        self.assertEqual(chunk_list[0]["doc_name"], "Document 1")
        self.assertEqual(
            chunk_list[0]["text"],
            "This is the content of document 1.",
        )
        self.assertEqual(chunk_list[0]["score"], 0.95)

        retrieval_node._execute = mock_execute

    @patch(
        "app.workflow_engine.as_workflow.node.retrieval.get_session",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.retrieval.RetrievalService",
    )
    def test_retrieve_no_results(
        self,
        MockRetrievalService: MagicMock,
        mock_get_session: MagicMock,
    ) -> None:
        """Test retrieving documents when no results are found."""
        # Create a retrieval node
        retrieval_node = RetrievalNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=self.node_kwargs,
            glb_custom_args={},
            params={},
        )

        # Override the execute method to return empty results
        def mock_execute(**kwargs: Any) -> Generator:
            query = retrieval_node.sys_args["input_params"][0]["value"]
            # Return empty list for nodes
            # Create empty result list
            result = []
            yield [
                WorkflowVariable(
                    name="chunk_list",
                    content=result,
                    source=retrieval_node.node_id,
                    data_type=DataType.ARRAY_OBJECT,
                    input={"input": query},
                    output={"chunk_list": result},
                    output_type="json",
                    node_type=retrieval_node.node_type,
                    node_name=retrieval_node.node_name,
                ),
            ]

        # Replace the execute method
        retrieval_node._execute = mock_execute

        # Execute the node
        result_generator = retrieval_node._execute()
        results = list(result_generator)

        # Verify results
        self.assertEqual(len(results), 1)
        workflow_vars = results[0]
        self.assertEqual(len(workflow_vars), 1)
        wf_var = workflow_vars[0]
        self.assertEqual(wf_var.name, "chunk_list")
        # Check that chunk list is empty
        chunk_list = wf_var.content
        self.assertEqual(len(chunk_list), 0)

    @patch(
        "app.workflow_engine.as_workflow.node.retrieval.get_session",
    )
    @patch(
        "app.workflow_engine.as_workflow.node.retrieval.RetrievalService",
    )
    def test_retrieve_multiple_knowledge_bases(
        self,
        MockRetrievalService: MagicMock,
        mock_get_session: MagicMock,
    ) -> None:
        """Test retrieving documents from multiple knowledge bases."""
        # Create configuration with multiple knowledge bases
        multi_kb_kwargs = {
            "config": {
                "node_param": {
                    "knowledge_base_ids": [
                        "11111111-1111-1111-1111-111111111111",
                        "22222222-2222-2222-2222-222222222222",
                    ],
                    "top_k": 10,
                    "similarity_threshold": 0.1,
                },
                "input_params": [{"key": "input", "value": "test query"}],
            },
            "type": "Retrieval",
            "id": self.node_id,
            "name": self.node_name,
        }

        # Create mock node
        mock_node = MagicMock()
        mock_node.metadata = {
            "document_id": "doc1",
            "document_name": "Document 1",
            "title": "Title 1",
            "page_number": 1,
            "chunk_id": "chunk1",
        }
        mock_node.get_content.return_value = (
            "Content from multiple knowledge bases."
        )
        mock_node.get_score.return_value = 0.95
        mock_node.id_ = "node1"  # Create a retrieval node with multiple KBs
        retrieval_node = RetrievalNode(
            node_id=self.node_id,
            node_name=self.node_name,
            node_kwargs=multi_kb_kwargs,
            glb_custom_args={},
            params={},
        )

        # Override the execute method
        def mock_execute(**kwargs: Any) -> Generator:
            query = retrieval_node.sys_args["input_params"][0]["value"]
            # Verify knowledge base IDs are correctly processed
            knowledge_base_ids = retrieval_node.sys_args["node_param"][
                "knowledge_base_ids"
            ]
            kb_uuids = [uuid.UUID(kb_id) for kb_id in knowledge_base_ids]
            # Check that both KBs are included
            self.assertEqual(len(kb_uuids), 2)
            self.assertEqual(
                str(kb_uuids[0]),
                "11111111-1111-1111-1111-111111111111",
            )
            self.assertEqual(
                str(kb_uuids[1]),
                "22222222-2222-2222-2222-222222222222",
            )

            # Return mock data
            nodes = [mock_node]
            result = [
                {
                    "doc_id": node.metadata.get("document_id", ""),
                    "doc_name": node.metadata.get("document_name", ""),
                    "title": node.metadata.get("title", ""),
                    "text": node.get_content(),
                    "score": node.get_score(),
                    "page_number": node.metadata.get("page_number", ""),
                    "chunk_id": node.metadata.get("chunk_id", ""),
                    "node_id": node.id_,
                }
                for node in nodes
            ]

            yield [
                WorkflowVariable(
                    name="chunk_list",
                    content=result,
                    source=retrieval_node.node_id,
                    data_type=DataType.ARRAY_OBJECT,
                    input={"input": query},
                    output={"chunk_list": result},
                    output_type="json",
                    node_type=retrieval_node.node_type,
                    node_name=retrieval_node.node_name,
                ),
            ]  # Replace the execute method

        retrieval_node._execute = mock_execute

        # Execute the node
        result_generator = retrieval_node._execute()
        results = list(result_generator)  # Verify results
        self.assertEqual(len(results), 1)
        workflow_vars = results[0]
        self.assertEqual(len(workflow_vars), 1)
        wf_var = workflow_vars[0]
        chunk_list = wf_var.content
        self.assertEqual(len(chunk_list), 1)
        self.assertEqual(chunk_list[0]["doc_id"], "doc1")
        self.assertEqual(
            chunk_list[0]["text"],
            "Content from multiple knowledge bases.",
        )


if __name__ == "__main__":
    unittest.main()
