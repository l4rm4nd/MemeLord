import os
import zipfile
from io import BytesIO
from django.contrib import admin, messages
from django.core import serializers
from django.db.models import Count
from django.http import HttpResponse
from django.utils.html import format_html
from django.core.management import call_command
from django.utils import timezone

from .models import Tag, Album, Media, Comment


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "media_count", "created_at")
    search_fields = ("name", "slug")
    ordering = ("name",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_media_count=Count("media_items"))

    @admin.display(ordering="_media_count", description="Used in memes")
    def media_count(self, obj):
        return obj._media_count


class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_private", "media_count", "created_at")
    search_fields = ("title", "owner__username", "owner__email")
    list_filter = ("is_private", "created_at")
    autocomplete_fields = ("owner",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_media_count=Count("media_items"))

    @admin.display(ordering="_media_count", description="Memes in album")
    def media_count(self, obj):
        return obj._media_count


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "text", "created_at")
    readonly_fields = ("author", "created_at")
    show_change_link = False


class MediaAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "thumbnail_preview",
        "title",
        "media_type",
        "uploader",
        "public_feed_enabled",
        "album",
        "tag_list",
        "created_at",
    )
    list_select_related = ("uploader", "album")
    search_fields = (
        "title",
        "uploader__username",
        "uploader__email",
        "tags__name",
    )
    list_filter = (
        "media_type",
        "public_feed_enabled",
        "album",
        "tags",
        "created_at",
    )
    date_hierarchy = "created_at"
    filter_horizontal = ("tags",)
    readonly_fields = ("preview", "created_at", "updated_at")
    inlines = [CommentInline]
    list_per_page = 50
    actions = ["download_media_as_zip"]

    fieldsets = (
        (None, {
            "fields": ("title", "file", "media_type", "uploader", "album", "public_feed_enabled")
        }),
        ("Tags", {
            "fields": ("tags",),
        }),
        ("Preview", {
            "fields": ("preview",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("tags", "uploader", "album")

    @admin.display(description="Preview")
    def thumbnail_preview(self, obj):
        """Small preview in the list view."""
        if not obj.file:
            return "—"

        if obj.media_type == Media.MediaType.IMAGE:
            # Use thumbnail if available and has a file, otherwise use full image
            try:
                if obj.thumbnail and obj.thumbnail.name:
                    img_url = obj.thumbnail.url
                else:
                    img_url = obj.file.url
            except Exception:
                # Fallback to original file if thumbnail fails
                img_url = obj.file.url
            
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                img_url,
            )
        elif obj.media_type == Media.MediaType.VIDEO:
            return "🎥"
        return "—"

    @admin.display(description="Tags")
    def tag_list(self, obj):
        names = [t.name for t in obj.tags.all()]
        return ", ".join(names) if names else "—"

    @admin.display(description="Preview (full)")
    def preview(self, obj):
        """Bigger preview on the detail page."""
        if not obj.file:
            return "No file"
        
        # Check if file actually exists in storage
        try:
            if not obj.file.storage.exists(obj.file.name):
                return format_html(
                    '<div style="color: #dc3545; padding: 10px; border: 1px solid #dc3545; border-radius: 4px;">'
                    '⚠️ File missing from storage: {}'
                    '</div>',
                    obj.file.name
                )
        except Exception as e:
            return format_html(
                '<div style="color: #ffc107; padding: 10px; border: 1px solid #ffc107; border-radius: 4px;">'
                '⚠️ Could not verify file existence: {}'
                '</div>',
                str(e)
            )
        
        if obj.media_type == Media.MediaType.IMAGE:
            return format_html(
                '<img src="{}" style="max-width: 100%; max-height: 400px; border-radius: 6px;" />',
                obj.file.url,
            )
        elif obj.media_type == Media.MediaType.VIDEO:
            return format_html(
                '<video src="{}" controls style="max-width: 100%; max-height: 400px; border-radius: 6px;"></video>',
                obj.file.url,
            )
        return "Unsupported file type"

    @admin.action(description="Download selected media as ZIP (with all fixtures)")
    def download_media_as_zip(self, request, queryset):
        """
        Create a comprehensive backup ZIP containing media files and complete database fixtures.
        
        ## How to use:
        1. Navigate to the Media section in Django admin at `/admin/myapp/media/`
        2. Select the media items you want to backup (use "Select all" for complete backup)
        3. Choose "Download selected media as ZIP (with all fixtures)" from the Actions dropdown
        4. Click "Go"
        
        ## The downloaded ZIP contains:
        - **media/** - All media files in their original folder structure (memes/user_X/...)
        - **fixtures/** - Complete database fixtures for restore:
          - groups.json - User groups
          - users.json - User accounts (excluding passwords)
          - tags.json - All tags associated with the media
          - media.json - Media metadata and relationships
          - comments.json - All comments on the media
        - **README.md** - Detailed restore instructions with correct import order
        - **summary.json** - Backup statistics and metadata
        
        ## Restore process:
        1. Extract media files to MEDIA_ROOT
        2. Load fixtures in order: groups → users → tags → media → comments
        3. Run `python manage.py generate_thumbnails` (optional)
        
        ## Technical details:
        - Preserves original folder structure for easy restoration
        - Works with all storage backends (local, S3, Azure, GCS, SFTP, Dropbox, FTP)
        - User passwords excluded for security (must be reset after import)
        - Captures all related data: users, groups, tags, and comments
        - Maintains referential integrity through proper fixture loading order
        
        To restore:
        1. Extract media files to MEDIA_ROOT
        2. Run: python manage.py loaddata fixtures/groups.json
        3. Run: python manage.py loaddata fixtures/users.json
        4. Run: python manage.py loaddata fixtures/tags.json
        5. Run: python manage.py loaddata fixtures/media.json
        6. Run: python manage.py loaddata fixtures/comments.json
        7. Run: python manage.py generate_thumbnails (if needed)
        """
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        import logging
        import json
        
        logger = logging.getLogger(__name__)
        storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
        User = get_user_model()
        
        # Create an in-memory ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            files_added = 0
            
            # ============ STEP 1: Add media files ============
            for media in queryset:
                if not media.file:
                    continue
                
                try:
                    # Use the same path structure as stored in the database
                    # e.g., "media/memes/user_1/filename.jpg"
                    zip_filename = f"media/{media.file.name}"
                    
                    # Read file content from storage (works for all backends)
                    with media.file.storage.open(media.file.name, 'rb') as file_obj:
                        file_content = file_obj.read()
                    
                    # Add file content to ZIP with original path structure
                    zip_file.writestr(zip_filename, file_content)
                    files_added += 1
                    
                    logger.debug(f"Added {zip_filename} to ZIP from {storage_backend} storage")
                    
                except Exception as e:
                    logger.error(f"Error adding {media.title or media.id} to ZIP: {str(e)}")
                    self.message_user(
                        request,
                        f"Error adding {media.title or media.id}: {str(e)}",
                        level=messages.WARNING
                    )
            
            # ============ STEP 2: Gather all related objects ============
            
            # Collect all related users
            user_ids = set()
            # Users from media uploaders
            user_ids.update(queryset.values_list('uploader_id', flat=True))
            # Users from comment authors
            comment_author_ids = Comment.objects.filter(media__in=queryset).values_list('author_id', flat=True)
            user_ids.update(comment_author_ids)
            
            users = User.objects.filter(id__in=user_ids)
            
            # Collect all groups for these users
            group_ids = set()
            for user in users:
                group_ids.update(user.groups.values_list('id', flat=True))
            groups = Group.objects.filter(id__in=group_ids)
            
            # Collect all tags
            tag_ids = set()
            for media in queryset:
                tag_ids.update(media.tags.values_list('id', flat=True))
            tags = Tag.objects.filter(id__in=tag_ids)
            
            # Collect all comments
            comments = Comment.objects.filter(media__in=queryset)
            
            # ============ STEP 3: Serialize to JSON fixtures ============
            # Order: groups -> users -> tags -> media -> comments
            
            # Serialize groups (no dependencies)
            groups_data = serializers.serialize(
                'json',
                groups,
                indent=2
            )
            zip_file.writestr('fixtures/groups.json', groups_data)
            
            # Serialize users (depends on groups for M2M relationship)
            users_data = serializers.serialize(
                'json',
                users,
                indent=2,
                fields=('username', 'email', 'first_name', 'last_name', 
                       'is_staff', 'is_active', 'date_joined', 'groups')
            )
            zip_file.writestr('fixtures/users.json', users_data)
            
            # Serialize tags (no dependencies)
            tags_data = serializers.serialize(
                'json',
                tags,
                indent=2
            )
            zip_file.writestr('fixtures/tags.json', tags_data)
            
            # Serialize media (depends on users)
            media_data = serializers.serialize(
                'json',
                queryset,
                indent=2
            )
            zip_file.writestr('fixtures/media.json', media_data)
            
            # Serialize comments (depends on media and users)
            comments_data = serializers.serialize(
                'json',
                comments,
                indent=2
            )
            zip_file.writestr('fixtures/comments.json', comments_data)
            
            # ============ STEP 4: Create README ============
            readme_content = f"""# MemeLoard Backup Archive
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
Storage Backend: {storage_backend}

## Contents
- {files_added} media file(s) in media/ directory
- {users.count()} user(s)
- {groups.count()} group(s)
- {tags.count()} tag(s)
- {queryset.count()} media record(s)
- {comments.count()} comment(s)

## Restore Instructions

### 1. Extract Media Files
Extract the contents of this archive. The media files are in the `media/` directory
and should be placed in your MEDIA_ROOT directory.

```bash
# Example: Extract to your Django project
unzip media_backup.zip
cp -r media/* /path/to/your/project/media/
```

### 2. Load Fixtures (in order)
IMPORTANT: Load fixtures in the correct order to respect foreign key dependencies.

```bash
# Navigate to your Django project directory
cd /path/to/your/project

# Load in this specific order (order matters!):
python manage.py loaddata fixtures/groups.json       # 1. No dependencies
python manage.py loaddata fixtures/users.json        # 2. Depends on groups (M2M)
python manage.py loaddata fixtures/tags.json         # 3. No dependencies
python manage.py loaddata fixtures/media.json        # 4. Depends on users (uploader FK)
python manage.py loaddata fixtures/comments.json     # 5. Depends on media & users (FKs)
```

### 3. Generate Thumbnails (optional)
If thumbnails were not included or need regeneration:

```bash
python manage.py generate_thumbnails
```

## Notes
- User passwords are NOT included in this backup for security reasons
- You may need to reset passwords: `python manage.py changepassword <username>`
- Ensure your storage backend settings match the original configuration
- Check file permissions after extraction

## Troubleshooting

### Foreign Key Errors
If you get foreign key constraint errors during import:
1. Make sure you load fixtures in the exact order specified above
2. Check that your database is empty or doesn't have conflicting IDs
3. Consider using `--ignorenonexistent` flag if some models don't exist

### Missing Files
If media files are missing after import:
1. Verify MEDIA_ROOT setting matches extraction location
2. Check file permissions (should be readable by web server)
3. Verify storage backend configuration

### Duplicate Key Errors
If importing into existing database with overlapping IDs:
1. Consider using natural keys instead
2. Or clear existing data first (CAUTION: data loss)
3. Or manually adjust fixture IDs
"""
            zip_file.writestr('README.md', readme_content)
            
            # ============ STEP 5: Create summary JSON ============
            summary = {
                'export_date': timezone.now().isoformat(),
                'storage_backend': storage_backend,
                'statistics': {
                    'media_files': files_added,
                    'users': users.count(),
                    'groups': groups.count(),
                    'tags': tags.count(),
                    'media_records': queryset.count(),
                    'comments': comments.count(),
                },
                'user_list': list(users.values_list('username', flat=True)),
                'tag_list': list(tags.values_list('name', flat=True)),
            }
            zip_file.writestr('summary.json', json.dumps(summary, indent=2))
        
        if files_added == 0:
            self.message_user(
                request,
                "No media files were found to download.",
                level=messages.WARNING
            )
            return
        
        # Prepare the response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="memeloard_backup.zip"'
        
        self.message_user(
            request,
            f"Successfully created comprehensive backup with {files_added} media file(s), "
            f"{users.count()} user(s), {tags.count()} tag(s), "
            f"and {comments.count()} comment(s) from {storage_backend} storage.",
            level=messages.SUCCESS
        )
        
        return response

    @admin.action(description="Export selected media as JSON only")
    def export_as_json(self, request, queryset):
        """
        Export selected media objects as JSON (dumpdata format) - standalone option.
        """
        # Serialize the queryset
        data = serializers.serialize(
            'json',
            queryset,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
            indent=2
        )
        
        # Create the response
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="media_export.json"'
        
        self.message_user(
            request,
            f"Successfully exported {queryset.count()} media object(s) as JSON.",
            level=messages.SUCCESS
        )
        
        return response

    @admin.action(description="Export selected media as JSON")
    def export_as_json(self, request, queryset):
        """
        Export selected media objects as JSON (dumpdata format).
        """
        # Serialize the queryset
        data = serializers.serialize(
            'json',
            queryset,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
            indent=2
        )
        
        # Create the response
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="media_export.json"'
        
        self.message_user(
            request,
            f"Successfully exported {queryset.count()} media object(s) as JSON.",
            level=messages.SUCCESS
        )
        
        return response


class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "media", "author", "created_at")
    search_fields = ("text", "author__username", "author__email", "media__title")
    list_filter = ("created_at", "author")
    date_hierarchy = "created_at"
    autocomplete_fields = ("media", "author")
    list_per_page = 50

    @admin.display(description="Comment")
    def short_text(self, obj):
        if len(obj.text) > 60:
            return obj.text[:57] + "..."
        return obj.text


admin.site.register(Tag, TagAdmin)
#admin.site.register(Album, AlbumAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(Comment, CommentAdmin)