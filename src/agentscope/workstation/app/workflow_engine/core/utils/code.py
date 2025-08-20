# -*- coding: utf-8 -*-
"""
This module defines the CodeBlock class which helps in managing and organizing
code blocks with imports, initializations, and executable statements. It also
provides functionality to optionally control indentation.
"""
from typing import Union, List, Optional


class CodeBlock:
    """
    A class to manage and organize code blocks with imports,
    initializations, and executable statements, with optional indentation
    control.
    """

    def __init__(
        self,
        imports: Optional[List[str]] = None,
        inits: Optional[List[str]] = None,
        execs: Optional[List[str]] = None,
        increase_indent: bool = False,
    ):
        """
        Initialize the CodeBlock with optional imports, initializations,
        executable statements, and indentation control.

        :param imports: A list of import statements as strings.
        :param inits: A list of initialization statements as strings.
        :param execs: A list of executable statements as strings.
        :param increase_indent: A flag to increase indentation of the code
            block.
        """
        self.imports: List[str] = imports if imports is not None else []
        self.inits: List[str] = inits if inits is not None else []
        self.execs: List[str] = execs if execs is not None else []
        self.increase_indent: bool = increase_indent

    def add_import(self, import_statement: str) -> None:
        """
        Add an import statement to the code block.

        :param import_statement: The import statement to be added as a string.
        """
        self.imports.append(import_statement)

    def add_init(self, init_statement: str) -> None:
        """
        Add an initialization statement to the code block.

        :param init_statement: The initialization statement to be added as a
            string.
        """
        self.inits.append(init_statement)

    def add_exec(self, exec_statement: str) -> None:
        """
        Add an executable statement to the code block.

        :param exec_statement: The executable statement to be added as a
            string.
        """
        self.execs.append(exec_statement)

    def __getitem__(self, key: str) -> Union[List[str], bool]:
        """
        Retrieve the list of statements or the indentation flag by key.

        :param key: The key indicating which attribute to retrieve ("imports",
                    "inits", "execs", or "increase_indent").
        :return: The list of statements or the boolean flag corresponding to
            the key.
        :raises KeyError: If the key is not found in the CodeBlock.
        """
        if key == "imports":
            return self.imports
        elif key == "inits":
            return self.inits
        elif key == "execs":
            return self.execs
        elif key == "increase_indent":
            return self.increase_indent
        else:
            raise KeyError(f"Key {key} not found in CodeBlock.")
