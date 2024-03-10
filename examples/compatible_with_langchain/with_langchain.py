import langchain
from langchain_openai import OpenAI

from agentscope.agents import AgentBase


class LangChainAgent(AgentBase):
    def __init__(self, name):
        # We only keep the agent name here.
        super().__init__(name, use_memory=False)

        # init model by langchain
        self.memory = langchain

    def reply(self, x):
        ### [START] By langchain

        # manage memory
        if x is not None:
            if x.name.lower() == "user":
                self.memory.add_user_messary(x.content)
            else:
                self.memory.add_ai_messary(x.content)

        # construct prompt
        prompt = langchain.PromptTemplate(
            input_variables=["dialog_history"],
            template=(
                "You're a helpful assistant.\n"
                "The following is a dialog history:\n"
                "{}\n"
                f"{self.name}: "
            )
        )

        # Obtain dialog history from memory and format the prompt by langchain

        llm_chain = langchain.LLMChain(
            prompt=prompt,
            llm=OpenAI(temperature=0.5),
            verbose=True,
            memory=self.memory
        )

        llm_chain.predict(human_input=x.content)

        ### [END] by langchain





agent = LangChainAgent("Assistant")

from agentscope.agents import UserAgent

user = UserAgent("User")

x = None
while x is None or x.content != "exit":
    x = agent(x)
    x = user(x)