from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <-- Added this
from django.conf.urls.static import static # <-- Added this

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')), # This connects your store app
]

# Tell Django how to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)