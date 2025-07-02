# -*- coding: utf-8 -*-
"""base64 utils"""
import base64
import re


def is_valid_base64_image(base64_string: str) -> bool:
    """check if it is a valid base64 image"""
    try:
        if not re.match(r"^data:image\/(jpeg|png|gif);base64,", base64_string):
            return False

        image_data = base64_string.split(",")[1]
        decoded_data = base64.b64decode(image_data)
        if len(decoded_data) > 2 * 1024 * 1024:
            return False

        return True
    except Exception:
        return False
