from django.views.decorators.csrf import csrf_exempt
import os, base64, io, json
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import (
    JsonResponse,
    Http404,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from .forms import *
from .models import *
import re
from django.db.models import Count
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.contrib.auth import get_user_model

User = get_user_model()

@require_GET
@csrf_exempt
def public_memes(request):
    if not getattr(settings, 'ENABLE_PUBLIC_FEED', False):
        from django.http import Http404
        raise Http404()

    qs = (
        Media.objects.filter(public_feed_enabled=True)
        .select_related("uploader", "album")
        .prefetch_related("tags")
        .annotate(comment_count=Count("comments"))
        .order_by("-created_at")
    )

    tag_slug = request.GET.get("tag") or ""
    current_tag = None
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)
        qs = qs.distinct()
        from .models import Tag
        current_tag = Tag.objects.filter(slug=tag_slug).first()

    paginator = Paginator(qs, 24)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "current_tag": current_tag,
        "public_feed": True,
    }
    return render(request, "myapp/meme_list.html", context)

@login_required
def meme_list(request):
    qs = (
        Media.objects.filter()
        .select_related("uploader", "album")
        .prefetch_related("tags")
        .annotate(comment_count=Count("comments"))
        .order_by("-created_at")
    )

    tag_slug = request.GET.get("tag") or ""
    current_tag = None
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)
        qs = qs.distinct()
        from .models import Tag  # or keep the import at top
        current_tag = Tag.objects.filter(slug=tag_slug).first()

    paginator = Paginator(qs, 24)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # Infinite scroll / AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "myapp/partials/meme_grid.html",
            {"page_obj": page_obj},
            request=request,
        )
        return JsonResponse(
            {
                "html": html,
                "has_next": page_obj.has_next(),
                "next_page_number": page_obj.next_page_number()
                if page_obj.has_next()
                else None,
            }
        )

    # Normal initial page load
    context = {
        "page_obj": page_obj,
        "current_tag": current_tag,
        "debug": settings.DEBUG,
    }
    return render(request, "myapp/meme_list.html", context)

@login_required
def meme_upload(request):
    from django.conf import settings
    enable_public = getattr(settings, 'ENABLE_PUBLIC_FEED', False)
    if request.method == "POST":
        form = MediaUploadForm(request.POST, request.FILES)
        form.fields["album"].queryset = Album.objects.filter(owner=request.user)
        if not enable_public and "is_public" in form.fields:
            form.fields.pop("is_public")
        if form.is_valid():
            media = form.save(user=request.user, commit=True)
            if not enable_public:
                media.public_feed_enabled = True  # fallback: always public if feature is off
                media.save(update_fields=["public_feed_enabled"])
            return redirect("myapp:meme_detail", pk=media.pk)
    else:
        form = MediaUploadForm()
        form.fields["album"].queryset = Album.objects.filter(owner=request.user)
        if not enable_public and "is_public" in form.fields:
            form.fields.pop("is_public")

    context = {
        "form": form,
        "enable_public": enable_public,
    }
    return render(request, "myapp/meme_upload.html", context)

@login_required
@require_POST
def meme_update_title(request, pk):
    media = get_object_or_404(Media, pk=pk)

    if not (request.user == media.uploader or request.user.is_superuser):
        return HttpResponseForbidden("You are not allowed to edit this meme.")

    form = MediaTitleForm(request.POST, instance=media)
    if form.is_valid():
        form.save()

    return redirect("myapp:meme_detail", pk=media.pk)

@login_required
def meme_detail(request, pk):
    media = get_object_or_404(
        Media.objects.select_related("uploader", "album")
        .prefetch_related("tags", "comments__author"),
        pk=pk,
    )

    if not media.public_feed_enabled:
        if not request.user.is_superuser and (
            not media.album or media.album.owner != request.user
        ):
            raise Http404("Media not found")

    # only used if some non-AJAX POST still hits meme_detail
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.media = media
            comment.author = request.user
            comment.save()
            return redirect("myapp:meme_detail", pk=media.pk)
    else:
        comment_form = CommentForm()

    title_form = MediaTitleForm(instance=media)
    tag_initial = ", ".join(tag.name for tag in media.tags.all())
    tag_form = MediaTagForm(initial={"tags_input": tag_initial})

    # comment pagination (newest first)
    comments_qs = media.comments.select_related("author").order_by("-created_at")
    cpage = request.GET.get("cpage") or 1
    comments_paginator = Paginator(comments_qs, 50)
    comments_page = comments_paginator.get_page(cpage)

    context = {
        "media": media,
        "comment_form": comment_form,
        "comments_page": comments_page,   # <── this is what the template uses
        "title_form": title_form,
        "tag_form": tag_form,
    }
    return render(request, "myapp/meme_detail.html", context)


@login_required
@require_POST
def meme_update_tags(request, pk):
    media = get_object_or_404(Media, pk=pk)

    if not (request.user == media.uploader or request.user.is_superuser):
        return HttpResponseForbidden("You are not allowed to edit tags for this meme.")

    form = MediaTagForm(request.POST)
    if form.is_valid():
        names = form.parse_tags()
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(
                name__iexact=name,
                defaults={"name": name},
            )
            tags.append(tag)
        media.tags.set(tags)

    return redirect("myapp:meme_detail", pk=media.pk)

@login_required
@require_POST
def meme_delete(request, pk):
    media = get_object_or_404(Media, pk=pk)

    if not (request.user == media.uploader or request.user.is_superuser):
        return HttpResponseForbidden("You are not allowed to delete this meme.")

    media.delete()
    return redirect("myapp:meme_list")


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if not (request.user == comment.author or request.user.is_superuser):
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    media_pk = comment.media_id
    comment.delete()
    return redirect("myapp:meme_detail", pk=media_pk)

@login_required
@require_GET
def tag_suggestions(request):
    q = (request.GET.get("q") or "").strip()

    if q:
        # Filter by search string, order by popularity then name
        tags = (
            Tag.objects.filter(name__icontains=q)
            .annotate(num_media=Count("media_items"))
            .order_by("-num_media", "name")[:10]
        )
    else:
        # No query: return most popular tags overall
        tags = (
            Tag.objects.annotate(num_media=Count("media_items"))
            .order_by("-num_media", "name")[:10]
        )

    results = [
        {"id": t.id, "name": t.name, "slug": t.slug, "count": t.num_media or 0}
        for t in tags
    ]
    return JsonResponse({"results": results})

@require_GET
def post_logout(request):
    if request.user.is_authenticated:
        return redirect('meme_list')
    else:
        return render(request, 'registration/post-logout.html')

@login_required
def meme_random(request):
    """
    Random meme feed.

    - Respects ?tag=<slug> filter (like meme_list)
    - Orders matching media randomly with order_by("?")
    - Uses same template and infinite scroll JSON shape as meme_list
    """
    page_number = request.GET.get("page") or 1
    per_page = 24  # keep in sync with meme_list

    tag_slug = request.GET.get("tag")
    current_tag = None

    qs = (
        Media.objects
        .select_related("uploader")
        .prefetch_related("tags")
        .annotate(comment_count=Count("comments"))
    )

    # Apply same tag filter logic as meme_list
    if tag_slug:
        current_tag = get_object_or_404(Tag, slug=tag_slug)
        qs = qs.filter(tags=current_tag)

    # Random order after filtering
    qs = qs.order_by("?")

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    random_mode = True

    # Infinite scroll: same JSON shape as meme_list
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "myapp/partials/meme_grid.html",
            {"page_obj": page_obj, "request": request},
        )
        return JsonResponse(
            {
                "html": html,
                "has_next": page_obj.has_next(),
                "next_page_number": page_obj.next_page_number()
                if page_obj.has_next()
                else None,
            }
        )

    return render(
        request,
        "myapp/meme_list.html",
        {
            "page_obj": page_obj,
            "current_tag": current_tag,
            "random_mode": random_mode,
        },
    )

@login_required
@require_GET
def meme_comments(request, pk):
    media = get_object_or_404(Media, pk=pk)

    cpage = request.GET.get("cpage") or 1

    comments_qs = (
        media.comments
        .select_related("author")
        .order_by("-created_at")    # <── match detail view
    )

    paginator = Paginator(comments_qs, 50)
    comments_page = paginator.get_page(cpage)

    html = render_to_string(
        "myapp/partials/comments_block.html",
        {"media": media, "comments_page": comments_page},
        request=request,
    )

    return JsonResponse({
        "html": html,
        "page": comments_page.number,
        "has_next": comments_page.has_next(),
        "next_page_number": comments_page.next_page_number()
            if comments_page.has_next() else None,
    })

@login_required
@require_POST
def meme_add_comment(request, pk):
    media = get_object_or_404(Media, pk=pk)

    form = CommentForm(request.POST)
    if not form.is_valid():
        # XHR → return errors as JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": False,
                    "errors": form.errors,
                },
                status=400,
            )
        # non-XHR fallback: just reload detail with errors (rare)
        return redirect("myapp:meme_detail", pk=pk)

    comment = form.save(commit=False)
    comment.media = media
    comment.author = request.user
    comment.save()

    # Rebuild the first comments page (newest first)
    comments_qs = media.comments.select_related("author").order_by("-created_at")
    paginator = Paginator(comments_qs, 50)
    comments_page = paginator.get_page(1)

    html = render_to_string(
        "myapp/partials/comments_block.html",
        {"comments_page": comments_page},
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "html": html,
            "count": paginator.count,
            "page": comments_page.number,
            "num_pages": paginator.num_pages,
        }
    )

@login_required
@require_GET
def meme_statistics(request):
    """
    Display comprehensive statistics about uploaded memes.
    Optimized for large datasets.
    """
    from django.db.models import Avg
    from datetime import timedelta
    
    # Total counts - single queries each
    total_memes = Media.objects.count()
    total_users = User.objects.filter(media_items__isnull=False).distinct().count()
    total_comments = Comment.objects.count()
    total_tags = Tag.objects.count()
    
    # Top uploaders (top 10)
    top_uploaders = (
        User.objects
        .annotate(meme_count=Count('media_items'))
        .filter(meme_count__gt=0)
        .order_by('-meme_count')[:10]
    )
    
    # Top commenters (top 10)
    top_commenters = (
        User.objects
        .annotate(comment_count=Count('media_comments'))
        .filter(comment_count__gt=0)
        .order_by('-comment_count')[:10]
    )
    
    # Most commented memes (top 10)
    most_commented = (
        Media.objects
        .annotate(comment_count=Count('comments'))
        .filter(comment_count__gt=0)
        .select_related('uploader')
        .order_by('-comment_count')[:10]
    )
    
    # Most tagged memes (top 10)
    most_tagged = (
        Media.objects
        .annotate(tag_count=Count('tags'))
        .filter(tag_count__gt=0)
        .select_related('uploader')
        .order_by('-tag_count')[:10]
    )
    
    # Popular tags (top 15)
    popular_tags = (
        Tag.objects
        .annotate(usage_count=Count('media_items'))
        .filter(usage_count__gt=0)
        .order_by('-usage_count')[:15]
    )
    
    # File type statistics - OPTIMIZED: use database aggregation
    # Use values() to only fetch file names, not entire objects
    file_type_stats = {}
    media_files = Media.objects.values_list('file', flat=True)
    
    for file_name in media_files:
        if file_name:
            ext = os.path.splitext(file_name)[1].lower()
            if ext:
                file_type_stats[ext] = file_type_stats.get(ext, 0) + 1
    
    # Sort by count descending
    file_type_stats = dict(sorted(file_type_stats.items(), key=lambda x: x[1], reverse=True))
    
    # Media type breakdown (image vs video)
    media_type_stats = (
        Media.objects
        .values('media_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Recent activity (last 7 days)
    last_week = timezone.now() - timedelta(days=7)
    memes_last_week = Media.objects.filter(created_at__gte=last_week).count()
    comments_last_week = Comment.objects.filter(created_at__gte=last_week).count()
    
    # Average stats - OPTIMIZED: use proper aggregation
    avg_comments_per_meme = total_comments / total_memes if total_memes > 0 else 0
    
    # Calculate average tags per meme efficiently
    avg_tags_result = Media.objects.annotate(
        tag_count=Count('tags')
    ).aggregate(
        avg_tags=Avg('tag_count')
    )
    avg_tags_per_meme = avg_tags_result['avg_tags'] or 0
    
    context = {
        'total_memes': total_memes,
        'total_users': total_users,
        'total_comments': total_comments,
        'total_tags': total_tags,
        'top_uploaders': top_uploaders,
        'top_commenters': top_commenters,
        'most_commented': most_commented,
        'most_tagged': most_tagged,
        'popular_tags': popular_tags,
        'file_type_stats': file_type_stats,
        'media_type_stats': media_type_stats,
        'memes_last_week': memes_last_week,
        'comments_last_week': comments_last_week,
        'avg_comments_per_meme': round(avg_comments_per_meme, 2),
        'avg_tags_per_meme': round(avg_tags_per_meme, 2),
    }
    
    return render(request, 'myapp/statistics.html', context)
