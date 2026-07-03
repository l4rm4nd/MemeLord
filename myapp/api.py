"""
REST API for MemeLord.

Authentication: Bearer token via `Authorization: Bearer <token>` header.
"""
import datetime
import functools
import random as _random

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import APIToken, Media


def _parse_date(value: str):
    """Parse a YYYY-MM-DD string. Returns (date, None) or (None, error_response)."""
    try:
        return datetime.date.fromisoformat(value), None
    except ValueError:
        return None, JsonResponse(
            {"error": f"Invalid date '{value}'. Use YYYY-MM-DD."},
            status=400,
        )


def _api_token_required(view_func):
    """Decorator that validates the Bearer token and sets request.api_user."""
    @functools.wraps(view_func)
    @csrf_exempt
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header with Bearer token required."},
                status=401,
            )

        raw_token = auth_header[7:].strip()
        try:
            api_token = APIToken.objects.select_related("user").get(
                token=raw_token, is_active=True
            )
        except APIToken.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid or inactive API token."},
                status=401,
            )

        # Record last usage without triggering full save/signals
        APIToken.objects.filter(pk=api_token.pk).update(last_used_at=timezone.now())
        request.api_user = api_token.user
        return view_func(request, *args, **kwargs)

    return wrapper


@_api_token_required
@require_GET
def memes_list(request):
    """
    GET /api/memes/

    Query parameters:
        username    – filter by uploader username (exact, case-insensitive)
        title       – partial title search (case-insensitive)
        tag         – filter by tag slug (exact); repeat for multiple tags (AND)
        date_from   – ISO date (YYYY-MM-DD), inclusive lower bound on upload date
        date_to     – ISO date (YYYY-MM-DD), inclusive upper bound on upload date
        media_type  – "image" or "video"
        ordering    – "upload_date" | "-upload_date" (default) | "title" | "-title"
        page        – page number (default 1)
        page_size   – items per page, 1-100 (default 20)
    """
    qs = (
        Media.objects
        .select_related("uploader")
        .prefetch_related("tags", "comments__author")
    )

    # --- Filters ---

    username = request.GET.get("username", "").strip()
    if username:
        qs = qs.filter(uploader__username__iexact=username)

    title = request.GET.get("title", "").strip()
    if title:
        qs = qs.filter(title__icontains=title)

    # Support ?tag=funny&tag=cats (multiple tag filter = AND)
    tags = request.GET.getlist("tag")
    for tag_slug in tags:
        tag_slug = tag_slug.strip()
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
    if tags:
        qs = qs.distinct()

    date_from = request.GET.get("date_from", "").strip()
    if date_from:
        parsed, err = _parse_date(date_from)
        if err:
            return err
        qs = qs.filter(created_at__date__gte=parsed)

    date_to = request.GET.get("date_to", "").strip()
    if date_to:
        parsed, err = _parse_date(date_to)
        if err:
            return err
        qs = qs.filter(created_at__date__lte=parsed)

    media_type = request.GET.get("media_type", "").strip().lower()
    if media_type:
        if media_type not in ("image", "video"):
            return JsonResponse(
                {"error": "media_type must be 'image' or 'video'."},
                status=400,
            )
        qs = qs.filter(media_type=media_type)

    # --- Ordering ---
    ordering_map = {
        "upload_date": "created_at",
        "-upload_date": "-created_at",
        "title": "title",
        "-title": "-title",
    }
    ordering_param = request.GET.get("ordering", "-upload_date").strip()
    db_ordering = ordering_map.get(ordering_param, "-created_at")
    qs = qs.order_by(db_ordering)

    # --- Pagination ---
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = min(100, max(1, int(request.GET.get("page_size", 20))))
    except (ValueError, TypeError):
        page_size = 20

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = list(qs[start:end])

    # --- Serialize ---
    results = [_serialize_media(request, m) for m in items]

    # Build next/previous links
    base_url = request.build_absolute_uri(request.path)
    params = request.GET.copy()

    next_url = None
    if end < total:
        params["page"] = page + 1
        next_url = f"{base_url}?{params.urlencode()}"

    prev_url = None
    if page > 1:
        params["page"] = page - 1
        prev_url = f"{base_url}?{params.urlencode()}"

    return JsonResponse(
        {
            "count": total,
            "page": page,
            "page_size": page_size,
            "next": next_url,
            "previous": prev_url,
            "results": results,
        }
    )


def _serialize_media(request, media):
    """Return a JSON-serialisable dict for a single Media object."""
    try:
        image_url = request.build_absolute_uri(media.file.url)
    except Exception:
        image_url = None

    try:
        thumbnail_url = (
            request.build_absolute_uri(media.thumbnail.url)
            if media.thumbnail
            else None
        )
    except Exception:
        thumbnail_url = None

    return {
        "id": media.pk,
        "title": media.title,
        "tags": [t.name for t in media.tags.all()],
        "upload_date": media.created_at.isoformat(),
        "author": media.uploader.username,
        "media_type": media.media_type,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "comments": [
            {
                "author": c.author.username,
                "text": c.text,
                "date": c.created_at.isoformat(),
            }
            for c in media.comments.all()
        ],
    }


@_api_token_required
@require_GET
def memes_random(request):
    """
    GET /api/memes/random/

    Returns a single random meme the authenticated user has access to.
    Accepts the same filter parameters as /api/memes/ (except ordering,
    page, and page_size which are irrelevant here).

    Query parameters:
        username    – filter by uploader username (exact, case-insensitive)
        title       – partial title search (case-insensitive)
        tag         – filter by tag slug; repeat for AND logic
        date_from   – ISO date (YYYY-MM-DD)
        date_to     – ISO date (YYYY-MM-DD)
        media_type  – "image" or "video"
    """
    qs = (
        Media.objects
        .select_related("uploader")
        .prefetch_related("tags", "comments__author")
    )

    username = request.GET.get("username", "").strip()
    if username:
        qs = qs.filter(uploader__username__iexact=username)

    title = request.GET.get("title", "").strip()
    if title:
        qs = qs.filter(title__icontains=title)

    tags = request.GET.getlist("tag")
    for tag_slug in tags:
        tag_slug = tag_slug.strip()
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
    if tags:
        qs = qs.distinct()

    date_from = request.GET.get("date_from", "").strip()
    if date_from:
        parsed, err = _parse_date(date_from)
        if err:
            return err
        qs = qs.filter(created_at__date__gte=parsed)

    date_to = request.GET.get("date_to", "").strip()
    if date_to:
        parsed, err = _parse_date(date_to)
        if err:
            return err
        qs = qs.filter(created_at__date__lte=parsed)

    media_type = request.GET.get("media_type", "").strip().lower()
    if media_type:
        if media_type not in ("image", "video"):
            return JsonResponse(
                {"error": "media_type must be 'image' or 'video'."},
                status=400,
            )
        qs = qs.filter(media_type=media_type)

    # Pick a random ID to avoid loading the full queryset into memory
    ids = list(qs.values_list("pk", flat=True))
    if not ids:
        return JsonResponse({"error": "No memes found matching the given filters."}, status=404)

    random_pk = _random.choice(ids)
    media = (
        Media.objects
        .select_related("uploader")
        .prefetch_related("tags", "comments__author")
        .get(pk=random_pk)
    )

    return JsonResponse(_serialize_media(request, media))
