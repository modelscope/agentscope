# -*- coding: utf-8 -*-
""" Import all service-related modules in the package."""
from loguru import logger

from .execute_code.exec_python import execute_python_code
from .file.common import (
    create_file,
    delete_file,
    move_file,
    create_directory,
    delete_directory,
    move_directory,
)
from .file.text import read_text_file, write_text_file
from .file.json import read_json_file, write_json_file
from .sql_query.mysql import query_mysql
from .sql_query.sqlite import query_sqlite
from .sql_query.mongodb import query_mongodb
from .web_search.search import bing_search, google_search
from .service_response import ServiceResponse
from .service_factory import ServiceFactory
from .retrieval.similarity import cos_sim
from .text_processing.summarization import summarization
from .retrieval.retrieval_from_list import retrieve_from_list
from .service_status import ServiceExecStatus


def get_help() -> None:
    """Get help message."""
    help_msg = f"The following service are available:\n{__all__}"
    logger.info(help_msg)


__all__ = [
    "execute_python_code",
    "create_file",
    "delete_file",
    "move_file",
    "create_directory",
    "delete_directory",
    "move_directory",
    "read_text_file",
    "write_text_file",
    "read_json_file",
    "write_json_file",
    "bing_search",
    "google_search",
    "query_mysql",
    "query_sqlite",
    "query_mongodb",
    "ServiceResponse",
    "ServiceFactory",
    "cos_sim",
    "summarization",
    "retrieve_from_list",
    "ServiceExecStatus",
]
