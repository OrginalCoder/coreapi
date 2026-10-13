"""Root URL configuration for CoreAPI."""

from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # OpenAPI Schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Core application URLs (website & API)
    path('', include('core.urls')),
]

# Custom error handlers
handler404 = 'core.views.custom_404_view'
