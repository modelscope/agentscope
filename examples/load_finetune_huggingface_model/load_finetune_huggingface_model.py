import agentscope
from agentscope.agents.user_agent import UserAgent
from agentscope.pipelines.functional import sequentialpipeline
from huggingface_model import Finetune_DialogAgent


def main() -> None:
    """A basic conversation demo with a custom model"""

    # Initialize AgentScope with your custom model configuration
    

    agentscope.init(
        model_configs=[
            {
                "model_type": "huggingface",
                "config_name": "my_custom_model",
                "model_id": "google/gemma-2b-it",  # Or another generative model of your choice
                # "local_model_path": # Specify your local model path
                "max_length": 128,
                "device": "cuda",

                # "data_path": "GAIR/lima", # Specify a Hugging Face data path if you wish to finetune the model from the start

                # fine_tune_config (Optional): Configuration for fine-tuning the model. This dictionary
                # can include hyperparameters and other training options that
                # will be passed to the fine-tuning method. Defaults to None.
                # "fine_tune_config":{
                # "lora_config": {"r": 20, "lora_alpha": 40},
                # "training_args": {"max_steps": 20, "logging_steps": 2}
                # }
            },
        ],
    )

    # Init agents with the custom model
    dialog_agent = Finetune_DialogAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant.",
        model_config_name="my_custom_model",  # Use your custom model config name here
    )
    
    dialog_agent.load_model(model_id = "google/gemma-2b", local_model_path = None) #load gemma-2b-it from Hugging Face
    # dialog_agent.fine_tune(data_path=  "GAIR/lima") #fine-tune loaded model with lima dataset with default hyperparameters
    
    #fine-tune loaded model with lima dataset with customized hyperparameters (`fine_tune_config` argument is optional. Defaults to None.)
    dialog_agent.fine_tune("GAIR/lima", fine_tune_config ={
    "lora_config": {"r": 24, "lora_alpha": 48},
    "training_args": {"max_steps": 30, "logging_steps": 3}
    })

    user_agent = UserAgent()

    # Start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([dialog_agent, user_agent], x)

if __name__ == "__main__":
    main()
