from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store import views

urlpatterns = [
    # 1. Standard Database Admin
    path('admin/', admin.site.urls),

    # 2. Staff Dashboard Login
    # We use login_view because it handles both staff and customers
    path('dashboard/login/', views.login_view, name='staff_login'),
path('delivery/update/', views.delivery_agent_update, name='delivery_agent_update'),
    # 3. Main Storefront URLs
    path('', include('store.urls')),
]

# 4. Media & Static File Serving (Only in Debug mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)