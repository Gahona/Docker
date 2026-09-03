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


import asyncio
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response


def async_generator_a_sync(async_gen):
    """Convierte un generador async en uno síncrono, ejecutándolo trozo a trozo."""
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
    finally:
        loop.close()


class MessageStreamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation")
        content = request.data.get("content")

        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversación no encontrada"}, status=404)

        Message.objects.create(conversation=conversation, role="user", content=content)

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.all()
        ]

        servicio_llm = get_servicio_llm()

        def event_stream():
            texto_completo = ""
            async_gen = servicio_llm.generar_respuesta_stream(history)
            for trozo in async_generator_a_sync(async_gen):
                texto_completo += trozo
                yield f"data: {trozo}\n\n"

            Message.objects.create(conversation=conversation, role="assistant", content=texto_completo)
            yield "event: done\ndata: [DONE]\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response