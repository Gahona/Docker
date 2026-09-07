from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet, MessageStreamView, UsageSummaryView

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    path('stream/', MessageStreamView.as_view(), name='message-stream'),
    path('usage/summary/', UsageSummaryView.as_view(), name='usage-summary'),
]