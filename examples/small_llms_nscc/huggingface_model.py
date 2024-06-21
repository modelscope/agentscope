# -*- coding: utf-8 -*-
"""
This module provides a HuggingFaceWrapper to manage
and operate Hugging Face Transformers models, enabling loading,
fine-tuning, and response generation.
Key features include handling model and tokenizer operations,
adapting to specialized datasets, and robust error management.
"""
from typing import Sequence, Any, Union, List, Optional, Dict
import os
from datetime import datetime
import json

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
import transformers
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from datasets import load_dataset
from loguru import logger
from dotenv import load_dotenv

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
        pretrained_model_name_or_path: Optional[str] = None,
        max_length: int = 512,
        top_p: float = 0.001,
        data_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        device: Optional[torch.device] = None,
        local_model_path: Optional[str] = None,
        local_tokenizer_path: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initializes the HuggingFaceWrapper with the given configuration.

        Arguments:
            config_name (str): Configuration name for model setup.
            pretrained_model_name_or_path (str): Identifier for
                                        the pre-trained model on
                                        Hugging Face.
            max_length (int): Maximum sequence length for the
                              model output per reply.
                              Defaults to 512.
            data_path (str, optional): Path to the dataset for
                                       fine-tuning the model.
            output_dir (str, optional): User specified path to save
                                        the fine-tuned model
                                        and its tokenizer. By default
                                        save to this example's
                                        directory if not specified.
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
        self.top_p = top_p
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        dotenv_path = os.path.join(script_dir, ".env")
        _ = load_dotenv(dotenv_path)  # read local .env file
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")

        if device is None:
            self.device_map = "auto"
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu",
            )
        else:
            self.device_map = device
            self.device = device

        self.load_model(
            pretrained_model_name_or_path,
            local_model_path=local_model_path,
            fine_tune_config=fine_tune_config,
        )

        self.load_tokenizer(
            pretrained_model_name_or_path,
            local_tokenizer_path=local_tokenizer_path,
        )

        if data_path is not None:
            self.model = self.fine_tune_training(
                self.model,
                self.tokenizer,
                data_path,
                output_dir,
                token = self.huggingface_token,
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
                outputs[0][input_ids.shape[1] :],  # noqa: E203
                skip_special_tokens=True,
                do_sample=True,
                top_p=self.top_p,
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
        pretrained_model_name_or_path: Optional[str] = None,
        local_model_path: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Load a new model for the agent from
        a local path and update the agent's model.

        Arguments:
            local_model_path (str): The file path to the model to be loaded.
            pretrained_model_name_or_path (str): An identifier for
                                                 the model on Huggingface.

        Raises:
            Exception: If the model cannot be loaded from the given
                       path or identifier.
                       Possible reasons include file not found,
                       incorrect model ID,
                       or network issues while fetching the model.
        """

        bnb_config = None
        bnb_config_default = {}

        if fine_tune_config is not None:
            if fine_tune_config.get("bnb_config") is not None:
                bnb_config_default.update(fine_tune_config["bnb_config"])
        if bnb_config_default != {}:
            bnb_config = BitsAndBytesConfig(**bnb_config_default)

        from peft import LoraConfig

        lora_config = None
        lora_config_default = {}

        if fine_tune_config is not None:
            if fine_tune_config.get("lora_config") is not None:
                lora_config_default.update(fine_tune_config["lora_config"])

        try:
            if local_model_path is None:
                self.model = AutoModelForCausalLM.from_pretrained(
                    pretrained_model_name_or_path,
                    # device_map=self.device_map,
                    torch_dtype=torch.bfloat16,
                    **(
                        {"quantization_config": bnb_config}
                        if bnb_config is not None
                        else {}
                    ),
                    token=self.huggingface_token,
                )
                if lora_config_default != {}:
                    from peft import get_peft_model
                    self.lora_config = LoraConfig(**lora_config_default)
                    self.model = get_peft_model(self.model, self.lora_config)

                info_msg = (
                    f"Successfully loaded new model "
                    f"'{pretrained_model_name_or_path}' from "
                    f"Hugging Face"
                )
                    
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    local_model_path,
                    # device_map=self.device_map,
                    torch_dtype=torch.bfloat16,
                    **(
                        {"quantization_config": bnb_config}
                        if bnb_config is not None
                        else {}
                    ),
                    local_files_only=True,
                )
                if lora_config_default != {}:
                    from peft import get_peft_model
                    self.lora_config = LoraConfig(**lora_config_default)
                    self.model = get_peft_model(self.model, self.lora_config)

                info_msg = (
                    f"Successfully loaded new model "
                    f"'{pretrained_model_name_or_path}' from "
                    f"'{local_model_path}'"
                )

            # log the successful model loading
            logger.info(info_msg)

        except Exception as e:
            # Handle exceptions during model loading,
            # such as file not found or load errors
            error_msg = (
                f"Failed to load model '{pretrained_model_name_or_path}' "
                f"from '{local_model_path}': {e}"
            )

            logger.error(error_msg)

            raise

    def load_tokenizer(
        self,
        pretrained_model_name_or_path: Optional[str] = None,
        local_tokenizer_path: Optional[str] = None,
    ) -> None:
        """
        Load the tokenizer from a local path.

        Arguments:
            local_tokenizer_path (str): The file path to the
                                        tokenizer to be loaded.
            pretrained_model_name_or_path (str): An identifier
                                                for the model on Huggingface.
            fine_tune_config (dict, optional): Configuration options for
                                               fine-tuning the model,
                                               including QLoRA and training
                                               arguments.
        Raises:
            Exception: If the tokenizer cannot be loaded from the
            given path or identifier. Possible reasons include file not found,
            incorrect model ID, or network issues while fetching the tokenizer.
        """

        try:
            if local_tokenizer_path is None:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    pretrained_model_name_or_path,
                    token = self.huggingface_token,
                )
                # log the successful tokenizer loading
                logger.info(
                    f"Successfully loaded new tokenizer for model "
                    f"'{pretrained_model_name_or_path}' from Hugging Face",
                )

            else:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    local_tokenizer_path,
                )
                # log the successful tokenizer loading
                logger.info(
                    f"Successfully loaded new tokenizer for model "
                    f"'{pretrained_model_name_or_path}'"
                    f" from '{local_tokenizer_path}'",
                )
            self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})


        except Exception as e:
            # Handle exceptions during model loading,
            # such as file not found or load errors
            error_message = (
                f"Failed to load tokenizer for model"
                f" '{pretrained_model_name_or_path}' from "
                f"'{local_tokenizer_path}': {e}"
            )
            logger.error(error_message)

            raise

    def fine_tune(
        self,
        data_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        fine_tune_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Fine-tune the agent's model using data from the specified path.

        Arguments:
            data_path (str): The file path to the training
                             data from Hugging Face.
            output_dir (str, optional): User specified path
                                       to save the fine-tuned model
                                       and its tokenizer. By default
                                       save to this example's
                                       directory if not specified.

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
                output_dir,
                token = self.huggingface_token,
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

    # def filer_sequence_lengths(
    #     self,
    #     max_input_seq_length: int,
    #     dataset_obj: List[Dict[str, List[str]]],
    # ) -> List[int]:
    #     """
    #     Identifies and returns the indices of conversation
    #       entries that exceed max_input_seq_length characters in length.

    #     Args:
    #         dataset_obj (List[Dict[str, List[str]]]): A list where
    #             each dictionary contains 'conversations',
    #             a list of two strings (question and answer).

    #     Returns:
    #         List[int]: Indices of conversations where the combined
    #         length of the question and answer exceeds
    #         max_input_seq_length characters.
    #     """
    #     # Initialize a list to store the sequence lengths
    #     sequence_lengths = []

    #     # list of indices that are too long
    #     too_long = []

    #     # Loop over the dataset and get the lengths of text sequences
    #     for idx, example in enumerate(dataset_obj):
    #         sequence_length = len(
    #             example["input"] + example["target"],
    #         )
    #         sequence_lengths.append(sequence_length)
    #         if sequence_length > max_input_seq_length:
    #             too_long.append(idx)

    #     return too_long
    
    # supposedly more efficient def filter_sequence_lengths
    def filter_sequence_lengths(
            max_input_seq_length: int,
            dataset_obj: List[Dict[str, List[str]]]
        ) -> List[int]:
        """
        Identifies and returns the indices of conversation
        entries that exceed max_input_seq_length characters in length.

        Args:
            dataset_obj (List[Dict[str, List[str]]]): A list where
                each dictionary contains 'conversations',
                a list of two strings (question and answer).

        Returns:
            List[int]: Indices of conversations where the combined
            length of the question and answer exceeds
            max_input_seq_length characters.
        """
        return [
            idx for idx, example in enumerate(dataset_obj)
            if len(example["input"] + example["target"]) > max_input_seq_length
        ]

    def formatting_prompts_func(
        self,
        example: Dict[str, List[List[str]]],
        data_path: str,
    ) -> List[str]:
        """
        Formats each conversation in the dataset for training.
        Args:
            example (Dict[str, List[List[str]]]): A dataset.

        Returns:
            List[str]: A dataset with combined field.
        """

        if 'ToolBenchPlanner' in data_path or 'ToolBenchSummarizer' in data_path:

            # for planner/summarizer data
            text = (
                example["input"]
                + "\n ### Response: "
                + example["target"]
            )
        
        if 'ToolBenchCaller' in data_path:

            # for caller data
            text = (
                example["input"]
                + "\n "
                + example["target"]
            )
        
        return {"combined_text": text}

    def fine_tune_training(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        data_path: Optional[str] = None,
        output_dir: Optional[str] = None,
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
            output_dir (str, optional): User specified path
                                       to save the fine-tuned model
                                       and its tokenizer. By default
                                       save to this example's
                                       directory if not specified.
            token (str): The authentication token for Hugging Face.
            fine_tune_config (dict, optional): Configuration options for
                                               fine-tuning the model,
                                               including QLoRA and training
                                               arguments.

        Returns:
            AutoModelForCausalLM: The fine-tuned language model.

        Raises:
            Exception: Raises an exception if the dataset
                       loading or fine-tuning process fails.

        Note:
            This method updates the model in place and also logs
            the fine-tuning process.
            It utilizes the QLoRA configuration and custom training arguments
            to adapt the pre-trained model to the specific dataset.
            The training log and trained model are saved in the same
            directory with the specific timestamp at saving time
            as part of the log/model fodler name.
        """

        dataset = load_dataset(data_path, split="train", token=token)
        print('data_path', data_path)
        print("'ToolBenchPlanner' in data_path", 'ToolBenchPlanner' in data_path)
        if 'ToolBenchPlanner' in data_path:
            def contains_summarizer(entry):
                return 'Next: conclusion' in entry['target']

            # Filter the dataset to find entries containing the word 'summarizer'
            dataset = dataset.filter(contains_summarizer)
            print('this training is for improving planner on calling summarizer.')

        # from modelscope.msdatasets import MsDataset
        # dataset =  MsDataset.load('shenweizhou/alpha-umi-toolbench-processed-json_format')
        
        # dataset = dataset.select(
        #     i for i in range(100000)
        # )
        print("len(dataset['input'])",len(dataset['input']))
        print("len(dataset['target'])",len(dataset['target']))

        def is_too_long(example, max_length):
            return len(example["input"] + example["target"]) > max_length

        # Use the filter method to exclude long sequences
        dataset_reduced = dataset.filter(lambda x: not is_too_long(x, 4000))
        # indexes_to_drop = self.filer_sequence_lengths(4000, dataset)
        # dataset_reduced = dataset.select(
        #     i for i in range(len(dataset)) if i not in set(indexes_to_drop)
        # )
        
        print("len(dataset_reduced['input'])",len(dataset_reduced['input']))
        print("len(dataset_reduced['target'])",len(dataset_reduced['target']))

        print('dataset_reduced', dataset_reduced)


        from functools import partial
        formatting_prompts_func_partial = partial(self.formatting_prompts_func, data_path=data_path)
        formatted_dataset = dataset_reduced.map(formatting_prompts_func_partial, batched=False)
        formatted_dataset = formatted_dataset.train_test_split(test_size=0.01)


        

        training_defaults = {
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 2,
            "gradient_checkpointing": False,
            "num_train_epochs": 2,
            "output_dir": "./",
            "optim": "paged_adamw_8bit",
            "logging_steps": 1,
            "learning_rate":5e-5,
            "logging_strategy":"steps",
            "logging_steps": 1,
            "save_steps":10000,
        }

        if fine_tune_config is not None:
            if fine_tune_config.get("training_args") is not None:
                training_defaults.update(fine_tune_config["training_args"])

        if output_dir is not None:
            training_defaults["output_dir"] = output_dir

        

        
        if 'ToolBenchPlanner' in data_path:
            # for planner data
            collator = DataCollatorForCompletionOnlyLM(
                instruction_template = "APIs available:",
                response_template = "### Response:",
                tokenizer=tokenizer,
            )

        if 'ToolBenchCaller' in data_path:
            # for caller data
            collator = DataCollatorForCompletionOnlyLM(
                instruction_template = "APIs available:",
                response_template = "Action:",
                tokenizer=tokenizer,
            )

        if 'ToolBenchSummarizer' in data_path:
            # for summarizer data
            collator = DataCollatorForCompletionOnlyLM(
                instruction_template = "Summarize based on conversation history:",
                response_template = "### Response:",
                tokenizer=tokenizer,
            )


        trainer_args = transformers.TrainingArguments(**training_defaults)

        trainer = SFTTrainer(
            model,
            # formatting_func=self.formatting_prompts_func,
            data_collator=collator,
            train_dataset=formatted_dataset['train'],
            eval_dataset=formatted_dataset['test'],
            **(
                {"peft_config": self.lora_config}
                if self.lora_config is not None
                else {}
            ),
            args=trainer_args,
            max_seq_length=4096,
            dataset_text_field="combined_text",
        )

        logger.info(
            "fine-tuning model",
        )

        trainer.train()

        now = datetime.now()
        time_string = now.strftime("%Y-%m-%d_%H-%M-%S")

        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)

        # Specify the filename
        log_name_temp = model.config.name_or_path.split("/")[-1]
        log_name = f"{log_name_temp}_{time_string}_log_history.json"
        log_path = os.path.join(os.path.dirname(__file__), log_name)

        # log training history
        if output_dir is not None:
            with open(
                os.path.join(output_dir, log_name),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(trainer.state.log_history, f)
        else:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(trainer.state.log_history, f)

        # save model
        model_name = (
            f"sft_{model.config.name_or_path.split('/')[-1]}_{time_string}"
        )
        if output_dir is not None:
            model_path = os.path.join(output_dir, model_name)
        else:
            model_path = os.path.join(os.path.dirname(__file__), model_name)
        trainer.save_model(model_path)

        return model
