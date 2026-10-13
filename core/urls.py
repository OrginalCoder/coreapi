"""URL routing for CoreAPI application."""

from django.urls import path
from .views import index_view, docs_view, ChatAPIView

urlpatterns = [
    path('', index_view, name='index'),
    path('docs/', docs_view, name='docs'),
    path('api/v1/chat/', ChatAPIView.as_view(), name='api-chat'),
]
