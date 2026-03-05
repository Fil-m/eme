from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from projects.views import ProjectPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/profiles/', include('profiles.urls')),
    path('api/settings/', include('system_settings.urls')),
    path('api/nav/', include('eme_nav.urls')),
    path('api/media/', include('eme_media.urls')),
    path('api/network/', include('network.urls')),
    path('api/clone/', include('clone_master.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/ai/', include('eme_ai.urls')),
    path('api/kb/', include('eme_kb.urls')),
    path('api/chat/', include('eme_chat.urls')),
    path('api/game/', include('park_adventures.urls')),
    # Simple project detail page
    path('p/<int:pk>/', ProjectPageView.as_view(), name='project-page'),
    # Entry point for the SPA
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
