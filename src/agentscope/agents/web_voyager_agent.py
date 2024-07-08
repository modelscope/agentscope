# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""The WebVoyager agent, an innovative MLLM powered web agent that can
interacting with real-world websites with vision.
Implementation referenced on https://github.com/MinorJerry/WebVoyager/tree/main
The paper link is https://arxiv.org/abs/2401.13919.
"""
import time
import os
import re
from typing import Optional, Tuple, Any

from loguru import logger


from agentscope.agents import AgentBase
from agentscope.message import message_from_dict, Msg
from agentscope.browser.web_browser import WebBrowser
from agentscope.file_manager import file_manager


DEFAULT_SYSTEM_PROMPT = """
Imagine you are a robot browsing the web, just like humans. Now you need to complete a task.
In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. This screenshot will feature Numerical Labels placed in the TOP LEFT corner of each Web Element.
Carefully analyze the visual information to identify the Numerical Label corresponding to the Web Element that requires interaction, then follow the guidelines and choose one of the following actions:
- Click a Web Element.
- Type content in a textbox. It will delete existing content in the text box.
- Scroll up or down. Multiple scrolls are allowed to browse the webpage. Pay attention!! The default scroll is the whole window. If the scroll widget is located in a certain area of the webpage, then you have to specify a Web Element in that area. I would hover the mouse there and then scroll.
- Wait. Typically used to wait for unfinished webpage processes, with a duration of 5 seconds.
- Go back, returning to the previous webpage.
- Google, directly jump to the Google search page. When you can't find information in some websites, try starting over with Google.
- Answer. This action should only be chosen when all questions in the task have been solved.

Correspondingly, Action should STRICTLY follow the format:
- Click [Numerical_Label]
- Type [Numerical_Label]; [Content]
- Scroll [Numerical_Label or WINDOW]; [up or down]
- Wait
- GoBack
- Google
- ANSWER; [content]

Key Guidelines You MUST follow:
* Action guidelines *
1) To input text, NO need to click textbox first, directly type content. After typing, the system automatically hits `ENTER` key. Sometimes you should click the search button to apply search filters. Try to use simple language when searching.
2) You must Distinguish between textbox and search button, don't type content into the button! If no textbox is found, you may need to click the search button first before the textbox is displayed.
3) Execute only one action per iteration.
4) STRICTLY Avoid repeating the same action if the webpage remains unchanged. You may have selected the wrong web element or numerical label. Continuous use of the Wait is also NOT allowed.
5) When a complex Task involves multiple questions or steps, select "ANSWER" only at the very end, after addressing all of these questions (steps). Flexibly combine your own abilities with the information in the web page. Double check the formatting requirements in the task when ANSWER.
* Web Browsing Guidelines *
1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages. Pay attention to Key Web Elements like search textbox and menu.
2) Vsit video websites like YouTube is allowed BUT you can't play videos. Clicking to download PDF is allowed and will be analyzed by the Assistant API.
3) Focus on the numerical labels in the TOP LEFT corner of each rectangle (element). Ensure you don't mix them up with other numbers (e.g. Calendar) on the page.
4) Focus on the date in task, you must look for results that match the date. It may be necessary to find the correct year, month and day at calendar.
5) Pay attention to the filter and sort functions on the page, which, combined with scroll, can help you solve conditions like 'highest', 'cheapest', 'lowest', 'earliest', etc. Try your best to find the answer that best fits the task.

Your reply should strictly follow the format:
Thought: {Your brief thoughts (briefly summarize the info that will help ANSWER)}
Action: {One Action format you choose}

Then the User will provide:
Observation: {A labeled screenshot Given by User}
"""  # noqa

INIT_MSG_PROMPT = """Now given a task: {task_question}, Please interact with {task_web_url} and get the answer.
Observation: please analyze the attached screenshot and give the Thought and Action.
I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information. The textual information in the current round is: \n{web_text}. Please note that the label number may change in the next round, so always choose within the lastest round's number.
"""  # noqa

OBS_MSG_PROMPT = """Observation:{warn_obs} please analyze the attached screenshot and give the Thought and Action. I've provided the tag name of each element and the text it contains (if text exists). Note that <textarea> or <input> may be textbox, but not exactly. Please focus more on the screenshot and then refer to the textual information.\n{web_text}. Please note that the label number may change in the next round, so always choose within the lastest round's number.
"""  # noqa


class WebVoyagerAgent(AgentBase):
    """
    A simple agent use screen shot browser to browse web pages.
    Referanced from the project: web voyager.
    """

    def __init__(
        self,
        browser: WebBrowser,
        model_config_name: str,
        name: str,
        sys_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_iter: int = 30,
        max_attached_imgs: int = 5,
        default_homepage: str = "https://www.google.com",
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ) -> None:
        """Initialize the dialog agent.

        Arguments:
            name (`str`):
                The name of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.tion.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            memory_config (`Optional[dict]`):
                The config of memory.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            use_memory=use_memory,
            memory_config=memory_config,
        )
        self.browser = browser
        self.max_iter = max_iter
        self.max_attached_imgs = max_attached_imgs
        self.default_homepage = default_homepage
        self.task_question = ""
        self.task_dir = ""
        self.task_web = ""
        self.task_answer = ""

    def _clip_message_and_obs(self, msg_list: list) -> list:
        """
        Avoid to much image contents so the model won't confuse.
        """
        max_img_num = self.max_attached_imgs
        clipped_msg = []
        img_num = 0
        for idx in range(len(msg_list)):
            curr_msg = msg_list[len(msg_list) - 1 - idx]
            if curr_msg.role != "user":
                clipped_msg = [curr_msg] + clipped_msg
            else:
                if curr_msg.url is None:
                    clipped_msg = [curr_msg] + clipped_msg
                elif img_num < max_img_num:
                    img_num += 1
                    clipped_msg = [curr_msg] + clipped_msg
                else:
                    msg_omit = (
                        curr_msg.content.split("Observation:")[0].strip()
                        + "Observation: A screenshot and some texts. (Omitted in context.)"  # noqa
                    )
                    curr_msg_clip = Msg(
                        name=curr_msg.name,
                        content=msg_omit,
                        role=curr_msg.role,
                    )
                    clipped_msg = [curr_msg_clip] + clipped_msg
        return clipped_msg

    def _get_step_msg(
        self,
        it: int,
        warn_obs: str,
        image_url: str,
        web_text: str,
    ) -> Msg:
        """
        Get the step message for the current iter.
        """
        if it == 1:
            init_msg = INIT_MSG_PROMPT.format(
                task_question=self.task_question,
                task_web_url=self.task_web,
                web_text=web_text,
            )
            init_msg_format = Msg(
                name="user",
                content=init_msg,
                role="user",
                url=image_url,
            )
            return init_msg_format
        else:
            obs_text = OBS_MSG_PROMPT.format(
                warn_obs=warn_obs,
                web_text=web_text,
            )
            curr_msg = Msg(
                name="user",
                content=obs_text,
                role="user",
                url=image_url,
            )
            return curr_msg

    def reply(self, x: dict = None) -> dict:
        # pylint: disable=R0912
        # pylint: disable=R0915
        """
        Given the command, execute the browsing actions.
        Args:
            x (`dict`, defaults to `None`):
                A dictionary representing the user's input to the agent.
        Returns:
            A dictionary representing the message generated by the agent in
            response to the user's input.
        """
        # init task
        if isinstance(x.content, str):
            self.task_question = x.content
            self.task_dir = file_manager.dir_file
        else:
            self.task_question = x.content["question"]
            self.task_dir = x.content["dir"]

        # ensure directory exists
        path = self.task_dir
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory created: {path}")
        else:
            print(f"Directory already exists: {path}")

        self.task_web = self.default_homepage

        self.browser.visit_page(self.task_web)
        time.sleep(5)
        self.browser.try_click_body()

        # TODO self.browser.prevent_space()

        fail_obs = ""  # When error execute the action
        warn_obs = ""  # Type warning
        pattern = r"Thought:|Action:|Observation:"

        messages = [
            message_from_dict(
                {
                    "role": "system",
                    "content": self.sys_prompt,
                    "name": "system",
                },
            ),
        ]

        it = 0

        while it < self.max_iter:
            self.speak(f"Iter: {it}")
            it += 1
            if not fail_obs:
                try:
                    (
                        _web_eles,
                        web_eles_text,
                        screenshot_bytes,
                        web_ele_fields,
                    ) = self.browser.crawl_page(with_meta=True)
                    web_eles_text = "\n".join(web_eles_text)
                except Exception as e:
                    logger.error("Driver error when adding set-of-mark.")
                    logger.error(e)
                    break

                # get screnn shot
                img_path = os.path.join(
                    self.task_dir,
                    f"screenshot_{it}.png",
                )
                # self.speak(f"saving image to {img_path}")
                file_manager.save_image(screenshot_bytes, img_path)

                curr_msg = self._get_step_msg(
                    it,
                    warn_obs,
                    img_path,
                    web_eles_text,
                )

                messages.append(curr_msg)
            else:
                # TODO change fail obs
                curr_msg = message_from_dict(
                    {
                        "role": "user",
                        "name": "user",
                        "content": fail_obs,
                    },
                )
                messages.append(curr_msg)

            messages = self._clip_message_and_obs(messages)

            formated_messages = self.model.format(messages)
            gpt_4v_res = self.model(formated_messages).text
            self.speak(gpt_4v_res)

            messages.append(
                message_from_dict(
                    {
                        "role": "assistant",
                        "content": gpt_4v_res,
                        "name": "assistant",
                    },
                ),
            )

            # extract action info
            try:
                assert "Thought:" in gpt_4v_res and "Action:" in gpt_4v_res
            except AssertionError as e:
                logger.error(e)
                fail_obs = "Format ERROR: Both 'Thought' and 'Action' should be included in your reply."  # noqa
                continue

            # bot_thought = re.split(pattern, gpt_4v_res)[1].strip()
            bot_action = re.split(pattern, gpt_4v_res)[2].strip()
            action_key, info = self._extract_action(bot_action)

            fail_obs = ""
            warn_obs = ""
            # execute action
            try:
                # TODO how to prevent bad auto page navigation?
                # window_handle_task = driver_task.current_window_handle
                # driver_task.switch_to.window(window_handle_task)

                if action_key == "click":
                    click_ele_number = int(info[0])
                    ele_tag_name = web_ele_fields[click_ele_number]["tag_name"]
                    ele_type = web_ele_fields[click_ele_number]["type"]

                    self.browser.click(click_ele_number)

                    # TODO what to do to deal with PDF file

                    if ele_tag_name == "button" and ele_type == "submit":
                        time.sleep(10)
                    time.sleep(5)

                elif action_key == "wait":
                    time.sleep(5)

                elif action_key.startswith("type"):
                    warn_obs = ""
                    type_content = info["content"]
                    type_ele_number = int(info["number"])

                    ele_tag_name = web_ele_fields[type_ele_number]["tag_name"]
                    ele_type = web_ele_fields[type_ele_number]["type"]
                    if (ele_tag_name not in ("input", "textarea")) or (
                        ele_tag_name == "input"
                        and ele_type
                        not in ["text", "search", "password", "email", "tel"]
                    ):
                        warn_obs = f"note: The web element you're trying to type may not be a textbox, and its tag name is <{ele_tag_name}>, type is {ele_type}."  # noqa

                    self.browser.type(
                        type_ele_number,
                        type_content,
                        # submit=(action_key == "typesubmit"),
                        submit=True,
                    )

                    if "wolfram" in self.task_web:
                        time.sleep(5)

                elif action_key == "scroll":
                    scroll_ele_number = info["number"]
                    scroll_content = info["content"]

                    if scroll_ele_number == "WINDOW":
                        self.browser.scroll(direction=scroll_content)
                        time.sleep(3)
                    else:
                        # add try click body
                        self.browser.try_click_body()

                        scroll_ele_number = int(scroll_ele_number)
                        self.browser.focus_element(scroll_ele_number)
                        if scroll_content == "down":
                            self.browser.scroll_down()
                        else:
                            self.browser.scroll_up()
                        time.sleep(3)

                elif action_key == "goback":
                    self.browser.go_back()
                    time.sleep(2)

                elif action_key == "google":
                    self.browser.visit_page("https://www.google.com/")
                    time.sleep(2)

                elif action_key == "answer":
                    self.speak(info["content"])
                    self.task_answer = info["content"]
                    self.speak("finish.")
                    break

                else:
                    raise NotImplementedError
                fail_obs = ""
            except Exception as e:
                logger.error("driver error info:")
                logger.error(e)
                if "element click intercepted" not in str(e):
                    fail_obs = "The action you have chosen cannot be exected. Please double-check if you have selected the wrong Numerical Label or Action or Action format. Then provide the revised Thought and Action."  # noqa
                else:
                    fail_obs = ""
                time.sleep(2)

        # TODO save messages to trajectory
        # TODO when to close self.browser
        return Msg(name=self.name, content=self.task_answer, role="assistant")

    def _extract_action(self, text: str) -> Tuple[Any, Any]:
        """
        Extract action from responsed action text
        """
        patterns = {
            "click": r"Click \[?(\d+)\]?",
            "type": r"Type \[?(\d+)\]?[; ]+\[?(.[^\]]*)\]?",
            "scroll": r"Scroll \[?(\d+|WINDOW)\]?[; ]+\[?(up|down)\]?",
            "wait": r"^Wait",
            "goback": r"^GoBack",
            "google": r"^Google",
            "answer": r"ANSWER[; ]+\[?(.[^\]]*)\]?",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                if key in ["click", "wait", "goback", "google"]:
                    # no content
                    return key, match.groups()
                elif key in ["type", "scroll"]:
                    return key, {
                        "number": match.group(1),
                        "content": match.group(2),
                    }
                else:
                    return key, {"content": match.group(1)}
        return None, None
