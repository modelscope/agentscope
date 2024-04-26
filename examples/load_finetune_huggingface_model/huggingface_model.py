# -*- coding: utf-8 -*-
"""
This module provides a HuggingFaceWrapper to manage
and operate Hugging Face Transformers models, enabling loading,
fine-tuning, and response generation. It includes the
Finetune_DialogAgent class, which extends DialogAgent to
enhance fine-tuning capabilities with custom hyperparameters.
Key features include handling model and tokenizer operations,
adapting to specialized datasets, and robust error management.

Classes:
- HuggingFaceWrapper: Manages Hugging Face models and tokenizers.
- Finetune_DialogAgent: Extends DialogAgent for model fine-tuning.

"""
from typing import Sequence, Any, Union, List, Optional, Dict
import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from loguru import logger
from dotenv import load_dotenv

from agentscope.agents import DialogAgent
from agentscope.models import ModelWrapperBase, ModelResponse
from agentscope.message import MessageBase
from agentscope.utils.tools import _convert_to_str


class HuggingFaceWrapper(ModelWrapperBase):
    """Wrapper for a Hugging Face transformer model.

    This class is responsible for loading and fine-tuning
    pre-trained models from the Hugging Face library.
    """

    model_type: str = "huggingface"  # Unique identifier for this model wrapper

    def __init__(
        self,
        config_name: str,
        model_id: Optional[str] = None,
        max_length: int = 512,
        data_path: Optional[str] = None,
        device: Optional[torch.device] = None,
        local_model_path: Optional[str] = None,
        local_tokenizer_path: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initializes the HuggingFaceWrapper with the given configuration.

        Arguments:
            config_name (str): Configuration name for model setup.
            model_id (str): Identifier for the pre-trained model on
                            Hugging Face.
            max_length (int): Maximum sequence length for the
                              model output per reply.
                              Defaults to 512.
            data_path (str, optional): Path to the dataset for
                                       fine-tuning the model.
            device (torch.device, optional): Device to run the model on.
                                             Default to GPU if available.
            local_model_path (str, optional): Local file path to a
                                              pre-trained model.
            fine_tune_config (dict, optional): Configuration for
                                               fine-tuning the model.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(config_name=config_name)
        self.model = None
        self.max_length = max_length  # Set max_length as an attribute
        self.model_id = model_id
        relative_path = os.path.join(
            os.path.dirname(__file__),
            "../load_finetune_huggingface_model/.env",
        )
        dotenv_path = os.path.normpath(relative_path)
        _ = load_dotenv(dotenv_path)  # read local .env file
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")

        if device is None:
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu",
            )
        else:
            self.device = device

        self.load_model(model_id, local_model_path=local_model_path)
        self.load_tokenizer(
            model_id,
            local_tokenizer_path=local_tokenizer_path,
        )

        if data_path is not None:
            self.model = self.fine_tune_training(
                self.model,
                self.tokenizer,
                data_path,
                token=self.huggingface_token,
                fine_tune_config=fine_tune_config,
            )

    def __call__(
        self,
        inputs: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> ModelResponse:
        """Process the input data to generate a response from the model.

        This method tokenizes the input text, generates
        a response using the model,
        and then decodes the generated tokens into a string.

        Arguments:
            input (list): A list of dictionaries where each dictionary contains
                          'name', 'role' and 'content' keys
                          and their respective values.
            **kwargs: Additional keyword arguments for the
                      model's generate function.

        Returns:
            ModelResponse: An object containing the generated
                           text and raw model output.

        Raises:
            Exception: If an error occurs during text generation.
        """

        try:
            # Tokenize the input text
            concatenated_input = "\n ".join(
                [f"{d.get('role')}: {d['content']}" for d in inputs],
            )
            input_ids = self.tokenizer.encode(
                f"{concatenated_input}\n assistent: ",
                return_tensors="pt",
            )
            # Generate response using the model
            outputs = self.model.generate(
                input_ids.to(self.device),
                max_new_tokens=self.max_length,
                **kwargs,
            )
            # Decode the generated tokens to a string
            generated_text = self.tokenizer.decode(
                outputs[0][input_ids.shape[1]:],
                skip_special_tokens=True,
            )
            return ModelResponse(text=generated_text, raw=outputs)
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> List[dict]:
        """A basic strategy to format the input into the required format of
        Hugging Face models.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `List[dict]`:
                The formatted messages.
        """
        huggingface_msgs = []
        for msg in args:
            if msg is None:
                continue
            if isinstance(msg, MessageBase):
                # content shouldn't be empty string
                if msg.content == "":
                    logger.warning(
                        "The content field cannot be "
                        "empty string. To avoid error, the empty string is "
                        "replaced by a blank space automatically, but the "
                        "model may not work as expected.",
                    )
                    msg.content = " "

                huggingface_msg = {
                    "role": msg.role,
                    "content": _convert_to_str(msg.content),
                }

                # image url
                if msg.url is not None:
                    huggingface_msg["images"] = [msg.url]

                huggingface_msgs.append(huggingface_msg)
            elif isinstance(msg, list):
                huggingface_msgs.extend(self.format(*msg))
            else:
                raise TypeError(
                    f"Invalid message type: {type(msg)}, `Msg` is expected.",
                )

        return huggingface_msgs

    def load_model(
        self,
        model_id: Optional[str] = None,
        local_model_path: Optional[str] = None,
    ) -> None:
        """
        Load a new model for the agent from
        a local path and update the agent's model.

        Arguments:
            local_model_path (str): The file path to the model to be loaded.
            model_id (str): An identifier for the model on Huggingface.

        Raises:
            Exception: If the model cannot be loaded from the given
                       path or identifier.
                       Possible reasons include file not found,
                       incorrect model ID,
                       or network issues while fetching the model.
        """

        try:
            if local_model_path is None:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    token=self.huggingface_token,
                    device_map="auto",
                )
                info_msg = (
                    f"Successfully loaded new model '{model_id}' from "
                    f"Hugging Face"
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    local_model_path,
                    local_files_only=True,
                    device_map="auto",
                )
                info_msg = (
                    f"Successfully loaded new model '{model_id}' from "
                    f"'{local_model_path}'"
                )

            # log the successful model loading
            logger.info(info_msg)

        except Exception as e:
            # Handle exceptions during model loading,
            # such as file not found or load errors
            error_msg = (
                f"Failed to load model '{model_id}' "
                f"from '{local_model_path}': {e}"
            )

            logger.error(error_msg)

            raise

    def load_tokenizer(
        self,
        model_id: Optional[str] = None,
        local_tokenizer_path: Optional[str] = None,
    ) -> None:
        """
        Load the tokenizer from a local path.

        Arguments:
            local_tokenizer_path (str): The file path to the
                                        tokenizer to be loaded.
            model_id (str): An identifier for the model on Huggingface.

        Raises:
            Exception: If the tokenizer cannot be loaded from the
            given path or identifier. Possible reasons include file not found,
            incorrect model ID, or network issues while fetching the tokenizer.
        """

        try:
            if local_tokenizer_path is None:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    token=self.huggingface_token,
                )
                # log the successful tokenizer loading
                logger.info(
                    f"Successfully loaded new tokenizer for model "
                    f"'{model_id}' from Hugging Face",
                )
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    local_tokenizer_path,
                )
                # log the successful tokenizer loading
                logger.info(
                    f"Successfully loaded new tokenizer for model "
                    f"'{model_id}' from '{local_tokenizer_path}'",
                )

        except Exception as e:
            # Handle exceptions during model loading,
            # such as file not found or load errors
            error_message = (
                f"Failed to load tokenizer for model '{model_id}' from "
                f"'{local_tokenizer_path}': {e}"
            )
            logger.error(error_message)

            raise

    def fine_tune(
        self,
        data_path: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Fine-tune the agent's model using data from the specified path.

        Arguments:
            data_path (str): The file path to the training
                             data from Hugging Face.

        Raises:
            Exception: If the fine-tuning process fails. This could be
            due to issues with the data path, configuration parameters,
            or internal errors during the training process.
        """
        try:
            self.model = self.fine_tune_training(
                self.model,
                self.tokenizer,
                data_path,
                token=self.huggingface_token,
                fine_tune_config=fine_tune_config,
            )

            logger.info(
                f"Successfully fine-tuned model with data from '{data_path}'",
            )
        except Exception as e:
            logger.error(
                f"Failed to fine-tune model with data from '{data_path}': {e}",
            )
            raise

    def fine_tune_training(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        data_path: Optional[str] = None,
        token: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
    ) -> AutoModelForCausalLM:
        """
        The actual method that handles training and fine-tuning
        the model on the dataset specified by
        the data_path using a given tokenizer.

        Arguments:
            model (AutoModelForCausalLM): The pre-trained causal language model
                                          from Hugging Face's transformers.
            tokenizer (AutoTokenizer): The tokenizer corresponding to
                                       the pre-trained model.
            data_path (str): The file path or dataset identifier to load
                             the dataset from Hugging Face.
            token (str): The authentication token for Hugging Face.
            fine_tune_config (dict, optional): Configuration options for
                                               fine-tuning the model,
                                               including LoRA and training
                                               arguments.

        Returns:
            AutoModelForCausalLM: The fine-tuned language model.

        Raises:
            Exception: Raises an exception if the dataset
                       loading or fine-tuning process fails.

        Note:
            This method updates the model in place and also logs
            the fine-tuning process.
            It utilizes the LoRA configuration and custom training arguments
            to adapt the pre-trained model to the specific dataset.
            The training log and trained model are saved in the same
            directory with the specific timestamp at saving time
            as part of the log/model fodler name.
        """
        from datasets import load_dataset
        from datetime import datetime
        import json

        dataset = load_dataset(data_path, token=token)

        from peft import LoraConfig

        lora_config_default = {
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "bias": "none",
            "task_type": "CAUSAL_LM",
        }

        if fine_tune_config is not None:
            if fine_tune_config["lora_config"] is not None:
                lora_config_default.update(fine_tune_config["lora_config"])

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
            if fine_tune_config["training_args"] is not None:
                training_defaults.update(fine_tune_config["training_args"])

        from peft import get_peft_model

        lora_config = LoraConfig(**lora_config_default)
        model = get_peft_model(model, lora_config)

        from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
        import transformers

        def formatting_prompts_func(
            example: Dict[str, List[List[str]]],
        ) -> List[str]:
            output_texts = []
            for i in range(len(example["conversations"])):
                question = f"### Question: {example['conversations'][i][0]}"
                answer = f"### Answer: {example['conversations'][i][1]}"
                text = f"{question}\n {answer}"
                output_texts.append(text)
            return output_texts

        response_template = " ### Answer:"
        collator = DataCollatorForCompletionOnlyLM(
            response_template,
            tokenizer=tokenizer,
        )

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
        time_string = now.strftime("%Y-%m-%d_%H-%M-%S")

        # Specify the filename
        log_name_temp = model.config.name_or_path.split("/")[-1]
        log_name = f"{log_name_temp}_{time_string}_log_history.json"
        log_path = os.path.join(os.path.dirname(__file__), log_name)

        # log training history
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(trainer.state.log_history, f)

        # save model
        model_name = (
            f"sft_{model.config.name_or_path.split('/')[-1]}_{time_string}"
        )
        model_path = os.path.join(os.path.dirname(__file__), model_name)
        trainer.save_model(model_path)

        # save tokenizer
        tokenizer_name_temp = model.config.name_or_path.split("/")[-1]
        tokenizer_name = f"sft_{tokenizer_name_temp}_tokenizer_{time_string}"
        tokenizer_path = os.path.join(
            os.path.dirname(__file__),
            tokenizer_name,
        )
        tokenizer.save_pretrained(tokenizer_path)

        return model


class Finetune_DialogAgent(DialogAgent):
    """
    A dialog agent capable of fine-tuning its
    underlying model based on provided data.

    Inherits from DialogAgent and adds functionality for
    fine-tuning with custom hyperparameters.
    """

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        use_memory: bool = True,
        memory_config: Optional[dict] = None,
    ):
        """
        Initializes a new Finetune_DialogAgent with specified configuration.

        Arguments:
            name (str): Name of the agent.
            sys_prompt (str): System prompt or description of the agent's role.
            model_config_name (str): The configuration name for
                                     the underlying model.
            use_memory (bool, optional): Indicates whether to utilize
                                         memory features. Defaults to True.
            memory_config (dict, optional): Configuration for memory
                                            functionalities if
                                            `use_memory` is True.

        Note:
            Refer to `class DialogAgent(AgentBase)` for more information.
        """

        super().__init__(
            name,
            sys_prompt,
            model_config_name,
            use_memory,
            memory_config,
        )

    def load_model(
        self,
        model_id: Optional[str] = None,
        local_model_path: Optional[str] = None,
    ) -> None:
        """
        Load a new model into the agent.

        Arguments:
            model_id (str): The Hugging Face model ID or a custom identifier.
                            Needed if loading model from Hugging Face.
            local_model_path (str, optional): Path to a locally saved model.

        Raises:
            Exception: If the model loading process fails or if the
                       model wrapper does not support dynamic loading.
        """

        if hasattr(self.model, "load_model"):
            self.model.load_model(model_id, local_model_path)
        else:
            logger.error(
                "The model wrapper does not support dynamic model loading.",
            )

    def load_tokenizer(
        self,
        model_id: Optional[str] = None,
        local_tokenizer_path: Optional[str] = None,
    ) -> None:
        """
        Load a new tokenizer for the agent.

        Arguments:
            model_id (str): The Hugging Face model ID or a custom identifier.
                            Needed if loading tokenizer from Hugging Face.
            local_tokenizer_path (str, optional): Path to a locally saved
                                                  tokenizer.

        Raises:
            Exception: If the model tokenizer process fails or if the
                       model wrapper does not support dynamic loading.
        """

        if hasattr(self.model, "load_tokenizer"):
            self.model.load_tokenizer(model_id, local_tokenizer_path)
        else:
            logger.error("The model wrapper does not support dynamic loading.")

    def fine_tune(
        self,
        data_path: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Fine-tune the agent's underlying model.

        Arguments:
            data_path (str): The path to the training data.

        Raises:
            Exception: If fine-tuning fails or if the
                       model wrapper does not support fine-tuning.
        """

        if hasattr(self.model, "fine_tune"):
            self.model.fine_tune(data_path, fine_tune_config)
            logger.info("Fine-tuning completed successfully.")
        else:
            logger.error("The model wrapper does not support fine-tuning.")
