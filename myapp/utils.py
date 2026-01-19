import unicodedata
import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)

def generate_username(email):
    # Normalize the email
    normalized_email = unicodedata.normalize('NFKC', email)
    # Split the email to get the username part
    username_part = normalized_email.split('@')[0]
    # Slice the username to a maximum of 150 characters
    return username_part[:150]


def generate_thumbnail(file, max_size=(400, 400)):
    """
    Generate a thumbnail for an image file.
    
    Args:
        file: Django FileField/ImageField
        max_size: Tuple of (width, height) for thumbnail size
    
    Returns:
        ContentFile with thumbnail data, or None if generation fails
    """
    try:
        # Read the image
        image = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Create thumbnail
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG', quality=85, optimize=True)
        thumb_io.seek(0)
        
        # Generate filename
        original_name = os.path.basename(file.name)
        name_without_ext = os.path.splitext(original_name)[0]
        thumb_filename = f"{name_without_ext}_thumb.jpg"
        
        return ContentFile(thumb_io.read(), name=thumb_filename)
    
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None