import os
import sys
import io
import fitz  # type: ignore
import base64
from PIL import Image

# Config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MAX_IMAGE_SIZE

def load_and_validate_image(uploaded_file) -> dict:
    """
    Validates and loads the uploaded image file
    Supports: JPG, JPEG, PNG, WEBP
    """
    try:
        # Check file size
        file_size = len(uploaded_file.getvalue())
        if file_size > MAX_IMAGE_SIZE:
            return {
                "success": False,
                "image": None,
                "error": "File size too large. Maximum allowed size is 10MB."
            }

        # Load image
        image = Image.open(uploaded_file)

        # Convert to RGB if needed
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")

        return {
            "success": True,
            "image": image,
            "error": None,
            "width": image.width,
            "height": image.height,
            "format": image.format
        }

    except Exception as e:
        return {
            "success": False,
            "image": None,
            "error": f"Could not load image: {str(e)}"
        }


def save_temp_image(uploaded_file, patient_name: str) -> str:
    """
    Saves uploaded image temporarily for email attachment
    Returns the file path
    """
    try:
        # Create temp directory if not exists
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        # Clean patient name for filename
        clean_name = patient_name.replace(" ", "_").lower()
        file_path = os.path.join(temp_dir, f"report_{clean_name}.png")

        # Save image
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")
        image.save(file_path, "PNG")

        return file_path

    except Exception as e:
        return None


def delete_temp_image(file_path: str):
    """
    Deletes temporary image after email is sent
    Protects patient privacy
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def get_image_info(image: Image.Image) -> dict:
    """
    Returns basic information about the image
    """
    return {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format if image.format else "PNG"
    }


def extract_pdf_report(uploaded_file) -> dict:
    """
    Extracts text and the first image from an uploaded PDF report.
    """
    try:
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as buffer:
            buffer.write(uploaded_file.getvalue())

        document = fitz.open(temp_path)
        text_content = ""
        first_image_bytes = None

        for page in document:
            text_content += page.get_text()
            if first_image_bytes is None:
                images = page.get_images(full=True)
                if images:
                    xref = images[0][0]
                    base_image = document.extract_image(xref)
                    first_image_bytes = base_image["image"]

        document.close()
        uploaded_file.seek(0)

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        return {
            "success": True,
            "text": text_content,
            "image_bytes": first_image_bytes,
            "file_path": temp_path
        }
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "image_bytes": None,
            "error": f"Could not extract PDF content: {str(e)}"
        }


def resize_image_if_needed(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """
    Resizes image if it's too large for faster API processing
    Maintains aspect ratio
    """
    width, height = image.size

    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        image = image.resize((new_width, new_height), Image.LANCZOS)

    return image
