# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""The web browser module for agent to interact with web pages."""
import time
from pathlib import Path
from typing import Union, Callable, Optional

import requests
from loguru import logger
from pydantic import BaseModel

from agentscope.service import ServiceResponse, ServiceExecStatus


class WebElementInfo(BaseModel):
    """The information of a web interactive element."""

    html: str
    """The html content of the element."""

    tag_name: str
    """The tage name of the element."""

    node_name: str
    """The node name of the element."""

    node_value: Union[None, str]
    """The node value of the element."""

    type: Union[None, str]
    """The type of the element."""

    aria_label: Union[None, str]
    """The aria label of the element."""

    is_clickable: Union[str, bool]
    """Whether the element is clickable. If clickable, the value is the
    link of the element, otherwise, the value is False."""

    meta_data: list[str]
    """The meta data of the elements, e.g. attributes"""

    inner_text: str
    """The text content of the element."""

    origin_x: float
    """The x coordinate of the origin of the element."""

    origin_y: float
    """The y coordinate of the origin of the element."""

    width: float
    """The width of the element."""

    height: float
    """The height of the element."""


class WebBrowser:
    """The web browser for agent, which is implemented with playwright. This
    module allows agent to interact with web pages, such as visiting a web
    page, clicking on elements, typing text, scrolling web page, etc.

    Note:
        1. This module is still under development, and changes will be made in
        the future.
        2. In Playwright, because of its asynchronous operations, it is
        essential to use `if __name__ == "__main__":` to designate the main
        entry point of the program. This practice ensures that asynchronous
        functions are executed correctly within the appropriate context.

    Install:
        Execute the following code to install the required packages:

        .. code-block:: bash

            pip install playwright
            playwright install


    Details:
        1. The actions that the agent can take in the web browser includes:
        "action_click", "action_type", "action_scroll_up",
        "action_scroll_down", "action_press_key", and "action_visit_url".
        2. You can extract the html content, title, url, screenshot of the
        current web page by calling the corresponding properties, e.g.
        `page_url`, `page_html`, `page_title`, `page_screenshot`.
        3. You can set or remove the interactive marks on the web page by
        calling the `set_interactive_marks` and `remove_interactive_marks`
        methods.


    Examples:
        .. code-block:: python

            from agentscope.service import WebBrowser
            import time

            if __name__ == "__main__":
                browser = WebBrowser()
                # Visit the specific web page
                browser.action_visit_url("https://www.bing.com")
                # Set the interactive marks on the web page
                browser.set_interactive_marks()

                time.sleep(5)

                browser.close()

    """

    _actions = [
        "action_click",
        "action_type",
        "action_scroll_up",
        "action_scroll_down",
        "action_press_key",
        "action_visit_url",
    ]
    """The available actions for the web browser that agent can takes."""

    _interactive_elements: list
    """To record the interactive elements on the current page, which will be
    set after calling the `set_interactive_marks` method, and cleared after
    calling the `remove_interactive_marks` method."""

    def __init__(
        self,
        timeout: int = 30,
        browser_visible: bool = True,
        browser_width: int = 1280,
        browser_height: int = 1080,
    ) -> None:
        """Initialize the web browser module.

        Args:
            timeout (`int`, defaults to `30`):
                The timeout (in seconds) for the browser to wait for the
                page to load, defaults to 60s.
            browser_visible (`bool`, defaults to `True`):
                Whether the browser is visible.
            browser_width (`int`, defaults to `1280`):
                The width of the browser. Defaults to 1280.
            browser_height (`int`, defaults to `1080`):
                The height of the browser. Defaults to 1080.
        """

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError(
                "Please install the `playwright` package by running `pip "
                "install playwright; playwright install` to use the web "
                "browser. \n"
                "More details refer to "
                "https://playwright.dev/python/docs/intro.",
            ) from e

        # Init a web page
        playwright_process = sync_playwright().start()
        self.browser = playwright_process.chromium.launch(
            headless=not browser_visible,
        )

        self._page = self.browser.new_page()
        self._page.set_default_timeout(timeout * 1000)
        self._page.set_viewport_size(
            {
                "width": browser_width,
                "height": browser_height,
            },
        )

        # Init a dictionary to store the interactive elements on the page
        self._interactive_elements = []

        # Load the external JavaScript to crawl the page
        self._load_external_js()

    @property
    def url(self) -> str:
        """The url of current page."""
        return self._page.url

    @property
    def page_html(self) -> str:
        """The html content of current page."""
        return self._page.content()

    @property
    def page_title(self) -> str:
        """The title of current page."""
        return self._page.title()

    @property
    def page_markdown(self) -> str:
        """The content of current page in Markdown format."""
        try:
            import markdownify
        except ImportError as e:
            raise ImportError(
                "Please install the `markdownify` package to convert the page"
                "content to markdown format.",
            ) from e

        return markdownify.markdownify(self.page_html)

    @property
    def page_screenshot(self) -> bytes:
        """The screenshot of the current page."""
        return self._page.screenshot()

    # ----- Actions which are performed within a web page ---------------------
    def action_click(self, element_id: int) -> ServiceResponse:
        """Click on the element with the given id.

        Args:
            element_id (`int`):
                The id of the element to click.

        Returns:
            `ServiceResponse`:
                The response of the click action.
        """
        if not self._verify_element_id(element_id):
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"ElementIDError: The element id must be in the range "
                f"[0, {len(self._interactive_elements) - 1}], but "
                f"got {element_id}.",
            )

        element_handle = self._interactive_elements[element_id]
        element_handle.evaluate(
            "element => element.setAttribute('target', '_self')",
        )

        element_handle.click()

        self._wait_for_load(
            "Wait for click event",
            "Finished",
        )

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Click on element {element_id} done",
        )

    def action_type(
        self,
        element_id: int,
        text: str,
        submit: bool,
    ) -> ServiceResponse:
        """Type text into the element with the given id.

        Args:
            element_id (`int`):
                The id of the element to type text into.
            text (`str`):
                The text to type into the element.
            submit (`bool`):
                If press the "Enter" after typing text.

        Returns:
            `ServiceResponse`:
                The response of the type action.
        """
        if not self._verify_element_id(element_id):
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"ElementIDError: The element id must be in the range "
                f"[0, {len(self._interactive_elements) - 1}], but "
                f"got {element_id}.",
            )

        self.action_click(element_id)
        web_ele = self._interactive_elements[element_id]

        # Try to clear the text within the given elements
        try:
            self._page.evaluate('element => element.value = ""', web_ele)
        except Exception as e:
            logger.info(
                f"Exception {str(e)}, "
                "unable to clear the value within the given elements.",
            )

        # Focus on the element to type
        self._page.evaluate("element => element.focus()", web_ele)

        # Type in the text
        web_ele.type(str(text))
        self._wait_for_load(
            "Wait for finish typing",
            "Finished",
        )

        if submit:
            self.action_press_key("Enter")

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Typing done",
        )

    def action_scroll_up(self) -> ServiceResponse:
        """Scroll up the current web page."""
        self._page.keyboard.down("Alt")
        self._page.keyboard.press("ArrowUp")
        self._page.keyboard.up("Alt")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Scroll up done",
        )

    def action_scroll_down(self) -> ServiceResponse:
        """Scroll down the current web page."""
        self._page.keyboard.down("Alt")
        self._page.keyboard.press("ArrowDown")
        self._page.keyboard.up("Alt")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Scroll down done",
        )

    def action_press_key(self, key: str) -> ServiceResponse:
        """Press down a key in the current web page.

        Args:
            key (`str`):
                Chosen from `F1` - `F12`, `Digit0`- `Digit9`, `KeyA`- `KeyZ`, `Backquote`, `Minus`, `Equal`, `Backslash`, `Backspace`, `Tab`, `Delete`, `Escape`, `ArrowDown`, `End`, `Enter`, `Home`, `Insert`, `PageDown`, `PageUp`, `ArrowRight`, `ArrowUp`, etc.
        """  # noqa
        self._page.keyboard.press(key)

        # TODO: in a more elegant way to wait for the page to be loaded rather
        #  then using time.sleep
        # Wait for the page to be loaded
        time.sleep(2)

        self._wait_for_load(
            f"Wait for press key: {key}",
            "Finished",
        )
        response = ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Press key: {key} done",
        )
        return response

    # ------ Actions which are performed to change the web page ---------------
    def action_visit_url(self, url: str) -> ServiceResponse:
        """Visit the given url.

        Args:
            url (`str`):
                The url to visit in browser.
        """
        self._page.goto(url)
        self._wait_for_load(
            f"Wait for page {url} to load.",
        )

        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Load web page successfully.",
        )

    def get_action_functions(self) -> dict[str, Callable]:
        """Return a dictionary of the action functions, where the key is the
        action name and the value is the corresponding function."""
        return {
            action_name: getattr(self, action_name)
            for action_name in self._actions
        }

    # ------ Set or remove marks of interactive elements on the web page ------
    def set_interactive_marks(self) -> list[WebElementInfo]:
        """Mark the interactive elements on the current web page."""

        # Remove the existing interactive elements on the current web page
        self.remove_interactive_marks()

        # Load the javascript to crawl the page
        self._page.evaluate(self._mark_page_js)

        # Mark the interactive elements on the web page by calling the
        # JavaScript function `crawlPage`
        result_handle = self._page.evaluate_handle("setInteractiveMarks()")

        # Record the interactive elements on the current page
        interactive_items_handle = result_handle.get_property("items")
        items_info_handle = result_handle.get_property("itemsInfo")

        js_handles = (
            interactive_items_handle.evaluate_handle("items => items")
            .get_properties()
            .values()
        )
        self._interactive_elements = [
            item.get_property("element").as_element() for item in js_handles
        ]

        # Get the interactive items
        return [
            WebElementInfo(**info) for info in items_info_handle.json_value()
        ]

    def remove_interactive_marks(self) -> None:
        """Remove the interactive elements on the current web page."""
        # Load the javascript to crawl the page
        self._page.evaluate(self._mark_page_js)

        # Remove the interactive elements on the web page by calling the
        # JavaScript function `rmInteractiveMarks`
        self._page.evaluate("removeInteractiveMarks()")

        self._interactive_elements.clear()

    def close(self) -> None:
        """Close the browser"""
        self.browser.close()

    def _wait_for_load(
        self,
        hint_s: str,
        hint_e: str = "Page loaded.",
        timeout: Optional[int] = None,
    ) -> None:
        """Wait to ensure the page is loaded after certain actions.

        Args:
            hint_s (`str`):
                   The hint message before waiting.
                hint_e (`str`):
                    The hint message after waiting.
                timeout (`Optional[int]`, defaults to `None`)
                    The timeout for the page to load (in seconds)
        """
        logger.debug(hint_s)

        if timeout is not None:
            timeout = timeout * 1000

        self._page.wait_for_load_state("load", timeout=timeout)
        logger.debug(hint_e)

    def _verify_element_id(self, element_id: int) -> bool:
        """Verify the given element id is valid or not."""
        return 0 <= element_id < len(self._interactive_elements)

    def _load_external_js(self) -> None:
        """Read the JavaScript from local file. The JavaScript written in
        markpage.js will crawl all the interactive elements on the page,
        and mark them on with square marks.
        """
        current_file_path = Path(__file__)
        js_file_path = current_file_path.parent / "markpage.js"

        with open(js_file_path, "r", encoding="utf-8") as file:
            self._mark_page_js = file.read()

    def _get_jina_page(self) -> str:
        """Return the formatted current page text, using api from jina"""
        jina_url = "https://r.jina.ai/" + self.url
        try:
            page_text = requests.get(jina_url).text
            return page_text
        except Exception as e:
            return (
                f"Encounter exception {str(e)}"
                f"The page in {self.url} might not be loaded yet"
                "you might want to check the request connection or api quota."
            )
