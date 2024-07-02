# -*- coding: utf-8 -*-
"""
The web browser interface referenced from https://github.com/nat/natbot/,
and make it suitable for agentscope
"""
import time
import requests
from pathlib import Path
import markdownify
from sys import platform
from playwright.sync_api import sync_playwright

from agentscope.file_manager import file_manager

debug = False


class WebBrowser:
    """
    Web browser interface using playwright + chrome
    """

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60000,
        default_width = 1280,
        default_height = 1080,
    ) -> None:
        self.headless = headless
        self.current_step = 0

        self.playwright_process = sync_playwright().start()
        self.browser = self.playwright_process.chromium.launch(
            headless=headless,
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(timeout)
        self.page.set_viewport_size(
            {"width": default_width, "height": default_height}
        )
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = []
        self._read_crawlpage_js()

    def _read_crawlpage_js(self):
        current_file_path = Path(__file__)

        js_file_path = current_file_path.parent / "markpage.js"

        with open(js_file_path, "r", encoding="utf-8") as file:
            self._crawlpage_js = file.read()

    def visit_page(self, url: str) -> None:
        if "://" not in url:
            url = f"https://{url}"
        self.page.goto(url)
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = []

    def scroll(self, direction):
        if direction == "up":
            self.scroll_up()
        elif direction == "down":
            self.scroll_down()

    def scroll_up(self):
        # self.page.evaluate(
        #     "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop - window.innerHeight;",
        # )
        self.page.keyboard.down("Alt")
        self.page.keyboard.press("ArrowUp")
        self.page.keyboard.up("Alt")

    def scroll_down(self):
        # self.page.evaluate(
        #     "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop + window.innerHeight;",
        # )
        self.page.keyboard.down("Alt")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.up("Alt")

    def click(self, click_id: int):
        """
        Click on the element with the given id

        Note: The id should start from 0
        """
        # TODO enable both logic for text-based and vision-based
        element_handle = self.page_elements[click_id]
        element_handle.evaluate(
            "element => element.setAttribute('target', '_self')",
        )
        element_handle.click()

    def find_on_page(self, query: str) -> bool:
        """
        Find the query in the current page, make it center of the page,
        behave like control_f

        Returns:
            bool : whether the query is found
        """
        # TODO
        pass

    def find_next(self):
        """
        Goto the next position of the previous ctrl-f query
        """
        # TODO
        pass

    def enter(self):
        self.page.keyboard.press("Enter")

    def press_key(self, key: str):
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

    def type(self, click_id: int, text: str, submit=False):
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
        except:
            pass

        # focus on the element to type
        self.page.evaluate("element => element.focus()", web_ele)

        web_ele.type(text)
        time.sleep(2)
        if submit:
            web_ele.press("Enter")
        time.sleep(3)

    def go_back(self):
        """Go back to the previous page"""
        self.page.go_back()

    def focus_element(self, ele_id):
        web_ele = self.page_elements[ele_id]
        web_ele.evaluate("element => element.focus()")

    # from webvoyager
    def try_click_body(self) -> None:
        try:
            self.page.locator("body").click()
        except:
            pass

    def prevent_space(self) -> None:
        try:
            self.page.evaluate("""
                window.onkeydown = function(e) {
                    if(e.keyCode == 32 && e.target.type != 'text' && e.target.type != 'textarea') {
                        e.preventDefault();
                    }
                };
            """# noqa
            )
            # do we need sleep here?
            time.sleep(5)
        except:
            pass

    def _remove_labels_by_handle(self, labels_handle):
        labels_js_handles = labels_handle.evaluate_handle("labels => labels")
        labels = labels_js_handles.get_properties().values()
        for label in labels:
            label.as_element().evaluate("el => el.remove()")

    def crawl_page(self, vision=True, with_meta=False, with_select=False):
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

        time.sleep(5)

        return elements, format_ele_text, screenshot_bytes, web_ele_infos

    @property
    def url(self):
        return self.page.url

    @property
    def page_html(self):
        return self.page.content()

    @property
    def page_title(self):
        return self.page.title()

    @property
    def page_markdown(self):
        return markdownify.markdownify(self.page_html)

    def get_jina_page(self):
        jina_url = "https://r.jina.ai/" + self.url
        try:
            page_text = requests.get(jina_url).text
            return page_text
        except:
            return (
                f"The page in {self.url} is not loaded yet"
                "you should check the request connection or api qutoa"
            )

    def get_elements(self):
        # TODO get the elements to click as the nat_bot from text
        # TODO support more elements
        pass

    def page_screenshot(self) -> bytes:
        # TODO makesure the mark is aligned with page elements id
        """
        Get the screen shot of the current page

        Args:
            with_mark(`bool`) :
                whether to add the set of mark to the screen shot,
                showing all clickable elements and their id
        """
        # TODO modify file_manager save_image function to make it accept bytes
        # TODO add the mark to the screen shot
        # file_manager.save_image(
        #     self.page.screenshot(),
        #     filename=f"web_step{self.current_step}_screenshot.png"
        # )
        return self.page.screenshot()

    def close(self):
        self.browser.close()
