# -*- coding: utf-8 -*-
"""
The web browser interface for agentscope
"""
import time
from pathlib import Path

import requests
import markdownify
from loguru import logger

try:
    from playwright.sync_api import sync_playwright
except ImportError as import_error:
    from agentscope.utils.tools import ImportErrorReporter

    sync_playwright = ImportErrorReporter(
        import_error,
        "playwright in your system following guides"
        "in https://playwright.dev/python/docs/intro to run with the current",
    )


class WebBrowser:
    """
    Web browser interface using playwright + built-in browser.

    This class serve as an interface between agentscope's agent and
    the web browser to control. The interface is still under update, and more
    interactive actions, better webpage format presentation will be added
    in the future.

    You have to run `pip install playwright` to install python env
    and `playwright install` to install the browser before using it.
    """

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60000,
        default_width: int = 1280,
        default_height: int = 1080,
    ) -> None:
        """
        Init the playwright process and web browser.

        Args:
            headless (bool, optional):
                Whether to run the browser in headless mode. Defaults to False.
                When set to False, the browser will be visible to user.
            timeout (int, optional):
                The timeout for the browser to wait for the page to load.
                Defaults to 60000.
            default_width (int, optional):
                The default width of the browser. Defaults to 1280.
            default_height (int, optional):
                The default height of the browser. Defaults to 1080.
        """
        self.headless = headless
        self.current_step = 0

        self.playwright_process = sync_playwright().start()
        self.browser = self.playwright_process.chromium.launch(
            headless=headless,
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(timeout)
        self.page.set_viewport_size(
            {"width": default_width, "height": default_height},
        )
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = []
        self._read_crawlpage_js()

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

    def visit_page(self, url: str) -> None:
        """
        Goto the given url.
        """
        if "://" not in url:
            url = f"https://{url}"
        self.page.goto(url)
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = []

    def scroll(self, direction: str) -> None:
        """
        Scroll towards direction.
        """
        if direction == "up":
            self.scroll_up()
        elif direction == "down":
            self.scroll_down()

    def scroll_up(self) -> None:
        """
        Scroll up the current browser window.
        """
        self.page.keyboard.down("Alt")
        self.page.keyboard.press("ArrowUp")
        self.page.keyboard.up("Alt")

    def scroll_down(self) -> None:
        """
        Scroll down the current browser window.
        """
        self.page.keyboard.down("Alt")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.up("Alt")

    def click(self, click_id: int) -> None:
        """
        Click on the element with the given id

        Note: The id should start from 0
        """
        # TODO enable both logic for text-based and vision-based
        element_handle = self.page_elements[click_id]
        element_handle.evaluate(
            "element => element.setAttribute('target', '_self')",
        )
        ele_info = element_handle.evaluate(
            "element => element.getBoundingClientRect()",
        )
        ele_info = self.page.evaluate("getElementInfo", element_handle)
        if ele_info["tag_name"] == "button" and ele_info["type"] == "submit":
            time.sleep(5)
        element_handle.click()
        time.sleep(3)

    def find_on_page(self, query: str) -> bool:
        """
        Find the query in the current page, make it center of the page,
        behave like control_f

        Returns:
            bool : whether the query is found
        """
        # TODO the function is not yet implement
        # TODO whether to implement this in javascript or find other methods
        logger.info(f"Searching on {query}")
        return False

    def find_next(self) -> None:
        """
        Goto the next position of the previous ctrl-f query
        """
        # TODO add this
        return None

    def enter(self) -> None:
        """
        Press enter.
        """
        self.page.keyboard.press("Enter")

    def press_key(self, key: str) -> None:
        """
        Press down a key in the current page
        Args:
            key(`str`) : `F1` - `F12`, `Digit0`- `Digit9`, `KeyA`- `KeyZ`,
            `Backquote`, `Minus`, `Equal`, `Backslash`, `Backspace`, `Tab`,
            `Delete`, `Escape`, `ArrowDown`, `End`, `Enter`, `Home`, `Insert`,
            `PageDown`, `PageUp`, `ArrowRight`, `ArrowUp`,
        etc.
        """
        self.page.keyboard.press(key)

    def type(self, click_id: int, text: str, submit: bool = False) -> None:
        """
        Type text in the given elements
        Args:
            text(`str`) : text to type
        """
        self.click(click_id)
        web_ele = self.page_elements[click_id]

        # try to clear the text within the given elements
        try:
            self.page.evaluate('element => element.value = ""', web_ele)
        except Exception as e:
            logger.info(
                f"Expection {str(e)}, "
                "unable to clear the value within the given elements.",
            )

        # focus on the element to type
        self.page.evaluate("element => element.focus()", web_ele)

        web_ele.type(text)
        time.sleep(2)
        if submit:
            web_ele.press("Enter")
        time.sleep(2)

    def go_back(self) -> None:
        """Go back to the previous page"""
        self.page.go_back()

    def focus_element(self, ele_id: int) -> None:
        """
        Focus on the element with given id.
        """
        web_ele = self.page_elements[ele_id]
        web_ele.evaluate("element => element.focus()")

    # from webvoyager
    def try_click_body(self) -> None:
        """
        Try to click the main body of webpage.
        """
        try:
            self.page.locator("body").click()
        except Exception as e:
            logger.info(
                f"Unable to locat and click 'body' in webpage, {str(e)}",
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
        """
        Process the current page, return the interactive elements and
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
                the text description of formated elements.
            screenshot_bytes:
                the screenshot of webpage, with SOM, in bytes.
            web_ele_infos:
                the info dict of interactive elements.

        """
        js_script = self._crawlpage_js

        self.page.evaluate(js_script)
        result_handle = self.page.evaluate_handle(
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
            self.page.evaluate("getElementInfo", ele) for ele in elements
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
            screenshot_bytes = self.page_screenshot()
            self._remove_labels_by_handle(labels_handle)

        time.sleep(3)

        return elements, format_ele_text, screenshot_bytes, web_ele_infos

    @property
    def url(self) -> str:
        """return the url of current page"""
        return self.page.url

    @property
    def page_html(self) -> str:
        """return the html content of current page"""
        return self.page.content()

    @property
    def page_title(self) -> str:
        """return the title of current page"""
        return self.page.title()

    @property
    def page_markdown(self) -> str:
        """return the content of current page, in markdown format"""
        return markdownify.markdownify(self.page_html)

    def _get_jina_page(self) -> str:
        """return the formattted current page text, using api from jina"""
        jina_url = "https://r.jina.ai/" + self.url
        try:
            page_text = requests.get(jina_url).text
            return page_text
        except Exception as e:
            return (
                f"Enconter exception {str(e)}"
                f"The page in {self.url} might not be loaded yet"
                "you might want to check the request connection or api qutoa."
            )

    def page_screenshot(self) -> bytes:
        # TODO whether to keep this or intergrate into crawlpage.
        """
        Get the screen shot of the current page
        """
        return self.page.screenshot()

    def close(self) -> None:
        """close the browser"""
        self.browser.close()
