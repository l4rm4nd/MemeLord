from django.conf import settings
from django.db import models
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            # keep it simple and deterministic – tags are reused
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def meme_upload_to(instance, filename: str) -> str:
    # user based folder – keeps things tidy
    path = f"memes/user_{instance.uploader_id}/{filename}"
    logger.debug(f"Generating upload path: {path}")
    return path


class Album(TimeStampedModel):
    """
    Optional now, but ready for 'private albums' later.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="albums",
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Media(TimeStampedModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    uploader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="media_items",
    )
    title = models.CharField(max_length=150, blank=True)
    file = models.FileField(upload_to=meme_upload_to)
    thumbnail = models.ImageField(upload_to=meme_upload_to, blank=True, null=True)
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
    )

    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_items",
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="media_items",
        blank=True,
    )

    # future proofing for private albums, etc.
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Meme #{self.pk}"
    
    def save(self, *args, **kwargs):
        """
        Override save to add logging for storage operations.
        """
        storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
        
        if self.file:
            logger.debug(f"Saving media file: {self.file.name} using storage backend: {storage_backend}")
            logger.debug(f"Storage class: {self.file.storage.__class__.__name__}")
            logger.debug(f"File size: {self.file.size} bytes")
            
            if storage_backend == 's3':
                logger.debug(f"S3 Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT SET')}")
                logger.debug(f"S3 Region: {getattr(settings, 'AWS_S3_REGION_NAME', 'NOT SET')}")
                logger.debug(f"S3 Endpoint: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'DEFAULT')}")
                logger.debug(f"AWS Location: {getattr(settings, 'AWS_LOCATION', 'NOT SET')}")
        
        super().save(*args, **kwargs)
        
        if self.file:
            logger.debug(f"Media file saved successfully: {self.file.name}")
            logger.debug(f"File URL: {self.file.url}")

    def delete(self, *args, **kwargs):
        """
        Ensure the file is removed from storage when the Media object is deleted.
        """
        storage = self.file.storage
        path = self.file.name
        
        logger.debug(f"Deleting media file: {path}")
        logger.debug(f"Storage backend: {getattr(settings, 'STORAGE_BACKEND', 'local')}")

        # First delete the DB record
        super().delete(*args, **kwargs)

        # Then delete the actual file
        if path:
            try:
                storage.delete(path)
                logger.debug(f"Successfully deleted file from storage: {path}")
            except Exception as e:
                logger.error(f"Error deleting file from storage: {path}. Error: {str(e)}")

class Comment(TimeStampedModel):
    media = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="media_comments",
    )
    text = models.TextField(max_length=2000)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.media}"
