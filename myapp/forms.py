import os
import re
from django import forms
from django.conf import settings
from .models import *


# Allowed extensions (image board)
ALLOWED_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".mp4", ".webm",
}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/webm",
}


def validate_magic_header(file, ext):
    """
    Validate file signature (magic bytes) for allowed media types.
    File pointer is preserved.
    """
    header = file.read(16)
    file.seek(0)

    # JPEG
    if ext in {".jpg", ".jpeg"}:
        return header.startswith(b"\xFF\xD8")

    # PNG
    if ext == ".png":
        return header.startswith(b"\x89PNG\r\n\x1A\n")

    # GIF
    if ext == ".gif":
        return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")

    # WebP (RIFF.....WEBP)
    if ext == ".webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"

    # MP4: box header (size) + "ftyp"
    if ext == ".mp4":
        return len(header) >= 12 and header[4:8] == b"ftyp"

    # WebM (EBML)
    if ext == ".webm":
        return header.startswith(b"\x1A\x45\xDF\xA3")

    return False


class MediaUploadForm(forms.ModelForm):
    tags_input = forms.CharField(
        max_length=200,
        required=False,
        help_text="Comma separated tags, e.g. 'funny, cat, linux'",
        label="Tags",
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "autocorrect": "off",
            "autocapitalize": "off",
            "spellcheck": "false",
            "class": "form-control",
        }),
    )

    class Meta:
        model = Media
        fields = ["title", "file", "album", "tags_input"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "album": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_file(self):
        f = self.cleaned_data["file"]
        content_type = getattr(f, "content_type", "") or ""
        ext = os.path.splitext(f.name)[1].lower()

        # 1) Validate file size
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10 * 1024 * 1024)  # Default 10MB
        if f.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            file_size_mb = f.size / (1024 * 1024)
            raise forms.ValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds the maximum allowed size of {max_size_mb:.0f} MB."
            )

        # 2) Validate extension whitelist
        if ext not in ALLOWED_EXTS:
            raise forms.ValidationError(
                f"File type not allowed. Allowed extensions: {', '.join(sorted(ALLOWED_EXTS))}"
            )

        # 3) Validate MIME whitelist
        if content_type not in ALLOWED_MIME_TYPES:
            raise forms.ValidationError(
                "Invalid or unsafe file type (blocked MIME type)."
            )

        # 4) Validate magic bytes
        if not validate_magic_header(f, ext):
            raise forms.ValidationError(
                "File signature does not match its extension. Upload rejected."
            )

        # 5) Set media type for model
        if content_type.startswith("image/"):
            self.cleaned_data["media_type"] = Media.MediaType.IMAGE
        else:
            self.cleaned_data["media_type"] = Media.MediaType.VIDEO

        return f

    # --- Tag parsing helpers ---
    def _parse_tags(self):
        raw = self.cleaned_data.get("tags_input", "") or ""
        parts = re.split(r"[,#;]", raw)
        names = [p.strip() for p in parts if p.strip()]
        return names

    # --- Save with user + tags ---
    def save(self, user, commit=True):
        media = super().save(commit=False)
        media.uploader = user
        media.media_type = self.cleaned_data["media_type"]

        if commit:
            media.save()

        # Tags
        tag_names = self._parse_tags()
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name__iexact=name,
                defaults={"name": name},
            )
            tags.append(tag)

        if commit:
            media.tags.set(tags)

        return media


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Add a comment...",
                }
            )
        }

class MediaTitleForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": "Meme title",
                }
            )
        }

class MediaTagForm(forms.Form):
    tags_input = forms.CharField(
        max_length=200,
        required=False,
        label="Tags",
        help_text="Comma separated tags, e.g. 'funny, cat, linux'",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Add tags, separated by comma",
                "autocomplete": "off",
                "autocorrect": "off",
                "autocapitalize": "off",
                "spellcheck": "false",
            }
        ),
    )

    def parse_tags(self):
        raw = self.cleaned_data.get("tags_input") or ""
        parts = re.split(r"[,#;]", raw)
        return [p.strip() for p in parts if p.strip()]