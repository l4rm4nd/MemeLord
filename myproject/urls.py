from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from myapp import views as myapp_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", myapp_views.smart_login, name="login"),
    path("", include("myapp.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]

# Conditionally include OIDC URLs if OIDC_ENABLED is False
if not settings.OIDC_ENABLED:
    urlpatterns.append(path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'))
    urlpatterns.append(path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'))

# Conditionally include OIDC URLs if OIDC_ENABLED is True
if settings.OIDC_ENABLED:
    urlpatterns.append(path('oidc/', include('mozilla_django_oidc.urls')))

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
