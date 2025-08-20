# -*- coding: utf-8 -*-
"""The utilities for the text processing"""
import re
from typing import Optional, Any

import jieba
import jieba.analyse


def text_preprocessing(text: str, preprocessing_rules: dict) -> str:
    """Preprocess text"""
    if preprocessing_rules.get("replace_whitespace"):
        text = re.sub(r"\s+", " ", text).strip()
    if preprocessing_rules.get("remove_urls_emails"):
        text = re.sub(
            r"http\S+|www.\S+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "",
            text,
        )
    return text


def preprocess_chunk_or_child_chunk(text: str, rules: dict) -> Optional[str]:
    """Preprocess a chunk or child chunk if it is not empty after
    processing."""
    processed_text = text_preprocessing(text, rules)
    return processed_text if processed_text else None


def preprocess_chunks_and_child_chunks(
    chunks: list,
    child_chunks: list,
    rules: dict,
) -> tuple:
    """Preprocess chunks and their corresponding child chunks."""
    preprocessed_chunks = []
    preprocessed_child_chunks = []

    for chunk, chunk_list in zip(
        chunks,
        child_chunks if child_chunks else [[]] * len(chunks),
    ):
        processed_chunk = preprocess_chunk_or_child_chunk(chunk, rules)
        if processed_chunk:
            processed_chunks = [
                preprocess_chunk_or_child_chunk(chunk, rules)
                for chunk in chunk_list
            ]
            processed_child_chunks = [
                child_chunk for child_chunk in processed_chunks if child_chunk
            ]  # Filter out None values

            if processed_child_chunks:
                preprocessed_chunks.append(processed_chunk)
                preprocessed_child_chunks.append(processed_child_chunks)
            elif not child_chunks:  # If there are no child chunks, add the
                # chunk anyway
                preprocessed_chunks.append(processed_chunk)
                preprocessed_child_chunks.append([])

    return preprocessed_chunks, preprocessed_child_chunks


# pylint: disable=too-many-statements
def text_split(text: str, chunk_type: str, chunk_parameter: dict) -> tuple:
    """Split text according to the given mode and mode parameters."""

    def text_splitter_length_and_overlap(
        content: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[str]:
        result = []
        while content:
            result.append(content[:chunk_size])
            content = content[chunk_size - chunk_overlap :]
        return result

    def text_splitter_page(
        content: str,
        chunk_size: int,
    ) -> list[str]:
        # TODO: Implement real text_splitter_page
        return text_splitter_length_and_overlap(
            content,
            chunk_size=chunk_size,
            chunk_overlap=0,
        )

    def text_splitter_title(
        content: str,
        chunk_size: int,
    ) -> list[str]:
        # TODO: Implement real text_splitter_title
        return text_splitter_length_and_overlap(
            content,
            chunk_size=chunk_size,
            chunk_overlap=0,
        )

    # pylint: disable=too-many-branches
    def text_splitter_regex(
        content: str,
        regex: str = r"\n\s*\n|\n#",
        chunk_overlap: int = 100,
        chunk_size: int = 1000,
        keep_separator: bool = True,
    ) -> list[str]:
        if chunk_overlap > chunk_size:
            chunk_size = chunk_overlap * 5
        regex = re.compile(regex)

        matches = list(regex.finditer(content))
        chunks = []

        if not matches:
            start = 0
            while start < len(content):
                end = min(start + chunk_size, len(content))
                chunks.append(content[start:end])
                start += chunk_size - chunk_overlap
                if start >= end:
                    break
            return chunks

        if matches[0].start() > 0:
            chunks.append(content[: matches[0].start()])

        for i in range(len(matches) - 1):
            start = matches[i].start() if keep_separator else matches[i].end()
            end = matches[i + 1].start()
            chunk_ = content[start:end]
            if len(chunk_) > chunk_size:
                j = 0
                while j < len(chunk_):
                    sub_end = min(j + chunk_size, len(chunk_))
                    chunks.append(chunk_[j:sub_end])
                    j += chunk_size - chunk_overlap
                    if j >= len(chunk_):
                        break
            else:
                chunks.append(chunk_)
        start = matches[-1].start() if keep_separator else matches[-1].end()
        last_chunk = content[start:]
        if len(last_chunk) > chunk_size:
            j = 0
            while j < len(last_chunk):
                sub_end = min(j + chunk_size, len(last_chunk))
                chunks.append(last_chunk[j:sub_end])
                j += chunk_size - chunk_overlap
                if j >= len(last_chunk):
                    break
        else:
            chunks.append(last_chunk)

        result = [c for c in chunks if c.strip()]

        return result

    def text_splitter_paragraph(
        content: str,
        paragraph_chunk_identifier: str,
        paragraph_chunk_size: int,
        paragraph_chunk_overlap: int,
    ) -> list:
        paragraphs = content.split(paragraph_chunk_identifier)
        result = []

        for paragraph in paragraphs:
            if not paragraph:
                continue
            words = list(jieba.cut(paragraph.strip()))
            start = 0
            while start < len(words):
                end = start + paragraph_chunk_size
                if end > len(words):
                    end = len(words)
                result.append("".join(words[start:end]))
                start = end - paragraph_chunk_overlap

                if start < 0 or (end == len(words) and start < end):
                    break
        return result

    def text_splitter_by_identifier_and_chunk_size(
        content: str,
        chunk_identifier: str,
        chunk_size: int,
    ) -> list[str]:
        chunks = content.split(chunk_identifier)
        result = []
        for chunk_ in chunks:
            trimmed_chunk = chunk_.strip()
            if not trimmed_chunk:
                continue

            words_in_chunk = list(jieba.cut(trimmed_chunk.strip()))
            if len(words_in_chunk) <= chunk_size:
                result.append(trimmed_chunk.strip())
            else:
                sub_chunk_start = 0
                while sub_chunk_start < len(words_in_chunk):
                    sub_chunk_end = sub_chunk_start + chunk_size
                    if sub_chunk_end > len(words_in_chunk):
                        sub_chunk_end = len(words_in_chunk)
                    result.append(
                        "".join(
                            words_in_chunk[sub_chunk_start:sub_chunk_end],
                        ),
                    )
                    sub_chunk_start = sub_chunk_end

        return result

    def text_splitter_full_text(
        content: str,
        parent_chunk_size: int,
        child_chunk_identifier: str,
        child_chunk_size: int,
    ) -> tuple:
        words = re.findall(r"\S+\s*", content)
        limited_content = "".join(words[:parent_chunk_size])
        return [limited_content], [
            text_splitter_by_identifier_and_chunk_size(
                content=limited_content,
                chunk_identifier=child_chunk_identifier,
                chunk_size=child_chunk_size,
            ),
        ]

    def text_splitter_parent_child(
        content: str,
        parent_chunk_identifier: str,
        parent_chunk_size: int,
        child_chunk_identifier: str,
        child_chunk_size: int,
    ) -> tuple:
        res = []
        chunks = text_splitter_by_identifier_and_chunk_size(
            content=content,
            chunk_identifier=parent_chunk_identifier,
            chunk_size=parent_chunk_size,
        )
        for seg in chunks:
            res.append(
                text_splitter_by_identifier_and_chunk_size(
                    content=seg,
                    chunk_identifier=child_chunk_identifier,
                    chunk_size=child_chunk_size,
                ),
            )
        return chunks, res

    chunk, child_chunk, keywords_list = [], [], []

    if chunk_type in ["length", "basic"]:
        chunk = text_splitter_length_and_overlap(
            content=text,
            chunk_size=chunk_parameter.get("chunk_size", 1000),
            chunk_overlap=chunk_parameter.get("chunk_overlap", 200),
        )
    elif chunk_type == "page":
        chunk = text_splitter_page(
            content=text,
            chunk_size=chunk_parameter.get("chunk_size", 1000),
        )
    elif chunk_type == "title":
        chunk = text_splitter_title(
            content=text,
            chunk_size=chunk_parameter.get("chunk_size", 1000),
        )
    elif chunk_type == "regex":
        chunk = text_splitter_regex(
            content=text,
            regex=chunk_parameter.get("regex", "\n\n"),
            chunk_size=chunk_parameter.get("chunk_size", 1000),
            chunk_overlap=chunk_parameter.get("chunk_overlap", 200),
        )
    elif chunk_type == "paragraph":
        chunk = text_splitter_paragraph(
            content=text,
            paragraph_chunk_identifier=chunk_parameter.get(
                "paragraph_chunk_identifier",
                "\n\n",
            ),
            paragraph_chunk_size=chunk_parameter.get(
                "paragraph_chunk_size",
                500,
            ),
            paragraph_chunk_overlap=chunk_parameter.get(
                "paragraph_chunk_overlap",
                200,
            ),
        )
        keywords_list = [keywords_extract(_) for _ in chunk]
    elif chunk_type == "full-text":
        chunk, child_chunk = text_splitter_full_text(
            content=text,
            parent_chunk_size=chunk_parameter.get("parent_chunk_size", 10000),
            child_chunk_identifier=chunk_parameter.get(
                "child_chunk_identifier",
                "\n",
            ),
            child_chunk_size=chunk_parameter.get("child_chunk_size", 200),
        )
    elif chunk_type == "parent-child":
        chunk, child_chunk = text_splitter_parent_child(
            content=text,
            parent_chunk_identifier=chunk_parameter.get(
                "parent_chunk_identifier",
                "\n\n",
            ),
            parent_chunk_size=chunk_parameter.get("parent_chunk_size", 500),
            child_chunk_identifier=chunk_parameter.get(
                "child_chunk_identifier",
                "\n",
            ),
            child_chunk_size=chunk_parameter.get("child_chunk_size", 200),
        )
    else:
        raise ValueError(f"Invalid chunk type: {chunk_type}")
    return chunk, child_chunk, keywords_list


def keywords_extract(text: str, top_k: int = 10) -> list[str]:
    """Extract keywords from a text"""
    keywords = jieba.analyse.extract_tags(text, topK=top_k)
    return keywords


def preprocess_chunk_parameter(
    chunk_type: str = "length",
    **kwargs: Any,
) -> tuple:
    """init default mode parameter"""
    chunk_parameter = {}
    if chunk_type in ["length", "basic"]:
        chunk_parameter = {
            "chunk_size": kwargs.get("chunk_size", 500),
            "chunk_overlap": kwargs.get("chunk_overlap", 50),
        }
    elif chunk_type == "page":
        chunk_parameter = {
            "chunk_size": kwargs.get("chunk_size", 500),
        }
    elif chunk_type == "title":
        pass
    elif chunk_type == "regex":
        chunk_parameter = {
            "chunk_overlap": kwargs.get("chunk_overlap", 50),
            "regex": kwargs.get("regex", "\n\n"),
        }

    elif chunk_type == "parent-child":
        chunk_parameter = {
            "parent_as_context": (
                kwargs.get("parent_as_context")
                if kwargs.get("parent_as_context")
                else True
            ),
            "parent_chunk_identifier": kwargs.get(
                "parent_chunk_identifier",
            )
            or "\n\n",
            "parent_chunk_size": kwargs.get(
                "child_chunk_size",
            )
            or 500,
            "child_chunk_identifier": kwargs.get(
                "child_chunk_identifier",
            )
            or "\n",
            "child_chunk_size": kwargs.get(
                "child_chunk_size",
            )
            or 200,
        }
        if chunk_type == "full-text":
            chunk_parameter["parent_chunk_size"] = 10000
    elif chunk_type == "paragraph":
        chunk_parameter = {
            "paragraph_chunk_identifier": kwargs.get(
                "paragraph_chunk_identifier",
            )
            or "\n\n",
            "paragraph_chunk_size": kwargs.get(
                "paragraph_chunk_size",
            )
            or 500,
            "paragraph_chunk_overlap": kwargs.get(
                "paragraph_chunk_overlap",
                50,
            ),
        }
    else:
        raise ValueError(f"Invalid chunk type: {chunk_type}")
    preprocessing_rules = {
        "replace_whitespace": kwargs.get(
            "replace_whitespace",
            True,
        ),
        "remove_urls_emails": kwargs.get(
            "remove_urls_emails",
            False,
        ),
    }
    return chunk_type, chunk_parameter, preprocessing_rules
