"""
Image operate functions.

Note: Non exact division leads some error in width-and-height ratio.
"""
import re
import base64
from io import BytesIO
from PIL import Image

import typing

def get_image_bytes(image: Image, format: str = "png") -> bytes:
    """Save PIL image into bytes buffer instread of a disk file.
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()

def get_base64image(image: bytes, format: str = "png") -> str:
    """Turn image binary content into base64 encoded string, so that it can be used in image <img src="xxx" /> directly.
    """
    return """data:image/{format};base64,{data}""".format(
        format=format,
        data=base64.encodebytes(image).decode(),
        )

def parse_base64image(image: str) -> typing.Tuple[str, bytes]:
    """Parse base64 encoded image string. Returns (format, image_bytes).
    """
    header, data = image.split(",", 1)
    format = re.findall("data:image/(.*);base64", header)[0]
    return format, base64.decodebytes(data.encode("utf-8"))

def resize(src: Image, scale: float) -> Image:
    """Resize PIL image using scale. Non exact division leads some error in width-and-height ratio.
    """
    src_size = src.size
    dst_size = (int(src_size[0] * scale), int(src_size[1] * scale))
    dst = src.resize(dst_size)
    return dst

def resize_to_fixed_width(src: Image, new_width: int):
    """Keep image's width-and-height ratio, scale the image to a specified new width. Non exact division leads some error in width-and-height ratio.
    """
    width, height = src.size
    new_height = int(new_width * height / width)
    dst = src.resize((new_width, new_height))
    return dst

def resize_to_fixed_height(src: Image, new_height: int):
    """Keep image's width-and-height ratio, scale the image to a specified new height. Non exact division leads some error in width-and-height ratio.
    """
    width, height = src.size
    new_width = int(new_height * width / height)
    dst = src.resize((new_width, new_height))
    return dst
