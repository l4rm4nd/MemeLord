from django.core.management.base import BaseCommand
from myapp.models import Media
from myapp.utils import generate_thumbnail
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate thumbnails for existing media items that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of images to process in each batch (default: 100)',
        )

    def handle(self, *args, **options):
        force = options['force']
        batch_size = options['batch_size']
        
        # Always get all images - we'll check file existence in the loop
        # This ensures we catch images with DB references but missing files
        media_queryset = Media.objects.filter(media_type=Media.MediaType.IMAGE)
        
        total_count = media_queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No images found in database.'))
            return
        
        if force:
            self.stdout.write(f'Regenerating thumbnails for {total_count} images...')
        else:
            self.stdout.write(f'Checking {total_count} images and generating missing thumbnails...')
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        start_time = time.time()
        
        # Use iterator() to avoid loading all objects into memory at once
        # Process in batches to show progress
        media_items = media_queryset.iterator(chunk_size=batch_size)
        
        for idx, media in enumerate(media_items, 1):
            try:
                if not media.file:
                    skipped_count += 1
                    if idx % batch_size == 0 or idx == total_count:
                        self.stdout.write(f'Progress: {idx}/{total_count} ({idx*100//total_count}%) - Skipped media #{media.pk}: No file')
                    continue
                
                # Check if the original file actually exists in storage
                try:
                    if not media.file.storage.exists(media.file.name):
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠ Skipped media #{media.pk}: Original file missing from storage: {media.file.name}'
                            )
                        )
                        continue
                except Exception as e:
                    skipped_count += 1
                    logger.warning(f"Could not check original file existence for media #{media.pk}: {e}")
                    continue
                
                # Skip if thumbnail exists in database AND file exists in storage (unless forcing)
                if not force:
                    # First check if DB field is empty
                    if not media.thumbnail:
                        # No thumbnail reference - needs generation
                        pass
                    else:
                        # DB reference exists - check if file actually exists
                        try:
                            if media.thumbnail.storage.exists(media.thumbnail.name):
                                # Both DB reference and file exist - skip
                                skipped_count += 1
                                continue
                            else:
                                # Thumbnail reference exists but file is missing - regenerate
                                logger.info(f"Thumbnail file missing for media #{media.pk}, regenerating...")
                        except Exception as e:
                            logger.warning(f"Could not check thumbnail existence for media #{media.pk}: {e}")
                            # If we can't check, regenerate to be safe
                
                # Generate thumbnail
                thumb_content = generate_thumbnail(media.file)
                
                if thumb_content:
                    # Delete old thumbnail if forcing
                    if force and media.thumbnail:
                        try:
                            media.thumbnail.storage.delete(media.thumbnail.name)
                        except Exception as e:
                            logger.warning(f"Could not delete old thumbnail: {e}")
                    
                    # Save new thumbnail
                    media.thumbnail.save(
                        thumb_content.name,
                        thumb_content,
                        save=True
                    )
                    success_count += 1
                    
                    # Show progress every batch_size images or at the end
                    if idx % batch_size == 0 or idx == total_count:
                        elapsed = time.time() - start_time
                        rate = idx / elapsed if elapsed > 0 else 0
                        eta = (total_count - idx) / rate if rate > 0 else 0
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Progress: {idx}/{total_count} ({idx*100//total_count}%) | '
                                f'Success: {success_count} | Errors: {error_count} | '
                                f'Rate: {rate:.1f} img/s | ETA: {eta:.0f}s'
                            )
                        )
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Failed to generate thumbnail for media #{media.pk}'))
            
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Error processing media #{media.pk}: {str(e)}'))
                logger.error(f"Error generating thumbnail for media #{media.pk}: {e}", exc_info=True)
        
        # Final summary
        elapsed = time.time() - start_time
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Completed in {elapsed:.1f} seconds'))
        self.stdout.write(self.style.SUCCESS(f'Successfully generated: {success_count} thumbnails'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (no file): {skipped_count}'))
        self.stdout.write('='*60)
