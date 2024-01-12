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

    prompt = json.pop("inputs")

    global model, tokenizer, device

    prompt_tokenized = tokenizer(prompt, return_tensors="pt").to(device)

    response_ids = model.generate(
        prompt_tokenized.input_ids,
        **json,
    )

    response = tokenizer.batch_decode(
        response_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    response = response.removeprefix(prompt)

    print("=" * 80)
    print(f"[PROMPT]:\n{prompt}")
    print(f"[RESPONSE]:\n{response}")
    print("=" * 80)

    return {
        "response": response,
        "n_token_response": len(response_ids[0]),
        "n_token_prompt": len(prompt_tokenized.input_ids[0]),
        "timestamp": create_timestamp(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global model, tokenizer, device

    if args.device == "auto":
        device = "cuda"
    else:
        device = args.device

    model = modelscope.AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        device_map=args.device,
    )
    tokenizer = modelscope.AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        use_fast=False,
    )

    app.run(port=args.port)
