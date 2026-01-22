from django.urls import path, include
from . import views
import uuid
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

from . import views

app_name = "myapp"

urlpatterns = [
    path("memes/", views.meme_list, name="meme_list"),
]

# Conditionally add public feed route
if getattr(settings, 'ENABLE_PUBLIC_FEED', False):
    urlpatterns += [
        path("public/", views.public_memes, name="public_memes"),
        path("public/tags/suggest/", views.public_tag_suggestions, name="public_tag_suggestions"),
    ]

urlpatterns += [
    path("memes/upload/", views.meme_upload, name="meme_upload"),
    path("memes/random/", views.meme_random, name="meme_random"),
    path("memes/statistics/", views.meme_statistics, name="meme_statistics"),
    path("memes/<int:pk>/", views.meme_detail, name="meme_detail"),
    path("memes/<int:pk>/delete/", views.meme_delete, name="meme_delete"),
    path("memes/comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("memes/<int:pk>/title/", views.meme_update_title, name="meme_update_title"),
    path("memes/<int:pk>/tags/", views.meme_update_tags, name="meme_update_tags"),
    path("memes/tags/suggest/", views.tag_suggestions, name="tag_suggestions"),
    path("memes/<int:pk>/comments/", views.meme_comments, name="meme_comments"),
    path("memes/<int:pk>/comments/add/", views.meme_add_comment, name="meme_add_comment",),
    path('', views.meme_list, name="meme_list"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('post-logout/', views.post_logout, name='post_logout'),
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("assets/img/favicon.ico"),permanent=True,),
    ),
]

admin.site.site_header = "MemeLord"
admin.site.site_title = "MemeLord"
admin.site.index_title = "Welcome to MemeLord"
