from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Conversation(models.Model):
    id = models.BigAutoField(primary_key=True)  # ID autoincremental numérico (1, 2, 3...)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='conversations'
    )
    title = models.CharField(max_length=255, default='Nueva conversación')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} - {self.user.username}'


class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )

    id = models.BigAutoField(primary_key=True)  
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:30]}...'


class UsageLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='usage_logs'
    )
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'UsageLog(user={self.user.username}, tokens={self.total_tokens}, cost=${self.cost_usd})'