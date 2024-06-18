# -*- coding: utf-8 -*-
"""
The web browser interface referenced from https://github.com/nat/natbot/,
and make it suitable for agentscope
"""
import markdownify
from playwright.sync_api import sync_playwright

from agentscope.file_manager import file_manager


class WebBrowser:
    """
    Web browser interface using playwright + chrome
    """

    def __init__(
        self,
        headless: bool = False,
    ) -> None:
        self.headless = headless
        self.current_step = 0

        self.playwright_process = sync_playwright().start()
        self.browser = self.playwright_process.chromium.launch(
            headless=headless,
        )
        self.page = self.browser.new_page()
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = {}

    def visit_page(self, url: str) -> None:
        if "://" not in url:
            url = f"https://{url}"
        self.page.goto(url)
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = {}

    def scroll_up(self):
        self.page.evaluate(
            "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop - window.innerHeight;",
        )

    def scroll_down(self):
        self.page.evaluate(
            "(document.scrollingElement || document.body).scrollTop = (document.scrollingElement || document.body).scrollTop + window.innerHeight;",
        )

    def click(self, id: int):
        """
        Click on the element with the given id
        """
        # TODO enable both logic for text-based and vision-based
        pass

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

    def type_key(self, id: int, text: str):
        # TODO determin where to type?
        """
        Type text in the current page
        Args:
            text(`str`) : text to type
        """
        self.click(id)
        self.page.keyboard.type(text)

    def go_back(self):
        """Go back to the previous page"""
        self.page.go_back()

    @property
    def page_html(self):
        return self.page.content()

    @property
    def page_title(self):
        return self.page.title()

    @property
    def page_markdown(self):
        return markdownify.markdownify(self.page_html)

    def get_elements(self):
        # TODO get the elements to click as the nat_bot from text
        # TODO support more elements
        pass

    def page_screenshot(self, with_mark=False):
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
