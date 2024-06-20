# -*- coding: utf-8 -*-
"""
The web browser interface referenced from https://github.com/nat/natbot/,
and make it suitable for agentscope
"""
import time
import Path
import markdownify
from sys import platform
from playwright.sync_api import sync_playwright

from agentscope.file_manager import file_manager

debug = False

# from nat bot
black_listed_elements = set(
    [
        "html",
        "head",
        "title",
        "meta",
        "iframe",
        "body",
        "script",
        "style",
        "path",
        "svg",
        "br",
        "::marker",
    ]
)


class WebBrowser:
    """
    Web browser interface using playwright + chrome
    """

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60000,
    ) -> None:
        self.headless = headless
        self.current_step = 0

        self.playwright_process = sync_playwright().start()
        self.browser = self.playwright_process.chromium.launch(
            headless=headless,
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(timeout)
        self.page.set_viewport_size({"width": 1280, "height": 1080})
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = {}
        self.page_element_buffer = {}
        self._read_markpage_js()

    def _read_markpage_js(self):
        current_file_path = Path(__file__)

        js_file_path = current_file_path.parent / "markpage.js"

        with open(js_file_path, "r", encoding="utf-8") as file:
            self._markpage_js = file.read()

    def visit_page(self, url: str) -> None:
        if "://" not in url:
            url = f"https://{url}"
        self.page.goto(url)
        self.client = self.page.context.new_cdp_session(self.page)
        self.page_elements = {}
        self.page_element_buffer = {}

    def scroll(self, direction):
        if direction == "up":
            self.scroll_up()
        elif direction == "down":
            self.scroll_down()

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
        js = """
        links = document.getElementsByTagName("a");
        for (var i = 0; i < links.length; i++) {
            links[i].removeAttribute("target");
        }
        """
        print("Perfroming click on ", self.page_element_buffer.get(int(id)))
        self.page.evaluate(js)

        element = self.page_element_buffer.get(int(id))
        if element:
            x = element.get("center_x")
            y = element.get("center_y")

            self.page.mouse.click(x, y)
            # self.page.click('textarea[aria-label="搜索"]')
        else:
            print("Could not find element")

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

    def type(self, id: int, text: str):
        # TODO determin where to type?
        """
        Type text in the current page
        Args:
            text(`str`) : text to type
        """
        self.click(id)
        # print("typing text:", text)
        self.page.keyboard.type(text)
        # self.enter()

    def go_back(self):
        """Go back to the previous page"""
        self.page.go_back()

    # from webvoyager
    def try_click_body(self) -> None:
        try:
            self.page.locator("body").click()
        except:
            pass

    def prevent_space(self) -> None:
        self.page.evaluate(
            """
            window.onkeydown = function(e) {
                if(e.keyCode == 32 && e.target.type != 'text' && e.target.type != 'textarea') {
                    e.preventDefault();
                }
            };
        """
        )
        # do we need sleep here?
        time.sleep(5)

    def _get_web_element_rect(self):

        js_script = self._markpage_js

        # 执行 JavaScript 代码 并获得返回对象
        result_handle = self.page.evaluate_handle(js_script)

        # 获取各个属性的句柄
        labels_handle = result_handle.get_property("labels")
        items_handle = result_handle.get_property("items")

        # 提取labels的实际DOM元素
        rects = labels_handle.evaluate(
            "labels => labels.map(label => label.getBoundingClientRect())"
        )

        items_js_handles = (
            items_handle.evaluate_handle("items => items")
            .get_properties()
            .values()
        )
        elements = [
            item.get_property("element").as_element()
            for item in items_js_handles
            if item.get_property("element").as_element()
        ]

        # 提取items的实际DOM元素
        # is items raw nessessary?
        items_raw = items_handle.json_value()

        format_ele_text = []
        input_attr_types = ["text", "search", "password", "email", "tel"]

        web_ele_fields = []

        for web_ele_id in range(len(items_raw)):
            label_text = items_raw[web_ele_id]["text"]
            ele = elements[web_ele_id]  # 直接使用元素句柄
            ele_tag_name = self.page.evaluate(
                "ele => ele.tagName", ele
            ).lower()
            # ele_type = self.page.evaluate("ele => ele.type", ele) if ele_tag_name == "input" else ""
            ele_type = self.page.evaluate(
                "ele => ele.getAttribute('type')", ele
            )
            ele_aria_label = self.page.evaluate(
                "ele => ele.getAttribute('aria-label')", ele
            )
            web_ele_fields.append(
                {
                    "label_text": label_text,
                    "tag_name": ele_tag_name,
                    "type": ele_type,
                    "aria_label": ele_aria_label,
                }
            )

            if not label_text:
                if (
                    (ele_tag_name == "input" and ele_type in input_attr_types)
                    or ele_tag_name == "textarea"
                    or (
                        ele_tag_name == "button"
                        and ele_type in ["submit", "button"]
                    )
                ):
                    if ele_aria_label:
                        format_ele_text.append(
                            f'[{web_ele_id}]: <{ele_tag_name}> "{ele_aria_label}";'
                        )
                    else:
                        format_ele_text.append(
                            f'[{web_ele_id}]: <{ele_tag_name}> "{label_text}";'
                        )
            elif label_text and len(label_text) < 200:
                if not ("<img" in label_text and "src=" in label_text):
                    if ele_tag_name in ["button", "input", "textarea"]:
                        if ele_aria_label and (ele_aria_label != label_text):
                            format_ele_text.append(
                                f'[{web_ele_id}]: <{ele_tag_name}> "{label_text}", "{ele_aria_label}";'
                            )
                        else:
                            format_ele_text.append(
                                f'[{web_ele_id}]: <{ele_tag_name}> "{label_text}";'
                            )
                    else:
                        if ele_aria_label and (ele_aria_label != label_text):
                            format_ele_text.append(
                                f'[{web_ele_id}]: "{label_text}", "{ele_aria_label}";'
                            )
                        else:
                            format_ele_text.append(
                                f'[{web_ele_id}]: "{label_text}";'
                            )

        format_ele_text = "\t".join(format_ele_text)

        screenshot_bytes = self.page_screenshot()

        self._remove_labels_by_handle(labels_handle)

        time.sleep(5)

        return elements, format_ele_text, screenshot_bytes, web_ele_fields

    def _remove_labels_by_handle(self, labels_handle):
        labels_js_handles = labels_handle.evaluate_handle("labels => labels")
        labels = labels_js_handles.get_properties().values()
        for label in labels:
            label.as_element().evaluate("el => el.remove()")

    def _crawl_by_mark(self):
        (
            elements,
            format_ele_text,
            screenshot_bytes,
            web_ele_fields,
        ) = self._get_web_element_rect()
        return elements, format_ele_text, screenshot_bytes, web_ele_fields

    def _crawl_by_text(self) -> list[str]:
        """
        Referenced from natbot, to build text based web crawler

        The returned browser content of a web page looks like:
        ```
        CURRENT BROWSER CONTENT:
        ------------------
        <link id=1>About</link>
        <link id=2>Store</link>
        <link id=3>Gmail</link>
        <link id=4>Images</link>
        <link id=5>(Google apps)</link>
        <link id=6>Sign in</link>
        <img id=7 alt="(Google)"/>
        <input id=8 alt="Search"></input>
        <button id=9>(Search by voice)</button>
        <button id=10>(Google Search)</button>
        <button id=11>(I'm Feeling Lucky)</button>
        <link id=12>Advertising</link>
        <link id=13>Business</link>
        <link id=14>How Search works</link>
        <link id=15>Carbon neutral since 2007</link>
        <link id=16>Privacy</link>
        <link id=17>Terms</link>
        <text id=18>Settings</text>
        ------------------
        ```
        """
        page = self.page
        page_element_buffer = self.page_element_buffer
        start = time.time()

        device_pixel_ratio = page.evaluate("window.devicePixelRatio")
        if platform == "darwin" and device_pixel_ratio == 1:  # lies
            device_pixel_ratio = 2
        # device_pixel_ratio = 2

        win_upper_bound = page.evaluate("window.pageYOffset")
        win_left_bound = page.evaluate("window.pageXOffset")
        win_width = page.evaluate("window.screen.width")
        win_height = page.evaluate("window.screen.height")
        win_right_bound = win_left_bound + win_width
        win_lower_bound = win_upper_bound + win_height


        tree = self.client.send(
            "DOMSnapshot.captureSnapshot",
            {
                "computedStyles": [],
                "includeDOMRects": True,
                "includePaintOrder": True,
            },
        )

        # print("tree here is:", tree)
        strings = tree["strings"]
        document = tree["documents"][0]
        nodes = document["nodes"]
        backend_node_id = nodes["backendNodeId"]
        attributes = nodes["attributes"]
        node_value = nodes["nodeValue"]
        parent = nodes["parentIndex"]
        node_types = nodes["nodeType"]
        node_names = nodes["nodeName"]
        is_clickable = set(nodes["isClickable"]["index"])
        if debug:
            print("Clickables:", nodes["isClickable"])

        text_value = nodes["textValue"]
        text_value_index = text_value["index"]
        text_value_values = text_value["value"]

        input_value = nodes["inputValue"]
        input_value_index = input_value["index"]
        input_value_values = input_value["value"]

        input_checked = nodes["inputChecked"]
        layout = document["layout"]
        layout_node_index = layout["nodeIndex"]
        bounds = layout["bounds"]

        cursor = 0
        html_elements_text = []

        child_nodes = {}
        elements_in_view_port = []

        anchor_ancestry = {"-1": (False, None)}
        button_ancestry = {"-1": (False, None)}

        def convert_name(node_name, has_click_handler):
            if node_name == "a":
                return "link"
            if node_name == "input":
                return "input"
            if node_name == "textarea":
                return "textarea"
            if node_name == "img":
                return "img"
            if (
                node_name == "button" or has_click_handler
            ):  # found pages that needed this quirk
                return "button"
            else:
                return "text"

        def find_attributes(attributes, keys):
            values = {}

            for [key_index, value_index] in zip(*(iter(attributes),) * 2):
                if value_index < 0:
                    continue
                key = strings[key_index]
                value = strings[value_index]

                if key in keys:
                    values[key] = value
                    keys.remove(key)

                    if not keys:
                        return values

            return values

        def add_to_hash_tree(hash_tree, tag, node_id, node_name, parent_id):
            parent_id_str = str(parent_id)
            if not parent_id_str in hash_tree:
                parent_name = strings[node_names[parent_id]].lower()
                grand_parent_id = parent[parent_id]

                add_to_hash_tree(
                    hash_tree,
                    tag,
                    parent_id,
                    parent_name,
                    grand_parent_id,
                )

            is_parent_desc_anchor, anchor_id = hash_tree[parent_id_str]

            # even if the anchor is nested in another anchor, we set the "root" for all descendants to be ::Self
            if node_name == tag:
                value = (True, node_id)
            elif (
                is_parent_desc_anchor
            ):  # reuse the parent's anchor_id (which could be much higher in the tree)
                value = (True, anchor_id)
            else:
                value = (
                    False,
                    None,
                )  # not a descendant of an anchor, most likely it will become text, an interactive element or discarded

            hash_tree[str(node_id)] = value

            return value

        for index, node_name_index in enumerate(node_names):
            node_parent = parent[index]
            node_name = strings[node_name_index].lower()

            is_ancestor_of_anchor, anchor_id = add_to_hash_tree(
                anchor_ancestry,
                "a",
                index,
                node_name,
                node_parent,
            )

            is_ancestor_of_button, button_id = add_to_hash_tree(
                button_ancestry,
                "button",
                index,
                node_name,
                node_parent,
            )

            try:
                cursor = layout_node_index.index(
                    index,
                )  # todo replace this with proper cursoring, ignoring the fact this is O(n^2) for the moment
            except:
                continue

            if node_name in black_listed_elements:
                continue

            [x, y, width, height] = bounds[cursor]
            x /= device_pixel_ratio
            y /= device_pixel_ratio
            width /= device_pixel_ratio
            height /= device_pixel_ratio

            elem_left_bound = x
            elem_top_bound = y
            elem_right_bound = x + width
            elem_lower_bound = y + height

            partially_is_in_viewport = (
                elem_left_bound < win_right_bound
                and elem_right_bound >= win_left_bound
                and elem_top_bound < win_lower_bound
                and elem_lower_bound >= win_upper_bound
            )

            if not partially_is_in_viewport:
                continue

            meta_data = []

            # inefficient to grab the same set of keys for kinds of objects but its fine for now
            element_attributes = find_attributes(
                attributes[index],
                ["type", "placeholder", "aria-label", "title", "alt"],
            )

            ancestor_exception = is_ancestor_of_anchor or is_ancestor_of_button
            ancestor_node_key = (
                None
                if not ancestor_exception
                else str(anchor_id)
                if is_ancestor_of_anchor
                else str(button_id)
            )
            ancestor_node = (
                None
                if not ancestor_exception
                else child_nodes.setdefault(str(ancestor_node_key), [])
            )

            if node_name == "#text" and ancestor_exception:
                text = strings[node_value[index]]
                if text == "|" or text == "•":
                    continue
                ancestor_node.append(
                    {
                        "type": "type",
                        "value": text,
                    }
                )
            else:
                if (
                    node_name == "input"
                    and element_attributes.get("type") == "submit"
                ) or node_name == "button":
                    node_name = "button"
                    element_attributes.pop(
                        "type",
                        None,
                    )  # prevent [button ... (button)..]

                for key in element_attributes:
                    if ancestor_exception:
                        ancestor_node.append(
                            {
                                "type": "attribute",
                                "key": key,
                                "value": element_attributes[key],
                            }
                        )
                    else:
                        meta_data.append(element_attributes[key])

            element_node_value = None

            if node_value[index] >= 0:
                element_node_value = strings[node_value[index]]
                if (
                    element_node_value == "|"
                ):  # commonly used as a seperator, does not add much context - lets save ourselves some token space
                    continue
            elif (
                node_name == "input"
                and index in input_value_index
                and element_node_value is None
            ):
                node_input_text_index = input_value_index.index(index)
                text_index = input_value_values[node_input_text_index]
                if node_input_text_index >= 0 and text_index >= 0:
                    element_node_value = strings[text_index]

            # remove redudant elements
            if ancestor_exception and (
                node_name != "a" and node_name != "button"
            ):
                continue

            elements_in_view_port.append(
                {
                    "node_index": str(index),
                    "backend_node_id": backend_node_id[index],
                    "node_name": node_name,
                    "node_value": element_node_value,
                    "node_meta": meta_data,
                    "is_clickable": index in is_clickable,
                    "origin_x": int(x),
                    "origin_y": int(y),
                    "center_x": int(x + (width / 2)),
                    "center_y": int(y + (height / 2)),
                },
            )
            if debug:
                print("Added elements, ", elements_in_view_port[-1])

        # lets filter further to remove anything that does not hold any text nor has click handlers + merge text from leaf#text nodes with the parent
        elements_of_interest = []
        id_counter = 0

        for element in elements_in_view_port:
            node_index = element.get("node_index")
            node_name = element.get("node_name")
            node_value = element.get("node_value")
            is_clickable = element.get("is_clickable")
            origin_x = element.get("origin_x")
            origin_y = element.get("origin_y")
            center_x = element.get("center_x")
            center_y = element.get("center_y")
            meta_data = element.get("node_meta")

            inner_text = f"{node_value} " if node_value else ""
            meta = ""

            if node_index in child_nodes:
                for child in child_nodes.get(node_index):
                    entry_type = child.get("type")
                    entry_value = child.get("value")

                    if entry_type == "attribute":
                        entry_key = child.get("key")
                        meta_data.append(f'{entry_key}="{entry_value}"')
                    else:
                        inner_text += f"{entry_value} "

            if meta_data:
                meta_string = " ".join(meta_data)
                meta = f" {meta_string}"

            if inner_text != "":
                inner_text = f"{inner_text.strip()}"

            converted_node_name = convert_name(node_name, is_clickable)

            # not very elegant, more like a placeholder
            if (
                (converted_node_name != "button" or meta == "")
                and converted_node_name != "link"
                and converted_node_name != "input"
                and converted_node_name != "img"
                and converted_node_name != "textarea"
            ) and inner_text.strip() == "":
                continue

            self.page_element_buffer[id_counter] = element

            if inner_text != "":
                # e.g. <link id=1>About</link>
                elements_of_interest.append(
                    f"""<{converted_node_name} id={id_counter}{meta}>{inner_text}</{converted_node_name}>""",
                )
            else:
                # e.g. <img id=7 alt="(Google)"/>
                elements_of_interest.append(
                    f"""<{converted_node_name} id={id_counter}{meta}/>""",
                )
            id_counter += 1

        print("Parsing time: {:0.2f} seconds".format(time.time() - start))
        return elements_of_interest

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
