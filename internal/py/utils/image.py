import base64
import os

def encode_image(image_path):
    """Encodes an image to a base64 string."""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
