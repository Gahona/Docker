from rest_framework import serializers
from .models import Conversation, Message, UsageLog
from services.security import es_prompt_sospechoso


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_content(self, value):
        # Valida que el texto no contenga intentos de Prompt Injection
        if es_prompt_sospechoso(value):
            raise serializers.ValidationError(
                "Tu mensaje contiene palabras o instrucciones no permitidas por seguridad."
            )
        return value

    def validate_conversation(self, value):
        request = self.context.get('request')
        if value.user != request.user:
            raise serializers.ValidationError(
                "No tienes permiso para añadir mensajes a esta conversación."
            )
        return value


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UsageSchema(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    total_prompt_tokens = serializers.IntegerField()
    total_completion_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=6)