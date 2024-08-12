# -*- coding: utf-8 -*-
"""Set up a local language model service."""
import datetime
import argparse

from flask import Flask
from flask import request

import modelscope


def create_timestamp(format_: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Get current timestamp."""
    return datetime.datetime.now().strftime(format_)


app = Flask(__name__)


@app.route("/llm/", methods=["POST"])
def get_response() -> dict:
    """Receive post request and return response"""
    json = request.get_json()

    inputs = json.pop("messages")

    global model, tokenizer

    if hasattr(tokenizer, "apply_chat_template"):
        prompt = tokenizer.apply_chat_template(
            inputs,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        prompt = ""
        for msg in inputs:
            prompt += (
                f"{msg.get('name', msg.get('role', 'system'))}: "
                f"{msg.get('content', '')}\n"
            )

    print("=" * 80)
    print(f"[PROMPT]:\n{prompt}")

    prompt_tokenized = tokenizer(prompt, return_tensors="pt").to(model.device)
    prompt_tokens_input_ids = prompt_tokenized.input_ids[0]

    response_ids = model.generate(
        prompt_tokenized.input_ids,
        **json,
    )

    new_response_ids = response_ids[:, len(prompt_tokens_input_ids) :]

    response = tokenizer.batch_decode(
        new_response_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    print(f"[RESPONSE]:\n{response}")
    print("=" * 80)

    return {
        "data": {
            "completion_tokens": len(response_ids[0]),
            "messages": {},
            "prompt_tokens": len(prompt_tokens_input_ids),
            "response": {
                "choices": [
                    {
                        "message": {
                            "content": response,
                        },
                    },
                ],
                "created": "",
                "id": create_timestamp(),
                "model": "flask_model",
                "object": "text_completion",
                "usage": {
                    "completion_tokens": len(response_ids[0]),
                    "prompt_tokens": len(prompt_tokens_input_ids),
                    "total_tokens": len(response_ids[0])
                    + len(
                        prompt_tokens_input_ids,
                    ),
                },
            },
            "total_tokens": len(response_ids[0])
            + len(
                prompt_tokens_input_ids,
            ),
            "username": "",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global model, tokenizer

    model = modelscope.AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        device_map=args.device,
    )
    tokenizer = modelscope.AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        use_fast=False,
    )

    app.run(port=args.port)
