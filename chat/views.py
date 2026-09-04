import asyncio
from decimal import Decimal
from django.http import StreamingHttpResponse
from django.db.models import Sum
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Conversation, Message, UsageLog
from .serializers import ConversationSerializer, MessageSerializer
from services.llm import get_servicio_llm, calcular_coste
from chat.schemas import UsageSummarySchema


class MessageRateThrottle(UserRateThrottle):
    scope = "messages"


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
    throttle_classes = [MessageRateThrottle]

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
            
            # 1. Obtener la respuesta que ahora devuelve un dict
            llm_res = servicio_llm.generar_respuesta(history)

            # 2. Guardar el mensaje del asistente
            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=llm_res["respuesta"],
            )

            # 3. Registrar el uso de tokens y calcular el coste
            coste = calcular_coste(
                llm_res["prompt_tokens"],
                llm_res["completion_tokens"]
            )
            UsageLog.objects.create(
                user=self.request.user,
                prompt_tokens=llm_res["prompt_tokens"],
                completion_tokens=llm_res["completion_tokens"],
                total_tokens=llm_res["total_tokens"],
                cost_usd=coste
            )


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
    throttle_classes = [MessageRateThrottle]

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

            # Crear el mensaje
            Message.objects.create(conversation=conversation, role="assistant", content=texto_completo)

            # Registrar la estimación de tokens en el modo Streaming
            total_prompt_chars = sum(len(m.get("content", "")) for m in history)
            p_tokens = max(1, total_prompt_chars // 4)
            c_tokens = max(1, len(texto_completo) // 4)
            coste = calcular_coste(p_tokens, c_tokens)

            UsageLog.objects.create(
                user=request.user,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=p_tokens + c_tokens,
                cost_usd=coste
            )

            yield "event: done\ndata: [DONE]\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class UsageSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        resumen = UsageLog.objects.filter(user=request.user).aggregate(
            t_prompt=Sum('prompt_tokens'),
            t_completion=Sum('completion_tokens'),
            t_total=Sum('total_tokens'),
            t_cost=Sum('cost_usd')
        )

        data = UsageSummarySchema(
            user_id=request.user.id,
            username=request.user.username,
            total_prompt_tokens=resumen['t_prompt'] or 0,
            total_completion_tokens=resumen['t_completion'] or 0,
            total_tokens=resumen['t_total'] or 0,
            total_cost_usd=resumen['t_cost'] or Decimal("0.000000")
        )

        return Response(data.model_dump())