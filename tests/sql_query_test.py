# -*- coding: utf-8 -*-
""" Python sql query test."""
import unittest
from unittest.mock import MagicMock, patch

from agentscope.service.sql_query.mongodb import query_mongodb

from agentscope.service.sql_query.mysql import query_mysql
from agentscope.service.service_response import ServiceExecStatus
from agentscope.service.sql_query.sqlite import query_sqlite


class TestSQLQueries(unittest.TestCase):
    """ExampleTest for a unit test."""

    @patch("agentscope.service.sql_query.mysql.pymysql.connect")
    def test_query_mysql_success(self, mock_connect: MagicMock) -> None:
        """Test query mysql success"""
        # Set up a mock connection and cursor
        mock_cursor = mock_connect.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = [("data1",), ("data2",)]

        # Call the query_mysql function
        response = query_mysql(
            database="test_mysql_db",
            query="SELECT * FROM my_table",
            host="localhost",
            user="user",
            password="pass",
            port=3306,
            allow_change_data=False,
            maxcount_results=10,
        )

        # Assert that the query_mysql function returned the expected results
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(response.content, [("data1",), ("data2",)])

        # Ensure that the SQL query was executed correctly
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM my_table LIMIT 10",
        )
        # Ensure that all results were fetched
        mock_cursor.fetchall.assert_called_once()

    @patch("agentscope.service.sql_query.mysql.pymysql.connect")
    def test_query_mysql_failure(self, mock_connect: MagicMock) -> None:
        """Test query mysql failure"""
        # Set up pymysql.connect to raise an exception
        mock_connect.side_effect = Exception("Connection Error")

        # Call the query_mysql function
        response = query_mysql(
            database="test_mysql_db",
            query="SELECT * FROM my_table",
            host="localhost",
            user="user",
            password="pass",
            port=3306,
        )

        # Assert that the query_mysql function handled the exception
        self.assertEqual(response.status, ServiceExecStatus.ERROR)
        self.assertIn("Connection Error", str(response.content))

    # Test for mongodb
    @patch("agentscope.service.sql_query.mongodb.pymongo.MongoClient")
    def test_query_mongodb_success(self, mock_mongo_client: MagicMock) -> None:
        """Test query mongodb success"""
        # Set up a mock connection
        mock_collection = MagicMock()
        mock_collection.find.return_value.limit.return_value = [
            {"_id": 1, "data": "test"},
        ]
        mock = MagicMock()
        mock_db = MagicMock()
        mock.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_client = MagicMock()
        mock_mongo_client.return_value.__enter__.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db

        # Call the query_mongodb function
        response = query_mongodb(
            database="db_name",
            collection="collection_name",
            query={"data": "test"},
            host="localhost",
            port=27017,
            maxcount_results=10,
        )

        # Ensure that the query_mongodb returned the expected results
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(response.content, [{"_id": 1, "data": "test"}])

        # Ensure that the query was executed correctly
        mock_db.__getitem__.assert_called_with("collection_name")
        mock_collection.find.assert_called_with({"data": "test"})
        mock_collection.find.return_value.limit.assert_called_with(10)

    @patch("agentscope.service.sql_query.mongodb.pymongo.MongoClient")
    def test_query_mongodb_failure(self, mock_mongo_client: MagicMock) -> None:
        """Test query mongodb failure"""
        # Configure the mock to raise a connection error
        mock_mongo_client.side_effect = Exception("Connection Error")

        # Call the query_mongodb function
        response = query_mongodb(
            database="test_db",
            collection="test_collection",
            query={"name": "Test Data"},
            host="localhost",
            port=27017,
        )

        # Assert that the function handled the exception
        self.assertEqual(response.status, ServiceExecStatus.ERROR)
        self.assertIn("Connection Error", str(response.content))

    # Test for sqlite
    @patch("agentscope.service.sql_query.sqlite.sqlite3.connect")
    def test_query_sqlite_success(self, mock_connect: MagicMock) -> None:
        """Test successful SELECT query without data modification"""
        # Mock sqlite connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("data1",), ("data2",)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_connect.return_value = mock_connection

        # Execute the query_sqlite function
        response = query_sqlite(
            database="test_db.sqlite",
            query="SELECT * FROM my_table",
            allow_change_data=False,
            maxcount_results=10,
        )

        # Assert the query_sqlite function returned expected results
        self.assertEqual(response.status, ServiceExecStatus.SUCCESS)
        self.assertEqual(response.content, [("data1",), ("data2",)])

        # Verify the correct SQL query was executed
        mock_cursor.execute.assert_called_with(
            "SELECT * FROM my_table LIMIT 10",
        )
        # Ensure all results were fetched
        mock_cursor.fetchall.assert_called_once()

    @patch("agentscope.service.sql_query.sqlite.sqlite3.connect")
    def test_query_sqlite_exception_handling(
        self,
        mock_connect: MagicMock,
    ) -> None:
        """Test exception handling within the query_sqlite function"""
        # Configure the mock to raise an exception during connection
        mock_connect.side_effect = Exception("Connection Error")

        # Execute the query_sqlite function
        response = query_sqlite(
            database="test_db.sqlite",
            query="SELECT * FROM my_table",
        )

        # Assert that the function handled the exception
        self.assertEqual(response.status, ServiceExecStatus.ERROR)
        self.assertIn("Connection Error", str(response.content))


if __name__ == "__main__":
    unittest.main()
