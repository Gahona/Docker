from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet, MessageStreamView
from .views import UserUsageSummaryView

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('messages/stream/', MessageStreamView.as_view(), name='message-stream'),
    path('usage/summary/', UserUsageSummaryView.as_view(), name='usage-summary'),
    path('', include(router.urls)),
]