from agentscope.agents import DialogAgent
from agentscope.message import Msg
from typing import Any
import os

from loguru import logger
import json
ANSWER = 'Answer'
PLOTCONFIG = 'PlotConfig'
ROLECONFIG = 'RoleConfig'

ASSISTANT_PROMPT = """{}: <answer>\n{}: <plot_config>\n{}: <role_config>""".format(
    ANSWER, PLOTCONFIG, ROLECONFIG)

class ConfigParser(object):
    def __init__(self):
        self._last_answer='我还可以帮你做点什么？'
        self._last_plot_config={}
        self._last_role_config=[]

    def parse(self, llm_result: str):
        prompt = ANSWER + ':'

        if len(llm_result) >= len(prompt):
            start_pos = llm_result.find(prompt)
            end_pos = llm_result.find(f'{PLOTCONFIG}')
            if start_pos >= 0:
                if end_pos > start_pos:
                    answer = llm_result[start_pos + len(prompt):end_pos]
                else:
                    end_pos = llm_result.find(f'\n{ROLECONFIG}')
                    if end_pos > start_pos:
                        answer = llm_result[start_pos + len(prompt):end_pos]
                    else:
                        answer = llm_result[start_pos + len(prompt):]
            else:
                end_pos = llm_result.find(f'{PLOTCONFIG}')
                if end_pos >= 0:
                    answer = llm_result[:end_pos]
                else:
                    end_pos = llm_result.find(f'{ROLECONFIG}')
                    if end_pos >= 0:
                        answer = llm_result[:end_pos]
                    else:
                        answer = llm_result
        else:
            answer = ''
        
        def try_to_parse_json(text):
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError:
                return None
        maybe_json_obj = try_to_parse_json(answer)
        if maybe_json_obj:
            answer = ''
        answer.strip()
        plot_config = maybe_json_obj
        try: 
            prompt = PLOTCONFIG + ':'
            if len(llm_result) >= len(prompt):
                start_pos = llm_result.find(prompt)
                end_pos = llm_result.find(f'{ROLECONFIG}')
                if start_pos >= 0:
                    if end_pos > start_pos:
                        config_str = llm_result[start_pos + len(prompt):end_pos]
                    else:
                        end_pos = llm_result.find(f'\n{ROLECONFIG}')
                        config_str = llm_result[start_pos + len(prompt):]
                else:
                    config_str = llm_result
            else:
                config_str = ''
            plot_config = json.loads(config_str.strip())
        except Exception as e:
            logger.info('No plot config') 

        role_config=maybe_json_obj
        
        try: 
            prompt = ROLECONFIG + ':'
            config_str = llm_result[llm_result.rfind(prompt) + len(prompt):].strip()
            role_config = json.loads(config_str.strip())
        except Exception as e:
            logger.info('No role config')

        self._last_answer = answer or self._last_answer

        # 防止遇到纯[] 或者 {} 文本造成混淆
        if plot_config and isinstance(plot_config, dict):
            self._last_plot_config= plot_config
        if role_config and isinstance(role_config, list):    
            self._last_role_config= role_config

        return self._last_answer, self._last_plot_config, self._last_role_config


SYSTEM = 'You are a helpful assistant.'

PROMPT_CUSTOM = """你现在要扮演一个辅助生成悬疑猜谜解密类文字类游戏剧情类的编剧助手（GameBuilder）。\
你非常擅长构建充满幻想色彩、充满悬念的悬疑猜谜解密类文字类的游戏故事剧情，而且特别喜欢采用具有挑战性和悬念的表述文字类游戏剧情和游戏角色. \
可以利用梦境，时间蒙太奇手法，倒叙等手法或参考王家卫的风格，剧情设计可以参考《名侦探柯南》或者《深夜食堂》中的一些手法。\
你需要和用户进行对话，请求用户给出已有的部分剧情或者角色，并展开设计剧情， \
如果用户未输入剧情或角色，你需要不断地引导用户。 
游戏主要场景发生在餐厅，玩家定位是餐厅老板，他与剧情主角和配角对话挖掘线索，找到答案的过程。
注意：
玩家的扮演的是餐厅老板，不能作为剧情角色！！！玩家的扮演的是餐厅老板，不能作为剧情角色！！！玩家的扮演的是餐厅老板，不能作为剧情角色！！！

你需要和用户进行对话，明确并严格遵守用户对剧情和角色的要求, 并根据已有信息和你丰富的联想能力，\
运用逻辑推理和创新思维协助用户优化剧情，增强剧情悬念。在基础上先生成完整的剧情故事，然后基于真个故事\
尽可能填充完整的剧情配置文件和角色配置文件：

剧情配置文件为json格式：
{"plot_id": "...# 剧情编号，类型为int型数字，起始为1，用户要新建时要增加编号", \
"task": "... # 剧情的主题名称，尽量吸引人", \
"description": "... # 剧情的详细描述",\
"main_roles": "... # 剧情的主角名字，负责引出剧情， 类型是一个长度为1字符数组，起始为[]", \
"supporting_roles": "...# 剧情的配角，负责参与剧情，类型是一个字符数组，长度为3-5个配角名字，起始为[]", \
"openings": "... # 从第三方的视角基于剧情描述生成的系统用来开始剧情的引导语，要具有吸引力", \
"npc_openings": "... # 主角入场时求助的话，应当展现角色的性格特质、与剧情紧密相关。直接输出他想说的话本身，不要附加附加主角的动作或者名称", \
"opening_image": "... # 主角入场配图指令：开始于'生成一张图片，图片内容是...'，并根据NPC入场台词或剧情来详细描述。", \
"npc_quit_openings": "... # 主角退场委托的话，应当提供剧情发展的线索或结尾。直接输出主角想说的话本身，不要附加附加主角的动作或者名称", \
"done_hint": "...# 完成提示， 提出与剧情紧密相关的问题，应明确、具体并可回答, 比如通过观察这三个化身角色的行为和对话，你是否能找出真正的白骨精？", \
"done_condition": "... # 完成条件：明确的正确答案，用于核对玩家回应并决定剧情是否继续，比如化身1是真正的白骨精。", \
"user_openings_option": "... # 用户互动选项：从用户视角描述的互动对话选项，基于开场白和主角入场台词，约3-4句，采用关心或好奇的语气，起始为['有什么可以帮您的吗？']"
}

角色配置文件为json格式：
[ # 必须要包含剧情配置的主角和配角，不能有遗漏和省略，要保证可以直接使用json库被反序列化，
{"name": "...# 角色名称, \
"avatar_desc":"...# 请详细描述角色的特征，包括年龄、性别、头发的长度和颜色、面部特征、表情、装饰品（如眼镜、首饰等）以及任何其他显著的外貌特点。这些详细信息将帮助精确地生成人物的头像", 
"food_preference": "... # 角色对于食物的偏好，可以包含家乡，喜欢的口味或者美食以及忌口等", 
"background":"...#角色的年龄，性别，背景，性格，职业，特长等", 
"clues":  # 线索卡类型为列表，每个列表元素代表一条线索，每个角色至少4条线索，6条最好。 \
[ \
{"name": "... # 线索名字, 线索内容的概括，4-6个字以内", \
"content": "...# 对线索名字的展开描述，总结剧情的该角色的某条", \
"plot": "...# 线索对应的剧情编号，类型为int型数字，与剧情编号相同"} \
]

在接下来的对话中，请在每次回答时必须严格按照下面的格式, 必须先作出回复，再生成配置文件，不要回复其他任何内容：
Answer: ... # 你希望对用户说的话，包含对剧情的总结描述和询问用户对剧情要求，不要重复确认用户已经提出的要求，而应该拓展出新的角度或者方案来询问用户，尽量细节和丰富，禁止为空.
PlotConfig: ... # 生成的剧情配置文件，严格按照以上剧情配置文件json格式，并保证其内容不为空，故事中的主角和配角都要补充完整，不能任何省略。
RoleConfig: ... # 生成的角色配置文件，严格按照以上角色配置文件json格式，并保证其内容不为空，可以直接被反序列化，故事中的主角和配角都要补充完整，不能任何省略。

明白了请说“好的。”， 不要说其他的。"""

STARTER_MESSAGE = [{
    'role': 'system',
    'content': SYSTEM
}, {
    'role': 'user',
    'content': PROMPT_CUSTOM
}, {
    'role': 'assistant',
    'content': '好的.'
}]

class GameBuilder(DialogAgent):
    def __init__(
        self,
        name: str = 'assistant',
        model: str = 'post_api',
    ) -> None:
        model=os.environ.get("HTTP_LLM_MODEL") if model == "post_api" else model
        super().__init__(name=name, model=model, use_memory=True)
        self.retry_time = 3
        self.history_window = 10
        self.parser = ConfigParser()

    def build(self, content) -> dict:
        """Reply function of the agent. Processes the input data,
        generates a prompt using the current dialogue memory and system
        prompt, and invokes the language model to produce a response. The
        response is then formatted and added to the dialogue memory.

        Args:
            x (`dict`, defaults to `None`):
                A dictionary representing the user's input to the agent. This
                input is added to the dialogue memory if provided. Defaults to
                None.
        Returns:
            A dictionary representing the message generated by the agent in
            response to the user's input.
        """
        # record the input if needed
        
        msg = Msg(
            name='User',
            role='user',
            content=content
        )

        self.memory.add(msg)

        # prepare prompt
        prompt = self.engine.join(
            STARTER_MESSAGE,
            self.memory.get_memory(recent_n=self.history_window),
        )

        # call llm and generate response
        logger.info(f"prompt = {prompt}")
        try:
            response = self.model(prompt)
        except Exception as e:
            logger.error(f'call llm and generate err {e}')
            response = ''

        logger.info(f"response = {response}")
        answer, plot_config, role_config = self.parser.parse(response)

        def dump(config):
            return json.dumps(config, ensure_ascii=False)

        # 重新格式化
        new_content = ASSISTANT_PROMPT.replace('<answer>', answer).replace(
                '<plot_config>', dump(plot_config)).replace('<role_config>',
                                                   dump(role_config))
        msg = Msg(self.name, new_content)

        # logging and record the message in memory
        self.memory.add(msg)
        return answer, plot_config, role_config