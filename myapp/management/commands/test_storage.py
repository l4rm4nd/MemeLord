"""
Django management command to test and debug storage backend configuration.
Usage: python manage.py test_storage
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test storage backend configuration and connectivity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Storage Backend Test ===\n'))
        
        # Display current configuration
        storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
        self.stdout.write(f"Storage Backend: {storage_backend}")
        self.stdout.write(f"Storage Class: {default_storage.__class__.__name__}")
        self.stdout.write(f"Media URL: {settings.MEDIA_URL}")
        
        if storage_backend == 's3':
            self.stdout.write(self.style.WARNING('\n--- S3 Configuration ---'))
            self.stdout.write(f"AWS_ACCESS_KEY_ID: {'SET' if settings.AWS_ACCESS_KEY_ID else 'NOT SET'}")
            self.stdout.write(f"AWS_SECRET_ACCESS_KEY: {'SET' if settings.AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
            self.stdout.write(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT SET')}")
            self.stdout.write(f"AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'NOT SET')}")
            self.stdout.write(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'DEFAULT (AWS)')}")
            self.stdout.write(f"AWS_LOCATION: {getattr(settings, 'AWS_LOCATION', 'NOT SET')}")
            self.stdout.write(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'NOT SET')}")
            self.stdout.write(f"AWS_QUERYSTRING_AUTH: {getattr(settings, 'AWS_QUERYSTRING_AUTH', 'NOT SET')}")
            self.stdout.write(f"AWS_S3_FILE_OVERWRITE: {getattr(settings, 'AWS_S3_FILE_OVERWRITE', 'NOT SET')}")
        
        elif storage_backend == 'azure':
            self.stdout.write(self.style.WARNING('\n--- Azure Configuration ---'))
            self.stdout.write(f"AZURE_ACCOUNT_NAME: {getattr(settings, 'AZURE_ACCOUNT_NAME', 'NOT SET')}")
            self.stdout.write(f"AZURE_ACCOUNT_KEY: {'SET' if getattr(settings, 'AZURE_ACCOUNT_KEY', None) else 'NOT SET'}")
            self.stdout.write(f"AZURE_CONTAINER: {getattr(settings, 'AZURE_CONTAINER', 'NOT SET')}")
        
        elif storage_backend == 'gcs':
            self.stdout.write(self.style.WARNING('\n--- GCS Configuration ---'))
            self.stdout.write(f"GS_BUCKET_NAME: {getattr(settings, 'GS_BUCKET_NAME', 'NOT SET')}")
            self.stdout.write(f"GS_PROJECT_ID: {getattr(settings, 'GS_PROJECT_ID', 'NOT SET')}")
            self.stdout.write(f"GS_CREDENTIALS: {getattr(settings, 'GS_CREDENTIALS', 'NOT SET')}")
        
        elif storage_backend == 'local':
            self.stdout.write(self.style.WARNING('\n--- Local Storage Configuration ---'))
            self.stdout.write(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Test file upload
        self.stdout.write(self.style.WARNING('\n--- Testing File Upload ---'))
        test_filename = 'test_storage_file.txt'
        test_content = b'This is a test file for storage backend verification.'
        test_path = f'memes/user_test/{test_filename}'
        
        try:
            self.stdout.write(f"Attempting to save test file: {test_path}")
            
            # Save test file
            saved_path = default_storage.save(test_path, ContentFile(test_content))
            self.stdout.write(self.style.SUCCESS(f"✓ File saved successfully: {saved_path}"))
            
            # Check if file exists
            if default_storage.exists(saved_path):
                self.stdout.write(self.style.SUCCESS(f"✓ File exists in storage"))
                
                # Get file URL
                try:
                    file_url = default_storage.url(saved_path)
                    self.stdout.write(self.style.SUCCESS(f"✓ File URL: {file_url}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠ Could not generate URL: {str(e)}"))
                
                # Get file size
                try:
                    file_size = default_storage.size(saved_path)
                    self.stdout.write(self.style.SUCCESS(f"✓ File size: {file_size} bytes"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠ Could not get file size: {str(e)}"))
                
                # Read file content
                try:
                    with default_storage.open(saved_path, 'rb') as f:
                        content = f.read()
                        if content == test_content:
                            self.stdout.write(self.style.SUCCESS(f"✓ File content verified"))
                        else:
                            self.stdout.write(self.style.ERROR(f"✗ File content mismatch!"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Could not read file: {str(e)}"))
                
                # Delete test file
                self.stdout.write(f"\nCleaning up test file...")
                #default_storage.delete(saved_path)
                #if not default_storage.exists(saved_path):
                    #self.stdout.write(self.style.SUCCESS(f"✓ Test file deleted successfully"))
                #else:
                    #self.stdout.write(self.style.ERROR(f"✗ Test file still exists after deletion"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ File was not found in storage after save!"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error during storage test: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Complete ==='))
