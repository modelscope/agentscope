# -*- coding: utf-8 -*-
"""Parser for model response."""

from abc import ABC, abstractmethod
import json
from typing import Optional, Any

from agentscope._exception import JsonParsingError, MissingTagError
from agentscope.models import ModelResponse


class ParserBase(ABC):
    """The base class for model response parser."""

    @abstractmethod
    def parse(self, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a specific object, and stored in the
        parsed field of the response object."""

    def _extract_first_content_by_tag(
        self,
        response: ModelResponse,
        tag_start: str,
        tag_end: str,
    ) -> str:
        """Extract the first text content between the tag_start and tag_end
        in the response text. Note this function does not support nested.

        Args:
            response (`ModelResponse`):
                The response object.
            tag_start (`str`):
                The start tag.
            tag_end (`str`):
                The end tag.

        Returns:
            `str`: The extracted text content.
        """
        text = response.text

        index_start = text.find(tag_start) + len(tag_start)
        index_end = text.find(tag_end, index_start)

        if index_start == -1 or index_end == -1:
            missing_tags = []
            if index_start == -1:
                missing_tags.append(tag_start)
            if index_end == -1:
                missing_tags.append(tag_end)

            raise MissingTagError(
                f"Missing "
                f"tag{'' if len(missing_tags)==1 else 's'} "
                f"{' and '.join(missing_tags)} in response.",
                raw_response=text,
            )

        extract_text = text[index_start:index_end]

        return extract_text


class MarkdownJsonBlockParser(ParserBase):
    """A parser to parse the response text to a json object."""

    name: str = "json block"
    """The name of the parser."""

    tag_begin: str = "```json"
    """Opening tag for a code block."""

    content_hint: str = "{your_json_object}"
    """The hint of the content."""

    tag_end: str = "```"
    """Closing end for a code block."""

    _format_instruction = (
        "You should respond a json object in a json fenced code block as "
        "follows:\n```json\n{content_hint}\n```"
    )
    """The instruction for the format of the json object."""

    def __init__(self, content_hint: Optional[Any] = None) -> None:
        if content_hint is not None:
            if isinstance(content_hint, str):
                self.content_hint = content_hint
            else:
                self.content_hint = json.dumps(content_hint)

    def parse(self, response: ModelResponse) -> ModelResponse:
        """Parse the response text to a json object."""
        extract_text = self._extract_first_content_by_tag(
            response,
            self.tag_begin,
            self.tag_end,
        )

        try:
            parsed_json = json.loads(extract_text)
            response.parsed = parsed_json
            return response
        except json.decoder.JSONDecodeError as e:
            raw_response = f"{self.tag_begin}{extract_text}{self.tag_end}"
            raise JsonParsingError(
                f"The content between {self.tag_begin} and {self.tag_end} "
                f"MUST be a JSON object."
                f'When parsing "{raw_response}", an error occurred: {e}',
                raw_response=raw_response,
            ) from None

    @property
    def format_instruction(self) -> str:
        """Get the format instruction for the json object, if the
        format_example is provided, it will be used as the example.
        """
        return self._format_instruction.format(
            your_json_object=self.content_hint,
        )


class MarkdownCodeBlockParser(ParserBase):
    """The base class for parsing the response text by fenced block."""

    name: str = "{language_name} block"
    """The name of the parser."""

    tag_begin: str = "```{language_name}"
    """The beginning tag."""

    content_hint: str = "${your_{language_name}_CODE}"
    """The hint of the content."""

    tag_end: str = "```"
    """The ending tag."""

    format_instruction: str = (
        "You should generate {language_name} code in a {language_name} fenced "
        "code block as follows: \n```{language_name}\n"
        "${your_{language_name}_CODE}\n```"
    )
    """The instruction for the format of the code block."""

    def __init__(self, language_name: str) -> None:
        self.name = self.name.format(language_name=language_name)
        self.tag_begin = self.tag_begin.format(language_name=language_name)
        self.format_instruction = self.format_instruction.format(
            language_name=language_name,
        ).strip()

    def parse(self, response: ModelResponse) -> ModelResponse:
        extract_text = self._extract_first_content_by_tag(
            response,
            self.tag_begin,
            self.tag_end,
        )
        response.parsed = extract_text
        return response


class TaggedContent:
    """A tagged content object to store the tag name, tag begin, content hint
    and tag end."""

    name: str
    """The name of the tagged content."""

    tag_begin: str
    """The beginning tag."""

    content_hint: str
    """The hint of the content."""

    tag_end: str
    """The ending tag."""

    parse_json: bool
    """Whether to parse the content as a json object."""

    def __init__(
        self,
        name: str,
        tag_begin: str,
        content_hint: str,
        tag_end: str,
        parse_json: bool = False,
    ) -> None:
        """Initialize the tagged content object.

        Args:
            name (`str`):
                The name of the tagged content.
            tag_begin (`str`):
                The beginning tag.
            content_hint (`str`):
                The hint of the content.
            tag_end (`str`):
                The ending tag.
            parse_json (`bool`, defaults to `False`):
                Whether to parse the content as a json object.
        """

        self.name = name
        self.tag_begin = tag_begin
        self.content_hint = content_hint
        self.tag_end = tag_end
        self.parse_json = parse_json

    def __str__(self) -> str:
        """Return the tagged content as a string."""
        return f"{self.tag_begin}{self.content_hint}{self.tag_end}"


class MultiTaggedContentParser(ParserBase):
    """Parse response text by multiple tags, and return a dict of their
    content. Asking llm to generate JSON dictionary object directly maybe not a
    good idea due to involving escape characters and other issues. So we can
    ask llm to generate text with tags, and then parse the text to get the
    final JSON dictionary object.
    """

    format_instruction = (
        "Respond with specific tags as outlined below{json_required_hint}\n"
        "{tag_lines_format}"
    )
    """The instruction for the format of the tagged content."""

    json_required_hint = ", and the content between {} MUST be a JSON object:"
    """If a tagged content is required to be a JSON object by `parse_json`
    equals to `True`, this instruction will be used to remind the model to
    generate JSON object."""

    def __init__(self, *tagged_contents: TaggedContent) -> None:
        """Initialize the parser with tags.

        Args:
            tags (`dict[str, Tuple[str, str]]`):
                A dictionary of tags, the key is the tag name, and the value is
                a tuple of starting tag and end tag.
        """
        self.tagged_contents = list(tagged_contents)

        # Prepare the format instruction according to the tagged contents
        tag_lines = "\n".join([str(_) for _ in tagged_contents])

        # Prepare hint for the tagged contents that requires a JSON object.
        json_required_tags = ", ".join(
            [
                f"{_.tag_begin} and {_.tag_end}"
                for _ in tagged_contents
                if _.parse_json
            ],
        )
        if json_required_tags != "":
            json_required_hint = self.json_required_hint.format(
                json_required_tags,
            )
        else:
            json_required_hint = ": "

        self.format_instruction = self.format_instruction.format(
            json_required_hint=json_required_hint,
            tag_lines_format=tag_lines,
        )

    def parse(self, response: ModelResponse) -> ModelResponse:
        """Parse the response text by tags, and return a dict of their content
        in the parsed field of the model response object. If the tagged content
        requires to parse as a JSON object by `parse_json` equals to `True`, it
        will be parsed as a JSON object by `json.loads`."""

        tag_to_content = {}
        for tagged_content in self.tagged_contents:
            tag_begin = tagged_content.tag_begin
            tag_end = tagged_content.tag_end

            extract_content = self._extract_first_content_by_tag(
                response,
                tag_begin,
                tag_end,
            )

            if tagged_content.parse_json:
                try:
                    extract_content = json.loads(extract_content)
                except json.decoder.JSONDecodeError as e:
                    raw_response = f"{tag_begin}{extract_content}{tag_end}"
                    raise JsonParsingError(
                        f"The content between {tagged_content.tag_begin} and "
                        f"{tagged_content.tag_end} should be a JSON object."
                        f'When parsing "{raw_response}", an error occurred: '
                        f"{e}",
                        raw_response=raw_response,
                    ) from None

            tag_to_content[tagged_content.name] = extract_content

        response.parsed = tag_to_content
        return response
