# -*- coding: utf-8 -*-
import os
import mimetypes
from typing import Union, List


def infer_content_type(filename: str) -> str:
    """Infer content type by filename using Python's mimetypes and fallback
    rules.

    Args:
        filename: Path or name of file

    Returns:MIME content type string
    """
    # Use the mimetypes library to obtain more accurate MIME types.
    mimetypes.init()
    content_type, _ = mimetypes.guess_type(filename)

    if content_type:
        return content_type

    # If mimetypes cannot be recognized, use custom rules.
    _, ext = os.path.splitext(filename.lower())
    if ext in [".md", ".markdown"]:
        return "text/markdown"
    elif ext == ".txt":
        return "text/plain"
    elif ext == ".pdf":
        return "application/pdf"
    elif ext == ".doc":
        return "application/msword"
    elif ext == ".docx":
        return (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )
    else:
        return "application/octet-stream"


def extract_content(file_path: str, ext: str) -> str:
    """Extract content from a file given its path and extension."""

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    content_type = infer_content_type(file_path)

    if content_type == "application/pdf":
        try:
            from llama_index.readers.file import PyMuPDFReader

            reader = PyMuPDFReader()
            documents = reader.load_data(file_path)
            return "\n\n".join([doc.text for doc in documents])
        except ImportError:
            raise ImportError(
                "PyMuPDF required for PDF extraction. Install with: pip "
                "install llama_index.readers.file pymupdf",
            )

    elif content_type == "text/plain":
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    elif content_type == "text/markdown":
        from llama_index.readers.file.markdown.base import MarkdownReader

        documents = MarkdownReader().load_data(file_path)
        return "\n\n".join([doc.text for doc in documents])
    elif content_type in [
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document",
        "application/msword",
    ]:
        from llama_index.readers.file.docs.base import DocxReader
        from pathlib import Path

        documents = DocxReader().load_data(Path(file_path))
        return "\n\n".join([doc.text for doc in documents])
    elif content_type == "text/csv":
        import pandas as pd

        df = pd.read_csv(file_path)
        return df.to_string()
    else:
        raise ValueError(f"Unsupported file: {file_path}")
