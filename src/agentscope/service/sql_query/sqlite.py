# -*- coding: utf-8 -*-
""" Query in sqlite """
from typing import Optional
from typing import Any

from ...service.service_response import ServiceResponse
from ...utils.common import _if_change_database
from ...service.service_status import ServiceExecStatus

try:
    import sqlite3
except ImportError:
    sqlite3 = None


def query_sqlite(
    database: str,
    query: str,
    allow_change_data: bool = False,
    maxcount_results: Optional[int] = None,
    **kwargs: Any,
) -> ServiceResponse:
    """Executes query within sqlite database.

    Args:
        database (`str`):
            The name of the database to use.
        query (`str`):
            The query to execute.
        allow_change_data (`bool`, defaults to `False`):
            Whether to allow changing data in the database. Defaults to
            `False` to avoid accidental changes to the database.
        maxcount_results (`int`, defaults to `None`):
            The maximum number of results to return.

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

    try:
        conn = sqlite3.connect(database, **kwargs)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # commit the change if needed
        if _if_change_database(query):
            conn.commit()

        cursor.close()
        conn.close()

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=results,
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            # TDOO: more specific error message
            content=str(e),
        )
