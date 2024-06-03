from typing import Literal, Union, List
from pydantic import BaseModel

"""Request sent by AgentScope running instance, received by Flask server."""


class PushMsgToFrontEnd:
    """The AgentScope running instance sends a message to the Flask server to
    display in registered front end."""

    rule: str = "/api/messages/push"
    """The rule of the request."""

    class Request(BaseModel):
        """The request parameters."""

        run_id: str
        """The runtime instance ID."""

        name: str
        """The sender name of the message."""

        role: Literal["system", "user", "system"]
        """The role of the sender."""

        content: str
        """The content of the message."""

        url: Union[str, List[str]]
        """The url(s) in the message."""

        metadata: Union[str, dict]
        """The metadata of the message."""

        timestamp: str
        """The timestamp of the message."""

    class Response(BaseModel):
        """The response parameters."""

        status: Literal["success", "fail"]
        """The status of the request."""


class RegisterRuntimeInstance:
    """Register a running instance to the AgentScope Studio."""

    class Request(BaseModel):
        run_id: str
        """The runtime instance ID."""

        project: str
        """The name of the project that the runtime belongs to."""

        name: str
        """The name of the runtime."""

        run_dir: str
        """The directory used to save logs, files, codes, and api invocations.
        """

        timestamp: str
        """The timestamp of the runtime instance."""

    class Response(BaseModel):
        status: Literal["success", "fail"]
        """The status of the request."""


class RegisterServer(BaseModel):
    """Register a server to the AgentScope Studio."""

    class Request(BaseModel):
        server_id: str
        """The server instance ID."""

        host: str
        """The host of the server."""

        port: int
        """The port of the server."""

    class Response(BaseModel):
        status: Literal["success", "fail"]
        """The status of the request."""


"""Request sent by front end, received by Flask server."""


class GetDialogue(BaseModel):
    """Fetch the dialogue from the AgentScope Studio."""
    run_id: str
    """The runtime instance ID."""


class GetAllRuntimes(BaseModel):
    """Fetch all the running instances from the AgentScope Studio."""

    rule: str = "/api/runs/all"

    class Request(BaseModel):
        """The request parameters."""

    class Response(BaseModel):
        """The response parameters."""

        run_id: str
        """The runtime instance ID."""

        project: str
        """The name of the project that the runtime belongs to."""

        name: str
        """The name of the runtime."""

        run_dir: str
        """The directory used to save logs, files, codes, and api invocations.
        """

        timestamp: str
        """The timestamp of the runtime instance."""


class FetchLocalFileRequest(BaseModel):
    """Fetch the local file from the AgentScope Studio."""

    url: str
    """The local file url."""


class FetchCodeRequest(BaseModel):
    """Fetch the code from the AgentScope Studio."""

    run_dir: str
    """The directory used to save logs, files, codes, and api invocations."""


class FetchApiInvocationRequest(BaseModel):
    """Fetch the model invocations from the AgentScope Studio."""

    run_id: str