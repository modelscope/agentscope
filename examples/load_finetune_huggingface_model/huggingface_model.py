from transformers import AutoModelForCausalLM, AutoTokenizer
from agentscope.agents import DialogAgent

from agentscope.models import ModelWrapperBase, ModelResponse
from loguru import logger

import torch
import os
from dotenv import load_dotenv, find_dotenv

from typing import Optional

class HuggingFaceWrapper(ModelWrapperBase):
    model_type: str = "huggingface"  # Unique identifier for this model wrapper

    def __init__(self, config_name, model_id, max_length=512, data_path = None, device = None, local_model_path = None, fine_tune_config=None, **kwargs):
        super().__init__(config_name=config_name)
        self.max_length = max_length  # Set max_length as an attribute
        self.model_id = model_id
        # relative_path = os.path.join(os.path.dirname(__file__), "../../../examples/load_finetune_huggingface_model/.env")
        relative_path = os.path.join(os.path.dirname(__file__), "../load_finetune_huggingface_model/.env")
        dotenv_path = os.path.normpath(relative_path)
        _ = load_dotenv(dotenv_path) # read local .env file
        huggingface_token  = os.getenv('HUGGINGFACE_TOKEN')

        self.huggingface_token = huggingface_token
        if device == None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        try:
            if local_model_path == None:
                self.model = AutoModelForCausalLM.from_pretrained(model_id, token = huggingface_token, device_map="auto",)
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, token = huggingface_token)
                print("load new model")
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    local_model_path, local_files_only=True,
                    device_map="auto"
                )
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, token = huggingface_token)
                print("load local model")
                
            if data_path != None:
                self.model = self.fine_tune_training(self.model, self.tokenizer, data_path,  token = self.huggingface_token, fine_tune_config = fine_tune_config)
                
                
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise

    def __call__(self, input, **kwargs) -> ModelResponse:
        try:
            # Tokenize the input text
            concatenated_input  = "\n".join([f"{d.get('name', 'System')}: {d['content']}" for d in input])
            input_ids = self.tokenizer.encode(f"{concatenated_input}\nAssistent: ", return_tensors='pt')
            # Generate response using the model
            outputs = self.model.generate(input_ids.to(self.device), max_new_tokens = self.max_length, **kwargs)
            # Decode the generated tokens to a string
            generated_text = self.tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)
            
            return ModelResponse(text=generated_text, raw={'model_id': self.model_id})
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise

    def load_model(self, model_id, local_model_path = None):
        """
        Load a new model for the agent from a local path and update the agent's model.
        
        Parameters:
            local_model_path (str): The file path to the model to be loaded.
            model_id (str): An identifier for the model on Huggingface.
        """
        try:
            if local_model_path == None:
                self.model = AutoModelForCausalLM.from_pretrained(model_id, token = self.huggingface_token, device_map="auto",)
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, token = self.huggingface_token)
                print("new model")
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    local_model_path, local_files_only=True,
                    device_map="auto"
                )
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, token = self.huggingface_token)
                print("local model")
            
            
            # Optionally, log the successful model loading
            logger.info(f"Successfully loaded new model '{model_id}' from '{local_model_path}'")
        except Exception as e:
            # Handle exceptions during model loading, such as file not found or load errors
            logger.error(f"Failed to load model '{model_id}' from '{local_model_path}': {e}")
            raise  # Or handle error appropriately

    def fine_tune(self, data_path, fine_tune_config=None):
        """
        Fine-tune the agent's model using data from the specified path.
        
        Parameters:
            data_path (str): The file path to the training data.
        """
        try:
            self.model = self.fine_tune_training(self.model, self.tokenizer, data_path, token = self.huggingface_token, fine_tune_config = fine_tune_config)
            
            logger.info(f"Successfully fine-tuned model with data from '{data_path}'")
        except Exception as e:
            logger.error(f"Failed to fine-tune model with data from '{data_path}': {e}")
            raise  # Or handle the error appropriately


    def fine_tune_training(self, model, tokenizer, data_path, token, fine_tune_config=None):
        from datasets import load_dataset
        from datetime import datetime
        import os
        import json

        dataset = load_dataset(data_path, token = token)

        from peft import LoraConfig

        lora_config_default = {
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }

        if fine_tune_config is not None:
            if fine_tune_config['lora_config'] is not None:
                lora_config_default.update(fine_tune_config['lora_config'])


        training_defaults = {
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 1,
            "gradient_checkpointing": False,
            "max_steps": 10,
            "output_dir": "./",
            "optim": "paged_adamw_8bit",
            "fp16": True,
            "logging_steps": 1,
            # "learning_rate": 2e-6,
            # "num_train_epochs": 10.0,
        }

        if fine_tune_config is not None:
            if fine_tune_config['training_args'] is not None:
                training_defaults.update(fine_tune_config['training_args'])

        from peft import get_peft_model

        
        lora_config = LoraConfig(**lora_config_default)
        model = get_peft_model(model, lora_config)

        from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
        import transformers

        def formatting_prompts_func(example):
            output_texts = []
            for i in range(len(example['conversations'])):
                text = f"### Question: {example['conversations'][i][0]}\n ### Answer: {example['conversations'][i][1]}"
                output_texts.append(text)
            return output_texts

        response_template = " ### Answer:"
        collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

        trainer_args = transformers.TrainingArguments(**training_defaults)

        trainer = SFTTrainer(
            model,
            train_dataset=dataset["train"],
            eval_dataset=dataset["train"],
            formatting_func=formatting_prompts_func,
            data_collator=collator,
            peft_config=lora_config,
            args=trainer_args,
        )

        print("fine-tuning model")

        trainer.train()

        
        now = datetime.now()
        time_string = now.strftime('%Y-%m-%d_%H-%M-%S')

        # Specify the filename
        log_name = f"{model.config._name_or_path.split('/')[-1]}_{time_string}_log_history.json"

        relative_path = os.path.join(os.path.dirname(__file__), "../../../examples/load_finetune_huggingface_model/"+log_name)
        normalized_path = os.path.normpath(relative_path)

        os.makedirs(os.path.dirname(normalized_path), exist_ok=True)

        # Writing JSON data
        with open(normalized_path, 'w') as f:
            json.dump(trainer.state.log_history, f)

        save_name = f"sft_{model.config._name_or_path.split('/')[-1]}_{time_string}"
        relative_path = os.path.join(os.path.dirname(__file__), "../../../examples/load_finetune_huggingface_model/"+save_name)
        normalized_path = os.path.normpath(relative_path)

        os.makedirs(os.path.dirname(normalized_path), exist_ok=True)
        # Check if directory exists
        if not os.path.exists(normalized_path):
            # If not, create the directory
            os.makedirs(normalized_path)

        #save model
        trainer.save_model(normalized_path)
        # trainer.mode.save_config(save_path)

        
        return model


class Finetune_DialogAgent(DialogAgent):
    """
    A dialog agent capable of fine-tuning its underlying model based on provided data.

    Inherits from DialogAgent and adds functionality for fine-tuning with custom hyperparameters.

    Parameters:
        name (str): Name of the agent.
        sys_prompt (str): System prompt or description of the agent's role.
        model_config_name (str): The configuration name for the underlying model.
        use_memory (bool, optional): Whether to use memory for the agent. Defaults to True.
        memory_config (dict, Optional): Configuration for the agent's memory. Defaults to None.
    """
    def __init__(self, name: str, sys_prompt: str, model_config_name: str, use_memory: bool = True, memory_config: Optional[dict] = None):
        super().__init__(name, sys_prompt, model_config_name, use_memory, memory_config)

    def load_model(self, model_id, local_model_path=None):
        """
        Load a new model into the agent.

        Parameters:
            model_id (str): The Hugging Face model ID or a custom identifier.
            local_model_path (str, optional): Path to a locally saved model.
        """
        if hasattr(self.model, "load_model"):
            self.model.load_model(model_id, local_model_path)
        else:
            logger.error("The model wrapper does not support dynamic model loading.")

    def fine_tune(self, data_path, fine_tune_config=None):
        """
        Fine-tune the agent's underlying model.

        Parameters:
            data_path (str): The path to the training data.
        """
        if hasattr(self.model, "fine_tune"):
            self.model.fine_tune(data_path, fine_tune_config)
            logger.info("Fine-tuning completed successfully.")
        else:
            logger.error("The model wrapper does not support fine-tuning.")
