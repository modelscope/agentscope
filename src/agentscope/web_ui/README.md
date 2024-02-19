
# gradio_groupchat
A Custom Gradio component to show AgentScope in the web.

## Example usage

### Quick Running
For convince, we provide the pre-built app in wheel file, you can run the UI
in following command:
```shell
pip install gradio_groupchat-0.0.1-py3-none-any.whl
python _app.py
```
After the init and entering the UI port printed by `app.py`, e.g.,
`http://127.0.0.1:7860/`, you can choose `run.log.demo` in the top-middle
FileSelector window (it's a demo log file provide by us). Then
the dialog and system log should be shown correctly in the bottom windows.

### Customization
To customize the backend, or the frontend of the provided web UI, you can
```shell
# generate the template codes
# for network connectivity problem, try to run
# `npm config rm proxy && npm config rm https-proxy` first
gradio cc create GroupChat --template Chatbot
# replace the generated _app.py into our built-in _app.py
cp -f _app.py groupchat/demo
# debug and develop your web_ui
cd groupchat
# edit the _app.py, or other parts you want, reference link:
# https://www.gradio.app/guides/custom-components-in-five-minutes
gradio cc dev
```

If you want to release the modification, you can do
```shell
gradio cc build
pip install <path-to-whl>
python _app.py
```
