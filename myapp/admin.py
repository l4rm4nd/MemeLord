import os
import zipfile
from io import BytesIO
from django.contrib import admin, messages
from django.core import serializers
from django.db.models import Count
from django.http import HttpResponse
from django.utils.html import format_html
from django.core.management import call_command

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
        "thumbnail",
        "title",
        "media_type",
        "uploader",
        "is_public",
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
        "is_public",
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
            "fields": ("title", "file", "media_type", "uploader", "album", "is_public")
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
    def thumbnail(self, obj):
        """Small preview in the list view."""
        if not obj.file:
            return "—"

        if obj.media_type == Media.MediaType.IMAGE:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.file.url,
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

    @admin.action(description="Download selected media as ZIP (with JSON metadata)")
    def download_media_as_zip(self, request, queryset):
        """
        Create a ZIP file containing all selected media files plus a JSON metadata file.
        Preserves the original folder structure so files can be extracted directly to MEDIA_ROOT.
        Works with all storage backends (local, S3, Azure, GCS, SFTP, Dropbox, FTP).
        """
        from django.conf import settings
        import logging
        
        logger = logging.getLogger(__name__)
        storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
        
        # Create an in-memory ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            files_added = 0
            
            # Add media files preserving their original paths
            for media in queryset:
                if not media.file:
                    continue
                
                try:
                    # Use the same path structure as stored in the database
                    # e.g., "memes/user_1/filename.jpg"
                    zip_filename = media.file.name
                    
                    # Read file content from storage (works for all backends)
                    # This opens the file from whatever storage backend is configured
                    with media.file.storage.open(media.file.name, 'rb') as file_obj:
                        file_content = file_obj.read()
                    
                    # Add file content to ZIP with original path structure
                    zip_file.writestr(zip_filename, file_content)
                    files_added += 1
                    
                    logger.debug(f"Added {zip_filename} to ZIP from {storage_backend} storage")
                    
                except Exception as e:
                    # Log error but continue with other files
                    logger.error(f"Error adding {media.title or media.id} to ZIP: {str(e)}")
                    self.message_user(
                        request,
                        f"Error adding {media.title or media.id}: {str(e)}",
                        level=messages.WARNING
                    )
            
            # Add JSON metadata
            json_data = serializers.serialize(
                'json',
                queryset,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=False,
                indent=2
            )
            zip_file.writestr('metadata.json', json_data)
        
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
        response['Content-Disposition'] = 'attachment; filename="media_backup.zip"'
        
        self.message_user(
            request,
            f"Successfully created ZIP with {files_added} file(s) and metadata.json from {storage_backend} storage.",
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