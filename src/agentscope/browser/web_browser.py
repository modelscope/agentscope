# -*- coding: utf-8 -*-
"""
The web browser interface for agentscope
"""
import time
from pathlib import Path

import requests
from loguru import logger

try:
    import markdownify
    from playwright.sync_api import sync_playwright
except ImportError as import_error:
    from agentscope.utils.common import ImportErrorReporter

    markdownify = ImportErrorReporter(
        import_error,
        "web",
    )
    sync_playwright = ImportErrorReporter(
        import_error,
        "playwright in your system following guides"
        "in https://playwright.dev/python/docs/intro to run with the current",
    )

from agentscope.service import ServiceResponse, ServiceExecStatus


class WebBrowser:
    """The web browser for agent, which is implemented with playwright. This
    module allows agent to interact with web pages, such as visiting a web
    page, clicking on elements, typing text, scrolling web page, etc.

    Note:
        This module is still under development, and changes will be made in the
        future.

    Install:
        Execute the following code to install the required packages:

        .. code-block:: bash

            pip install playwright
            playwright install

    """

    def __init__(
        self,
        timeout: int = 60000,
        browser_visible: bool = True,
        browser_width: int = 1280,
        browser_height: int = 1080,
    ) -> None:
        """Initialize the web browser module.

        Args:
            timeout (`int`, defaults to `60000`):
                The timeout for the browser to wait for the page to load.
                Defaults to 60000.
            browser_visible (`bool`, defaults to `True`):
                Whether the browser is visible.
            browser_width (`int`, defaults to `1280`):
                The width of the browser. Defaults to 1280.
            browser_height (`int`, defaults to `1080`):
                The height of the browser. Defaults to 1080.
        """

        # Init a web page
        playwright_process = sync_playwright().start()
        self.browser = playwright_process.chromium.launch(
            headless=not browser_visible,
        )

        self._page = self.browser.new_page()
        self._page.set_default_timeout(timeout)
        self._page.set_viewport_size(
            {
                "width": browser_width,
                "height": browser_height,
            },
        )

        self.page_elements = []
        self._read_crawlpage_js()

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
        pass

    def action_type(self, element_id: int, text: str) -> ServiceResponse:
        """Type text into the element with the given id.

        Args:
            element_id (`int`):
                The id of the element to type text into.
            text (`str`):
                The text to type into the element.

        Returns:
            `ServiceResponse`:
                The response of the type action.
        """
        pass

    def action_scroll_up(self) -> ServiceResponse:
        """Scroll up the current web page."""
        pass

    def action_scroll_down(self) -> ServiceResponse:
        """Scroll down the current web page."""
        pass

    def action_press_key(self, key: str) -> ServiceResponse:
        """Press down a key in the current web page.

        Args:
            key (`str`):
                Chosen from `F1` - `F12`, `Digit0`- `Digit9`, `KeyA`- `KeyZ`,
                `Backquote`, `Minus`, `Equal`, `Backslash`, `Backspace`,
                `Tab`, `Delete`, `Escape`, `ArrowDown`, `End`, `Enter`,
                `Home`, `Insert`, `PageDown`, `PageUp`, `ArrowRight`, `ArrowUp`
                , etc.
        """
        pass

    # ------ Actions which are performed to change the web page ---------------
    def action_visit_url(self, url: str) -> ServiceResponse:
        """Visit the given url.

        Args:
            url (`str`):
                The url to visit in browser.
        """
        pass

    def get_action_functions(self) -> list:
        """Return a list of the available action functions."""
        return [
            self.action_click,
            self.action_type,
            self.action_scroll_up,
            self.action_scroll_down,
            self.action_press_key,
            self.action_visit_url,
        ]

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

    def close(self) -> None:
        """Close the browser"""
        self.browser.close()

    def _read_crawlpage_js(self) -> None:
        """
        Read the crawlpage JavaScript from local file.
        The JavaScript written in markpage.js will crawl all the
        interactive elements on the page, and mark them on with square marks.
        """
        current_file_path = Path(__file__)

        js_file_path = current_file_path.parent / "markpage.js"

        with open(js_file_path, "r", encoding="utf-8") as file:
            self._crawlpage_js = file.read()

    def visit_page(self, url: str) -> ServiceResponse:
        """
        Goto the given url.

        Args:
            url (str): The url to visit.
        """
        if "://" not in url:
            url = f"https://{url}"
        self._page.goto(url)
        self.client = self._page.context.new_cdp_session(self._page)
        self.page_elements = []
        time.sleep(3)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=self._page.url,
        )

    def scroll(self, direction: str) -> ServiceResponse:
        """
        Scroll towards direction.

        Args:
            direction (str): The direction to scroll. Should be Up or Down.
        """
        if direction.lower() == "up":
            self.scroll_up()
        elif direction.lower() == "down":
            self.scroll_down()
        else:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=f"Invalid scroll direction {direction}",
            )
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Scroll to {direction} done",
        )

    def scroll_up(self) -> ServiceResponse:
        """
        Scroll up the current browser window.
        """
        self._page.keyboard.down("Alt")
        self._page.keyboard.press("ArrowUp")
        self._page.keyboard.up("Alt")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Scroll up done",
        )

    def scroll_down(self) -> ServiceResponse:
        """
        Scroll down the current browser window.
        """
        self._page.keyboard.down("Alt")
        self._page.keyboard.press("ArrowDown")
        self._page.keyboard.up("Alt")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Scroll down done",
        )

    def click(self, element_id: int) -> ServiceResponse:
        """Click on the element with the given id

        Args:
            element_id (int): The id of the element to click.

        Returns:
            `ServiceResponse`: The response of the click action.
        """
        # TODO enable both logic for text-based and vision-based
        element_handle = self.page_elements[element_id]
        element_handle.evaluate(
            "element => element.setAttribute('target', '_self')",
        )
        ele_info = self._page.evaluate("getElementInfo", element_handle)
        if ele_info["tag_name"] == "button" and ele_info["type"] == "submit":
            time.sleep(5)
        element_handle.click()
        time.sleep(5)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Click on element {element_id} done",
        )

    def enter(self) -> ServiceResponse:
        """
        Press enter.
        """
        self._page.keyboard.press("Enter")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Enter pressed",
        )

    def press_key(self, key: str) -> ServiceResponse:
        """Press down a key in the current page.

        Args:
            key (`str`):
                Chosen from `F1` - `F12`, `Digit0`- `Digit9`, `KeyA`- `KeyZ`,
                `Backquote`, `Minus`, `Equal`, `Backslash`, `Backspace`,
                `Tab`, `Delete`, `Escape`, `ArrowDown`, `End`, `Enter`,
                `Home`, `Insert`, `PageDown`, `PageUp`, `ArrowRight`, `ArrowUp`
                , etc.
        """
        self._page.keyboard.press(key)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Press key: {key} done",
        )

    def type(
        self,
        element_id: int,
        text: str,
        submit: bool = False,
    ) -> ServiceResponse:
        """Type text into the element with the given id.

        Args:
            element_id (`int`):
                The id of the element to type text into.
            text (`str`):
                The text to type into the element.
            submit (`bool`, defaults to `False`):
                Whether to submit the type result after typing.

        Returns:
            `ServiceResponse`:
                The response of the type action.
        """
        self.click(element_id)
        web_ele = self.page_elements[element_id]

        # try to clear the text within the given elements
        try:
            self._page.evaluate('element => element.value = ""', web_ele)
        except Exception as e:
            logger.info(
                f"Exception {str(e)}, "
                "unable to clear the value within the given elements.",
            )

        # focus on the element to type
        self._page.evaluate("element => element.focus()", web_ele)

        web_ele.type(text)
        time.sleep(2)
        if submit:
            web_ele.press("Enter")
        time.sleep(2)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Typing done",
        )

    def go_back(self) -> ServiceResponse:
        """Go back to the previous page"""
        self._page.go_back()
        time.sleep(2)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content="Go back done",
        )

    def focus_element(self, element_id: int) -> ServiceResponse:
        """Scroll the browser window to focus on the element with the given id.

        Args:
            element_id (`int`) :
                The id of the element to focus on.

        Returns:
            `ServiceResponse`:
                The response of the focus action.
        """
        web_ele = self.page_elements[element_id]
        web_ele.evaluate("element => element.focus()")
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=f"Focus on element {element_id} done",
        )

    # from webvoyager
    def try_click_body(self) -> None:
        """Try to click the main body of webpage."""
        try:
            self._page.locator("body").click()
        except Exception as e:
            logger.info(
                f"Unable to locate and click 'body' in webpage, {str(e)}",
            )

    def _remove_labels_by_handle(self, labels_handle: object) -> None:
        """
        Remove the SOM labels by their element handles.
        """
        labels_js_handles = labels_handle.evaluate_handle("labels => labels")
        labels = labels_js_handles.get_properties().values()
        for label in labels:
            label.as_element().evaluate("el => el.remove()")

    def crawl_page(
        self,
        vision: bool = True,
        with_meta: bool = False,
        with_select: bool = False,
    ) -> tuple:
        """Process the current page, return the interactive elements and
        corresponding infos.

        Args:
            vision (`bool`):
                Will add set-of-mark to webpage if vision is enabled.
                Set-of-mark is a visual prompting method that
                partition an image into numbered regions,
                to improve the visual grounding ability of LLMs.
                Here, instead of using segmentation model, we use the native
                JavaScript to bound the interactive elements in the webpage.
                You can refer to the paper https://arxiv.org/abs/2310.11441
                if you want to know more details about set-of-mark.
            with_meta (`bool`):
                Whether to include meta_data field in the returned format text.
            with_select (`bool`):
                Return only the selected interactive elements or all
                interactive elements.

        Returns:
            elements:
                the handler from playwright of interactive elements.
            format_ele_text:
                a list of the formated elements' text description.
            screenshot_bytes:
                the screenshot of webpage, with SOM, in bytes.
            web_ele_infos:
                the info dict of interactive elements.

        """
        js_script = self._crawlpage_js

        self._page.evaluate(js_script)
        result_handle = self._page.evaluate_handle(
            f"crawlPage({str(vision).lower()})",
        )

        labels_handle = result_handle.get_property("labels")
        items_handle = result_handle.get_property("items")

        items_js_handles = (
            items_handle.evaluate_handle("items => items")
            .get_properties()
            .values()
        )
        elements = [
            item.get_property("element").as_element()
            for item in items_js_handles
            # if item.get_property("element").as_element()
        ]

        self.page_elements = elements

        items_raw = items_handle.json_value()
        web_ele_infos = [
            self._page.evaluate("getElementInfo", ele) for ele in elements
        ]

        format_ele_text = []
        input_attr_types = ["text", "search", "password", "email", "tel"]
        for web_ele_id in range(len(elements)):
            label_text = items_raw[web_ele_id]["text"]
            ele_tag_name = web_ele_infos[web_ele_id]["tag_name"]
            ele_type = web_ele_infos[web_ele_id]["type"]
            ele_aria_label = web_ele_infos[web_ele_id]["aria_label"]
            ele_meta_data = web_ele_infos[web_ele_id]["meta_data"]
            meta_string = " ".join(ele_meta_data)
            meta = f" {meta_string}"

            # TODO for page too long, we should add selection
            # on whether the element is in view port
            if with_select and not (
                (
                    not label_text
                    and (
                        (
                            ele_tag_name == "input"
                            and ele_type in input_attr_types
                        )
                        or ele_tag_name == "textarea"
                        or (
                            ele_tag_name == "button"
                            and ele_type in ["submit", "button"]
                        )
                    )
                )
                or (
                    label_text
                    and len(label_text) < 200
                    and not ("<img" in label_text and "src=" in label_text)
                )
            ):
                continue

            message = f"[{web_ele_id}]: <{ele_tag_name}>"
            if meta and with_meta:
                message += f"<meta data: {meta}>"
            if ele_aria_label:
                message += f'"<{ele_aria_label}>"'
            if label_text:
                message += f'"text: {label_text}"'
            format_ele_text.append(message)

        screenshot_bytes = None

        if vision:
            screenshot_bytes = self.page_screenshot
            self._remove_labels_by_handle(labels_handle)

        time.sleep(3)

        return elements, format_ele_text, screenshot_bytes, web_ele_infos
