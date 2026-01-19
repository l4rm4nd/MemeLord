# myapp/signals.py

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import *
from .utils import generate_thumbnail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Media)
def create_thumbnail_for_media(sender, instance, created, **kwargs):
    """
    Automatically generate a thumbnail when a new image is uploaded.
    """
    # Only process for images, when created or when file changed
    if instance.media_type != Media.MediaType.IMAGE:
        return
    
    # Don't generate if thumbnail already exists (avoid recursion)
    if instance.thumbnail:
        return
    
    # Don't process if no file
    if not instance.file:
        return
    
    try:
        logger.info(f"Generating thumbnail for media #{instance.pk}")
        thumb_content = generate_thumbnail(instance.file)
        
        if thumb_content:
            # Save without triggering signals again
            instance.thumbnail.save(
                thumb_content.name,
                thumb_content,
                save=False
            )
            # Use update to avoid triggering post_save again
            Media.objects.filter(pk=instance.pk).update(
                thumbnail=instance.thumbnail.name
            )
            logger.info(f"Thumbnail generated successfully for media #{instance.pk}")
        else:
            logger.warning(f"Failed to generate thumbnail for media #{instance.pk}")
    
    except Exception as e:
        logger.error(f"Error in create_thumbnail_for_media for media #{instance.pk}: {e}")


@receiver(pre_delete, sender=Media)
def delete_media_thumbnails(sender, instance, **kwargs):
    """
    Delete thumbnail file when Media is deleted.
    """
    if instance.thumbnail:
        try:
            storage = instance.thumbnail.storage
            path = instance.thumbnail.name
            if path:
                storage.delete(path)
                logger.debug(f"Deleted thumbnail: {path}")
        except Exception as e:
            logger.error(f"Error deleting thumbnail: {e}")


