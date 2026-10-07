"""
Messaging / Chat Models
"""
from django.db import models


class Conversation(models.Model):
    TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
    ]

    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    conversation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='direct')
    members = models.ManyToManyField(
        'users.User', through='ConversationMember', related_name='conversations'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='conversations'
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f'Conversation #{self.id}'

    def get_last_message(self):
        return self.messages.order_by('-sent_at').first()

    def get_unread_count(self, user):
        return self.messages.exclude(sender=user).filter(
            messagestatus__user=user, messagestatus__is_read=False
        ).count()


class ConversationMember(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'conversation_members'
        unique_together = ['conversation', 'user']


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )

    class Meta:
        db_table = 'messages'
        ordering = ['sent_at']

    def __str__(self):
        return f'Message from {self.sender} in {self.conversation}'


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    original_filename = models.CharField(max_length=500)
    file_size = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_attachments'


class MessageStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='statuses')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'message_statuses'
        unique_together = ['message', 'user']
