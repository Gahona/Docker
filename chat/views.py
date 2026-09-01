from rest_framework import viewsets, permissions
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from services.llm import get_servicio_llm

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(conversation__user=self.request.user)
    
    def perform_create(self, serializer):
        message = serializer.save()
        
        if message.role == "user":
            conversation = message.conversation
            history = [
                {"role": m.role, "content": m.content}
                for m in conversation.messages.all()
            ]
            servicio_llm = get_servicio_llm()
            reply_text = servicio_llm.generar_respuesta(history)

            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=reply_text,
            )
            