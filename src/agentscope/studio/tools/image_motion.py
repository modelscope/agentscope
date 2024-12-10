# -*- coding: utf-8 -*-
"""Image motion"""
import shutil
import tempfile
import urllib.request
import random
import cv2
import numpy as np
from PIL import Image
from agentscope.message import Msg
from agentscope.studio.tools.utils import is_url


def get_image_path_or_url(image_msg: Msg) -> str:
    """Get image path or url from image message"""
    if image_msg.url:
        if isinstance(image_msg.url, list):
            return image_msg.url[0]
        else:
            return image_msg.url
    elif image_msg.content:
        return image_msg.content
    else:
        raise ValueError("Image message must have content or url")


def load_image(image_path: str) -> np.ndarray:
    """Load an image from a local path or URL."""
    if is_url(image_path):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            # Download the image from the URL and save it to the temp file
            with urllib.request.urlopen(image_path) as response:
                temp.write(response.read())
            # Load the image using OpenCV
            img = cv2.imread(temp.name)
        # Delete the temp file
        shutil.rmtree(temp.name, ignore_errors=True)
    else:
        # Load the image from a local path
        img = cv2.imread(image_path)
    return img


def create_video_or_gif_from_image(
    msg: Msg,
    output_path: str,
    motion_style: str = "",
    duration: int = 5,
    fps: int = 30,
    output_format: str = "mp4",
) -> Msg:
    """
    Creates a video or GIF from a single image by applying a camera
    movement effect.

    Args:
        msg: A Msg object containing the image path or URL in its 'url'
             or 'content' attribute.
        output_path: The file path where the resulting video or GIF
             will be saved.
        motion_style: The type of camera movement to apply. Valid
            options are 'ramdom', 'left', 'right', 'zoom_in',
            and 'zoom_out'. If left empty, a random movement will be chosen.
        duration: Duration of the video/GIF in seconds.
        fps: Frames per second of the output video/GIF.
        output_format: The format of the output file. Can be either
             'mp4' for video or 'gif' for GIF animation.

    Returns:
        A Msg object containing details of the output video or GIF,
            including the path or URL.

    Raises:
        ValueError: If an unknown camera movement or output format is
            specified.
    """

    def apply_camera_move(
        frame: np.ndarray,
        move: str,
        move_amount: int,
    ) -> np.ndarray:
        """
        Applies a specified camera movement effect to an image frame.

        Args:
            frame: The image frame (as a numpy array) to which the
                camera movement effect will be applied. It should be a
                BGR image (as used by OpenCV).
            move: A string specifying the type of camera movement.
                Valid options are 'left', 'right', 'zoom_in',
                and 'zoom_out'.
            move_amount: An integer specifying the amount of movement.
                For left and right movements, this corresponds to the
                number of pixels the image will be shifted. For
                zooming, this value affects the scale factor.

        Returns:
            The modified image frame (as a numpy array) with the
                applied camera movement effect.

        Raises:
            ValueError: If an unknown camera movement is specified.
        """
        height, width, _ = frame.shape

        if move == "left":
            mat = np.float32([[1, 0, -move_amount], [0, 1, 0]])
            frame = cv2.warpAffine(
                frame,
                mat,
                (width, height),
                borderMode=cv2.BORDER_REPLICATE,
            )
        elif move == "right":
            mat = np.float32([[1, 0, move_amount], [0, 1, 0]])
            frame = cv2.warpAffine(
                frame,
                mat,
                (width, height),
                borderMode=cv2.BORDER_REPLICATE,
            )
        elif move == "zoom_out":
            center = (width // 2, height // 2)
            scale_factor = 1 - move_amount / 300
            mat = cv2.getRotationMatrix2D(center, 0, scale_factor)
            frame = cv2.warpAffine(
                frame,
                mat,
                (width, height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
        elif move == "zoom_in":
            center = (width // 2, height // 2)
            scale_factor = 1 + move_amount / 300
            mat = cv2.getRotationMatrix2D(center, 0, scale_factor)
            frame = cv2.warpAffine(
                frame,
                mat,
                (width, height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
        else:
            raise ValueError("Unknown camera move")

        return frame

    camera_moves = ["left", "right", "zoom_out", "zoom_in"]

    image_path = get_image_path_or_url(msg)
    img = load_image(image_path)
    height, width, _ = img.shape
    size = (width, height)

    frames_count = duration * fps
    if not motion_style or motion_style == "random":
        move = random.choice(camera_moves)
    else:
        move = motion_style
    frames = []

    if output_format == "mp4":
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, size)

    for i in range(frames_count):
        move_amount = int((i / frames_count) * 20)
        frame = apply_camera_move(
            frame=img.copy(),
            move=move,
            move_amount=move_amount,
        )
        if output_format == "gif":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将BGR转换为RGB
            frames.append(Image.fromarray(frame))
        else:
            out.write(frame)

    if output_format == "mp4":
        out.release()
    elif output_format == "gif":
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=1000 / fps,
            loop=0,
        )
    else:
        raise ValueError("Unknown output format")

    return Msg(
        name="ImageMotion",
        role="assistant",
        content=output_path,
        url=output_path,
        echo=True,
    )
