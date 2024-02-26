# -*- coding: utf-8 -*-
"""query in MongoDB """
from typing import Optional, Any

from ..service_response import ServiceResponse
from ...service.service_status import ServiceExecStatus

try:
    import pymongo.errors
except ImportError:
    pymongo = None


def query_mongodb(
    database: str,
    collection: str,
    query: dict,
    host: str,
    port: int,
    maxcount_results: Optional[int] = None,
    **kwargs: Any,
) -> ServiceResponse:
    """Execute query within MongoDB database.

    Args:
        database (`str`):
            The name of the database to use.
        collection (`str`):
            The name of the collection to use in mongodb.
        query (`dict`):
            The mongodb query to execute.
        host (`str`):
            The hostname or IP address of the MongoDB server.
        port (`int`):
            The port number of MongoDB server.
        maxcount_results (`int`, defaults to `None`):
            The maximum number of results to return. Defaults to `100` to
            avoid too many results.
        **kwargs:

    Returns:
        `ServiceResponse`: A `ServiceResponse` object that contains execution
        results or error message.

    Note:
        MongoDB is a little different from mysql and sqlite, for its
        operations corresponds to different functions. Now we only support
        `find` query and leave other operations in the future.
    """
    try:
        # Establish connection to MongoDB
        with pymongo.MongoClient(
            host=host,
            port=port,
            **kwargs,
        ) as mongo_client:
            db = mongo_client[database]
            coll = db[collection]

            # Perform the query
            if maxcount_results is not None:
                results = coll.find(query).limit(maxcount_results)
            else:
                results = coll.find(query)

            # mongo_client.close()

            # Convert the cursor to a list
            documents = list(results)
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=documents,
            )

    except Exception as e:
        # mongo_client.close()
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            # TODO: more specific error message
            content=str(e),
        )
