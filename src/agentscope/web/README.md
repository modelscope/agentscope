# Web UI

## AgentScope Web UI

A user interface for AgentScope, which is a tool for monitoring and
analyzing the communication of agents in a multi-agent application.

### Quick Start
To start a web UI, you can run the following python code:

```python
import agentscope

agentscope.web.init(
    path_save="YOUR_SAVE_PATH",
    host="YOUR_WEB_IP",         # defaults to 127.0.0.1
    port=5000                   # defaults to 5000
)
```
The argument `path_save` refers to the saving directory of your application,
which defaults to `./runs` in AgentScope.

Note when running AgentScope applications, the argument `save_log` of
`agentscope.init` function should be `True` to enable saving the logging files.
```python
import agentscope

agentscope.init(
    # ...
    save_log=True,      # defaults to True
    # ...
)
```
### A Running Example

The home page of web UI, which lists all available projects and runs in the
given saving path.

![The web UI](https://img.alicdn.com/imgextra/i3/O1CN01kpHFkn1HpeYEkn60I_!!6000000000807-0-tps-3104-1849.jpg)

By clicking a running instance, we can observe more details.

![The running details](https://img.alicdn.com/imgextra/i2/O1CN01AZtsf31MIHm4FmjjO_!!6000000001411-0-tps-3104-1849.jpg)


## AgentScope Studio

A running-time interface for AgentScope, which is a tool for monitoring
the communication of agents in a multi-agent application.

### How to Use
To start a studio, you can run the following python code:

```python
as_studio path/to/your/script.py
```
Remark: in `path/to/your/script.py`, there should be a `main` function.


### An Example (Text)

Run the following code in the root directory of this project after you setup the configs in `examples/conversation/conversation.py`:
```python
as_studio examples/conversation/conversation.py
```
The following interface will be launched at `localhost:7860`.

![](https://gw.alicdn.com/imgextra/i3/O1CN01X673v81WaHV1oCxEN_!!6000000002804-0-tps-2992-1498.jpg)

**Principle:** When calling agent's `self.speak(msg)` method, it will output `msg.content` to the frontend.

### Multimodal cases
`as_studio` also support multimodal cases, such as image, audio and video.

#### Image case
If you implement a text-to-image agent, `as_studio` will display the image as follows.
![](https://img.alicdn.com/imgextra/i4/O1CN012frtbt1EXqJO1eWh2_!!6000000000362-0-tps-3028-1524.jpg)

**Principle:** When calling agent's `self.speak(msg)` method, it will
output `msg.url` to the frontend. Here `msg.url` is a list of urls of images.

#### Audio case
If you implement an audio agent, `as_studio` will display the audio as follows.
![](https://img.alicdn.com/imgextra/i3/O1CN01c2TV4a1XMpUNniSkB_!!6000000002910-0-tps-2998-1506.jpg)

**Principle:** When calling agent's `self.speak(msg)` method, it will
output `msg.audio_path` to the frontend. Here `msg.audio_path` is a list of paths of audios.

#### Video case
If you implement a video agent, `as_studio` will display the video as follows.
![](https://img.alicdn.com/imgextra/i3/O1CN01nFGfY11amQTCpRrPe_!!6000000003372-0-tps-3018-1510.jpg)

**Principle:** When calling agent's `self.speak(msg)` method, it will
output `msg.video_path` to the frontend. Here `msg.video_path` is a list of paths of videos.


