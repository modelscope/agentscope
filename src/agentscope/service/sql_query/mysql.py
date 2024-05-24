# -*- coding: utf-8 -*-
"""query in Mysql """
from typing import Optional
from typing import Any

from ..service_response import ServiceResponse
from ...utils.common import _if_change_database
from ...service.service_status import ServiceExecStatus

try:
    import pymysql
except ImportError:
    pymysql = None


def query_mysql(
    database: str,
    query: str,
    host: str,
    user: str,
    password: str,
    port: int,
    allow_change_data: bool = False,
    maxcount_results: Optional[int] = None,
    **kwargs: Any,
) -> ServiceResponse:
    """
    Execute query within MySQL database.

    Args:
        database (`str`):
            The name of the database to use.
        query (`str`):
            SQL query to execute.
        host (`str`):
            The host name or IP address of the MySQL server, e.g. "localhost".
        user (`str`):
            The username of the MySQL account to use.
        password (`str`):
            The password of the MySQL account to use.
        port (`str`):
            The port number of the MySQL server, e.g. 3306.
        allow_change_data (`bool`, defaults to `False`):
            Whether to allow changing data in the database. Defaults to
            `False` to avoid accidental changes to the database.
        maxcount_results (`int`, defaults to `None`):
            The maximum number of results to return. Defaults to `100` to
            avoid too many results.

    Returns:
        `ServiceResponse`: A `ServiceResponse` object that contains
        execution results or error message.
    """

    # Check if the query is safe
    if not allow_change_data and not _if_change_database(query):
        raise ValueError(
            "Unsafe SQL query detected. Only SELECT statements are allowed. "
            "If you want to allow changing data in the database, "
            "set `allow_change_data` to `True`.",
        )

    # Limit the number of results by adding LIMIT keywords if necessary
    if maxcount_results is not None:
        if "limit" not in query.lower():
            query += f" LIMIT {maxcount_results}"

    # Execute the query
    try:
        # Establish a connection to the database
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            **kwargs,
        )

        cursor = conn.cursor()
        cursor.execute(query)

        if _if_change_database(query):
            conn.commit()

        cursor.close()
        conn.close()

        # Fetch the results
        results = cursor.fetchall()
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=results,
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            # TODO: more specific error message
            content=str(e),
        )
