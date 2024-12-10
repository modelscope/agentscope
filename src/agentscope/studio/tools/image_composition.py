# -*- coding: utf-8 -*-
"""Image composition"""
import textwrap

from typing import List, Optional, Union, Tuple, Sequence
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import json5

from agentscope.message import Msg
from agentscope.studio.tools.utils import is_local_file, is_url


def text_size(text: str, font: ImageFont) -> Tuple[int, int]:
    """
    Calculate the size (width and height in pixels) of the given text when
    rendered with the specified font.

    This is useful when you need to know how much space text will take up on
    an image before actually adding it to the image.

    Parameters:
    - text (str): The text string whose size is to be measured.
    - font (ImageFont.ImageFont): The font in which the text is to be rendered.

    Returns:
    - Tuple[int, int]: The width and height (in pixels) as a tuple.
    """
    im = Image.new(mode="P", size=(0, 0))

    draw = ImageDraw.Draw(im)

    left, top, right, bottom = draw.textbbox((0, 0), text=text, font=font)

    width = right - left
    height = bottom - top
    return width, height


def get_min_font_size(
    titles: Union[list[str], str],
    font_path: Optional[str],
    target_width: int,
    max_height: int,
) -> Tuple[ImageFont.FreeTypeFont, Union[float, int]]:
    """
    Determine the smallest font size that allows text of each title to fit
    within a specified width and height.

    This function iterates through a list of titles and progressively
    increases the font size from a starting value until the height of the
    rendered text exceeds the maximum allowed height. The smallest font size
    among all titles is returned along with an ImageFont instance of that size.

    Parameters:
    - titles (List[str]): A list of text strings (titles) to be measured.
    - font_path (str): The path to the font file to be used.
    - target_width (int): The maximum width available for the text.
    - max_height (int): The maximum height available for the text.

    Returns:
    - Tuple[ImageFont.ImageFont, int]: A tuple containing an ImageFont
    instance of the minimum font size and the minimum font size itself as
    an integer.
    """
    min_font_size = float("inf")
    for text in titles:
        if not text.strip():
            break
        font_size = 10  # Start with a small font size
        while True:
            try:
                font = ImageFont.truetype(
                    font_path,
                    font_size if font_path else 20,
                )
            except OSError as exc:
                raise FileNotFoundError(
                    f"Font file not found: {font_path}",
                ) from exc

            sample_width, _ = text_size(text, font=font)
            avg_char_width = sample_width / len(text)
            chars_per_line = max(1, int(target_width / avg_char_width))
            wrapped_text = textwrap.fill(text, width=chars_per_line)
            _, h = text_size(wrapped_text, font=font)
            if h > max_height:
                font_size -= 1
                break
            font_size += 1
        min_font_size = min(min_font_size, font_size)

    min_font = ImageFont.truetype(
        font_path,
        min_font_size if font_path else 20,
    )
    return min_font, min_font_size


def wrap_texts_with_font(
    titles: Union[list[str], str],
    font: ImageFont,
    target_width: int,
) -> List[str]:
    """
    Wrap a list of text strings so that each line does not exceed the
    target width when rendered with the specified font.

    Parameters:
    - titles (List[str]): A list of text strings (titles) to be wrapped.
    - font (ImageFont.ImageFont): The font in which the text will be rendered.
    - target_width (int): The maximum width each line of text should occupy.

    Returns:
    - List[str]: A list of the wrapped text strings.
    """
    wrapped_texts = []
    for text in titles:
        sample_width, _ = text_size(text, font=font)
        avg_char_width = sample_width / len(text)
        chars_per_line = max(1, int(target_width / avg_char_width))
        wrapped_text = textwrap.fill(text, width=chars_per_line)
        wrapped_texts.append(wrapped_text)
    return wrapped_texts


def load_images_from_string(string: str) -> Optional[Image.Image]:
    """
    Load an image from a given string that represents either a local file
    path or a URL.
    Parameters:
    - string (str): A string that represents either a local file path or a
    URL to an image.

    Returns:
    - Optional[Image.Image]: A PIL Image object if the image was
    successfully loaded; otherwise, None.

    """
    img = None
    try:
        if is_local_file(string):
            img = Image.open(string)
        elif is_url(string):
            response = requests.get(string)
            img = Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Failed to load image from '{string}': {e}")
    return img


def load_images_and_titles(
    image_paths: Sequence[Union[str, object]],
) -> Tuple[List[Image.Image], List[str]]:
    """
    Load images from the given paths or URLs and extract titles if available.

    Parameters:
    - image_paths (List[Union[str, object]]): A list of paths where each
    path can be a string URL or a local file path, or an object expected to
    have 'url' or 'content' attributes.

    Returns:
    - Tuple[List[Image.Image], List[str]]: A tuple containing two lists:
        - The first list contains PIL Image objects loaded from the paths.
        - The second list contains the extracted titles if available.
    """
    images = []
    msg_titles = []

    for path in image_paths:
        if isinstance(path, str):
            img = load_images_from_string(path)
            if not img:
                print(f"Invalid path: {path}")
                continue
        else:
            url = getattr(path, "url", None)
            if isinstance(url, list) and url:
                url = url[0]
            if isinstance(url, str):
                img = load_images_from_string(url)
                if not img:
                    print(f"Invalid url path: {url}")
                    continue
            else:
                title = getattr(path, "content", "")
                if title:
                    msg_titles.append(title)
                else:
                    print(f"Invalid path object: {path}")
                continue
        images.append(img)

    return images, msg_titles


# pylint: disable=R0912
def stitch_images_with_grid(
    image_paths: List[str],
    titles: Union[List[str], str] = None,
    output_path: str = None,
    row: int = 1,
    column: int = 1,
    spacing: int = 10,
    title_height: int = 100,
    font_name: Optional[str] = None,
) -> Msg:
    """
    Stitch multiple images and titles into a single image, supporting
    custom grid layouts.
    Now supports image loading from URLs.

    Parameters:
    - image_paths: List of image file paths or URLs.
    - titles: List of titles corresponding to each image.
    - output_path: File path for the output image.
    - row: Number of rows in the grid.
    - column: Number of columns in the grid.
    - spacing: The size of the gap between images.
    - title_height: The height of the title area.
    - font_name: font_name for rendering the titles. If None, the default
    font is used.
    """
    if titles and isinstance(titles, str):
        titles = json5.loads(titles)

    images, msg_titles = load_images_and_titles(image_paths)
    if msg_titles:
        titles = msg_titles

    if not titles:
        titles = [" "] * len(images)
    elif len(titles) < len(images):
        titles.extend([" "] * (len(images) - len(titles)))

    max_width = max(i.size[0] for i in images) + spacing
    max_height = max(i.size[1] for i in images) + title_height + spacing

    total_width = column * max_width
    total_height = row * max_height

    combined = Image.new("RGB", (total_width, total_height), color="white")

    font, _ = get_min_font_size(
        titles,
        font_name,
        max_width - spacing * 2,
        title_height - spacing,
    )

    wrapped_texts = wrap_texts_with_font(titles, font, max_width - spacing * 2)

    for idx, image in enumerate(images):
        row_idx = idx // column
        col_idx = idx % column
        x = col_idx * max_width
        y = row_idx * max_height + title_height + spacing * 3

        title_x = x + spacing // 2  # Add some left padding to the title
        title_y = (
            row_idx * max_height + spacing
        )  # Title starts at the top of its section

        # Create draw object
        draw = ImageDraw.Draw(combined)

        # Draw the wrapped text
        current_y = title_y
        for line in wrapped_texts[idx].split("\n"):
            draw.text((title_x, current_y), line, fill="black", font=font)
            current_y += text_size(line, font=font)[1] + spacing

        combined.paste(image, (x, y))

    if output_path:
        combined.save(output_path)
    combined.show()

    return Msg(
        name="ImageComposition",
        role="assistant",
        content=output_path,
        url=output_path,
        echo=True,
    )
