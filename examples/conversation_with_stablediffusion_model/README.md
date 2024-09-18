# Conversation with Stable-diffusion model

This example will show
- How to use Stable Diffusion models in AgentScope.

In this example, you can interact in a conversational format to generate images.
Once the image is generated, the agent will respond with the local file path where the image is saved.

## Prerequisites

You need to satisfy the following requirements to run this example:

- Install Stable Diffusion Web UI by following the instructions at [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
- Launching the Stable Diffusion Web UI with arguments: --api
- Ensure that your host can successfully access `http://127.0.0.1:7860/`(default) any other specified host and port you choose.
- Install the latest version of AgentScope by
    ```bash
    git clone https://github.com/modelscope/agentscope.git
    cd agentscope
    pip install -e .
    ```

## Running the Example
Run the example and input your questions.
```bash
python conversation_with_stablediffusion_model.py
```