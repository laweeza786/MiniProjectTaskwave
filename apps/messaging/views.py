from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from apps.messaging.models import Conversation, ConversationMember, Message, MessageStatus
from apps.users.models import User


@login_required
def inbox_view(request):
    user = request.user
    conversations = user.conversations.prefetch_related('members', 'messages').all()
    all_users = User.objects.filter(is_active=True).exclude(id=user.id)

    active_convo = None
    messages_list = []
    convo_id = request.GET.get('c')
    if convo_id:
        active_convo = get_object_or_404(Conversation, id=convo_id, members=user)
        messages_list = active_convo.messages.select_related('sender').order_by('sent_at')
    elif conversations.exists():
        active_convo = conversations.first()
        messages_list = active_convo.messages.select_related('sender').order_by('sent_at')

    context = {
        'conversations': conversations,
        'active_convo': active_convo,
        'messages_list': messages_list,
        'all_users': all_users,
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def start_direct_message(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    # Check if conversation already exists
    convo = Conversation.objects.filter(
        conversation_type='direct',
        members=request.user
    ).filter(members=target_user).first()

    if not convo:
        convo = Conversation.objects.create(
            conversation_type='direct',
            name=f'{request.user.get_short_name()} & {target_user.get_short_name()}',
            created_by=request.user
        )
        ConversationMember.objects.create(conversation=convo, user=request.user)
        ConversationMember.objects.create(conversation=convo, user=target_user)

    return redirect(f'/messages/?c={convo.id}')


@login_required
def send_message_api(request, conversation_id):
    if request.method == 'POST':
        convo = get_object_or_404(Conversation, id=conversation_id, members=request.user)
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=convo,
                sender=request.user,
                content=content
            )
            convo.updated_at = timezone.now()
            convo.save()

            return JsonResponse({
                'success': True,
                'id': msg.id,
                'sender': msg.sender.get_full_name(),
                'sender_initials': msg.sender.get_initials(),
                'content': msg.content,
                'sent_at': msg.sent_at.strftime('%H:%M'),
            })
    return JsonResponse({'error': 'Invalid'}, status=400)
