# -*- coding: utf-8 -*-
"""Video composition"""
import os
import tempfile
from typing import List, Optional, Union
import cv2
import json5
from agentscope.message import Msg


def load_videos_from_string(video_files: List[Union[str, Msg]]) -> List[str]:
    """
    Load video file paths from a mixed list of strings and objects with
    'url' attribute.

    Args:
        video_files: a list that may contain strings or other objects with
        'url' attribute.

    Returns:
        A list of video file paths as strings.
    """
    videos = []
    for video in video_files:
        if isinstance(video, str):
            videos.append(video)
        else:
            url = getattr(video, "url", None)
            if isinstance(url, list) and url:
                videos.extend(url)
            elif isinstance(url, str):
                videos.append(url)
    return videos


def get_video_properties(video_path: str) -> tuple[int, int, float]:
    """
    Get properties of a video file: width, height, and frames per second.

    Args:
        video_path: path to the video file.

    Returns:
        A tuple containing width, height and fps of the video.
    """
    video_cap = cv2.VideoCapture(video_path)
    width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    video_cap.release()
    return width, height, fps


def rescale_video(
    video_path: str,
    output_path: str,
    width: Optional[int],
    height: Optional[int],
    fps: Optional[int],
) -> None:
    """
    Rescale video to given width, height, and fps.
    If width or height is None, the original dimensions will be used.
    If fps is None, the original fps will be used.

    Args:
        video_path: path to the input video file.
        output_path: path where the rescaled video will be saved.
        width: target width for the rescaled video.
        height: target height for the rescaled video.
        fps: target frames per second for the rescaled video.
    """
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (width, height))
        out.write(frame)

    cap.release()
    out.release()


def merge_videos(
    video_files: List[Union[str, Msg]] = None,
    output_path: str = None,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    target_fps: Optional[int] = None,
) -> Msg:
    """
    Concatenate multiple video files into a single video file.

    Args:
        video_files: A list of paths to the video files to be merged. Can
            also be a JSON string representing a list of video file paths.
        output_path: Path to save the merged video file.
        target_width: Target width for the merged video, or None to use the
            width of the first video.
        target_height: Target height for the merged video, or None to use the
            height of the first video.
        target_fps: Target frames per second for the merged video, or None to
            use the FPS of the first video.

    Raises:
        AssertionError: If no video files are provided.
    """
    assert len(video_files) > 0, "No video files to append"

    # If video_files is a JSON string, parse it to a list
    if video_files and isinstance(video_files, str):
        video_files = json5.loads(video_files)

        # Extract string paths for the videos
    videos = load_videos_from_string(video_files)

    # If target properties are not provided, use properties of the first video
    if not all([target_width, target_height, target_fps]):
        (
            first_video_width,
            first_video_height,
            first_video_fps,
        ) = get_video_properties(videos[0])
        target_width = target_width or first_video_width
        target_height = target_height or first_video_height
        target_fps = target_fps or first_video_fps

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_files = []

    try:
        # Rescale videos and store them in temporary files
        for index, video_file in enumerate(videos):
            temp_file = os.path.join(temp_dir, f"temp_video_{index}.mp4")
            rescale_video(
                video_file,
                temp_file,
                target_width,
                target_height,
                target_fps,
            )
            temp_files.append(temp_file)

        # Initialize VideoWriter to output the merged video
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            target_fps,
            (target_width, target_height),
        )

        # Read frames from temporary files and write them to the output video
        for temp_file in temp_files:
            video_cap = cv2.VideoCapture(temp_file)
            while video_cap.isOpened():
                ret, frame = video_cap.read()
                if ret:
                    out.write(frame)
                else:
                    break
            video_cap.release()

    finally:
        out.release()
        for temp_file in temp_files:
            os.remove(temp_file)
        os.rmdir(temp_dir)

    return Msg(
        "VideoComposition",
        role="assistant",
        content=output_path,
        url=output_path,
        echo=True,
    )
