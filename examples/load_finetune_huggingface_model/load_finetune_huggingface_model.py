import agentscope
from agentscope.agents import DialogAgent
from agentscope.agents.user_agent import UserAgent
from agentscope.pipelines.functional import sequentialpipeline
from agentscope.models.huggingface_model import HuggingFaceWrapper


def main() -> None:
    """A basic conversation demo with a custom model"""

    # Initialize AgentScope with your custom model configuration
    agentscope.init(
        model_configs=[
            {
                "model_type": "huggingface",
                "config_name": "my_custom_model",
                "model_id": "google/gemma-2b-it",  # Or another generative model of your choice
                # "local_model_path": "/home/zhan1130/agentscope/examples/conversation_basic/sft_gemma-2b-it_2024-04-04_14-22-35",
                "max_new_tokens": 128,
                "device": "cuda",
                # "data_path": "GAIR/lima",
            },
        ],
    )

    # Init agents with the custom model
    dialog_agent = DialogAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant.",
        model_config_name="my_custom_model",  # Use your custom model config name here
    )
    
    dialog_agent.load_model(model_id = "google/gemma-2b-it", local_model_path = None) #load gemma-2b-it from Hugging Face
    dialog_agent.fine_tune(data_path=  "GAIR/lima") #fine-tune loaded model with lima dataset

    user_agent = UserAgent()

    # Start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([dialog_agent, user_agent], x)

if __name__ == "__main__":
    main()
