from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from apps.messaging.models import Conversation, ConversationMember, Message, MessageAttachment, MessageStatus
from apps.users.models import User
from apps.audit.middleware import log_activity


def get_conversation_meta(convo, current_user):
    """Returns display metadata tailored to the current user (especially for direct chats)."""
    if not convo:
        return {
            'is_direct': False,
            'name': 'Conversation',
            'user_id': None,
            'avatar': '',
            'initials': 'TW',
            'icon': 'ri-group-line',
            'bg_color': '#e0f2fe',
            'icon_color': '#0284c7'
        }

    if convo.conversation_type == 'direct':
        other_user = convo.members.exclude(id=current_user.id).first() or current_user
        name = other_user.get_full_name() or other_user.email
        avatar = other_user.profile_picture.url if other_user.profile_picture else ''
        initials = (other_user.first_name[:1] + other_user.last_name[:1]) if other_user.first_name else 'U'
        return {
            'is_direct': True,
            'name': name,
            'user_id': other_user.id,
            'avatar': avatar,
            'initials': initials,
            'icon': 'ri-user-line',
            'bg_color': '#e0f2fe',
            'icon_color': '#0284c7',
        }

    name = convo.name or 'Conversation'
    name_lower = name.lower()
    if 'taskwave' in name_lower:
        meta = {'icon': 'ri-macbook-line', 'bg_color': '#cffafe', 'icon_color': '#0891b2'}
    elif 'design' in name_lower:
        meta = {'icon': 'ri-palette-line', 'bg_color': '#fce7f3', 'icon_color': '#db2777'}
    elif 'quality' in name_lower or 'qa' in name_lower:
        meta = {'icon': 'ri-shield-check-line', 'bg_color': '#dcfce7', 'icon_color': '#16a34a'}
    elif 'marketing' in name_lower:
        meta = {'icon': 'ri-megaphone-line', 'bg_color': '#fef3c7', 'icon_color': '#d97706'}
    elif 'hr' in name_lower:
        meta = {'icon': 'ri-team-line', 'bg_color': '#f3e8ff', 'icon_color': '#9333ea'}
    elif 'client' in name_lower:
        meta = {'icon': 'ri-chat-1-line', 'bg_color': '#ffe4e6', 'icon_color': '#e11d48'}
    elif 'general' in name_lower:
        meta = {'icon': 'ri-group-line', 'bg_color': '#f1f5f9', 'icon_color': '#64748b'}
    else:
        meta = {'icon': 'ri-group-line', 'bg_color': '#e0f2fe', 'icon_color': '#0284c7'}

    return {
        'is_direct': False,
        'name': name,
        'user_id': None,
        'avatar': '',
        'initials': 'GP',
        'icon': meta['icon'],
        'bg_color': meta['bg_color'],
        'icon_color': meta['icon_color'],
    }


@login_required
def inbox_view(request):
    user = request.user
    user_convos = Conversation.objects.filter(members=user).prefetch_related('members', 'messages', 'messages__sender').order_by('-updated_at')

    # If user doesn't have conversations yet, add them to existing public group conversations
    if not user_convos.exists():
        all_groups = Conversation.objects.filter(conversation_type='group')
        for g in all_groups:
            ConversationMember.objects.get_or_create(conversation=g, user=user)
        user_convos = Conversation.objects.filter(members=user).prefetch_related('members', 'messages', 'messages__sender').order_by('-updated_at')

    # Format conversations list for UI
    formatted_convos = []
    total_unread_all = 0
    for c in user_convos:
        last_msg = c.messages.order_by('-sent_at').first()
        meta = get_conversation_meta(c, user)
        unread_cnt = c.get_unread_count(user)
        total_unread_all += unread_cnt
        time_str = ''
        if last_msg:
            if last_msg.sent_at.date() == timezone.now().date():
                time_str = last_msg.sent_at.strftime('%I:%M %p')
            else:
                time_str = last_msg.sent_at.strftime('%d %b')

        formatted_convos.append({
            'id': c.id,
            'name': meta['name'],
            'type': c.conversation_type,
            'description': c.description,
            'members_count': c.members.count(),
            'last_message': last_msg.content if last_msg else 'No messages yet.',
            'last_sender': 'You' if last_msg and last_msg.sender_id == user.id else (last_msg.sender.first_name if last_msg and last_msg.sender else ''),
            'time_str': time_str,
            'unread_count': unread_cnt,
            'meta': meta,
        })

    # Determine active conversation
    active_convo = None
    convo_id = request.GET.get('c')
    if convo_id and convo_id.isdigit():
        active_convo = Conversation.objects.filter(id=int(convo_id), members=user).first()
    if not active_convo and user_convos.exists():
        active_convo = user_convos.first()

    messages_list = []
    active_members = []
    shared_files = []
    active_meta = None
    if active_convo:
        active_meta = get_conversation_meta(active_convo, user)
        # Mark messages in active conversation as read
        MessageStatus.objects.filter(message__conversation=active_convo, user=user, is_read=False).update(is_read=True, read_at=timezone.now())

        messages_list = active_convo.messages.select_related('sender').prefetch_related('attachments').order_by('sent_at')

        # Active members
        for m in active_convo.members.all().order_by('first_name'):
            is_admin = ConversationMember.objects.filter(conversation=active_convo, user=m, is_admin=True).exists()
            active_members.append({
                'user': m,
                'name': m.get_full_name() or m.email,
                'role': m.role.name if m.role else 'Member',
                'is_admin': is_admin,
                'status': 'Online' if m.id == user.id else ('Online' if m.is_active else 'Offline'),
                'avatar': m.profile_picture.url if m.profile_picture else '',
                'initials': (m.first_name[:1] + m.last_name[:1]) if m.first_name else 'U',
            })

        # Shared files
        for msg in messages_list:
            for att in msg.attachments.all():
                shared_files.append({
                    'name': att.original_filename,
                    'size': f"{att.file_size / 1024:.1f} KB" if att.file_size < 1024 * 1024 else f"{att.file_size / (1024*1024):.1f} MB",
                    'type': att.file_type or 'file',
                    'time_str': att.uploaded_at.strftime('%I:%M %p') if att.uploaded_at.date() == timezone.now().date() else att.uploaded_at.strftime('%d %b %Y'),
                })

    all_users = User.objects.filter(is_active=True).exclude(id=user.id).order_by('first_name')

    context = {
        'conversations': formatted_convos,
        'active_convo': active_convo,
        'active_convo_meta': active_meta,
        'messages_list': messages_list,
        'active_members': active_members,
        'shared_files': shared_files,
        'all_users': all_users,
        'total_unread': total_unread_all,
        'last_message_id': messages_list.last().id if messages_list.exists() else 0,
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def send_message_api(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    convo = get_object_or_404(Conversation, id=conversation_id, members=request.user)
    content = request.POST.get('content', '').strip()
    uploaded_file = request.FILES.get('attachment') or request.FILES.get('file')

    if not content and not uploaded_file:
        return JsonResponse({'error': 'Message content or file required'}, status=400)

    # Create real user message
    msg = Message.objects.create(
        conversation=convo,
        sender=request.user,
        content=content or (uploaded_file.name if uploaded_file else '')
    )

    # Sender has read their own message
    MessageStatus.objects.create(message=msg, user=request.user, is_read=True, read_at=timezone.now())

    # Create unread notification status for all other conversation members
    for member in convo.members.exclude(id=request.user.id):
        MessageStatus.objects.get_or_create(message=msg, user=member, defaults={'is_read': False})

    att_data = None
    if uploaded_file:
        ext = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else 'file'
        att = MessageAttachment.objects.create(
            message=msg,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=ext
        )
        att_data = {
            'name': att.original_filename,
            'size': f"{att.file_size / 1024:.1f} KB" if att.file_size < 1024 * 1024 else f"{att.file_size / (1024*1024):.1f} MB",
            'type': att.file_type,
            'url': att.file.url if att.file else '#',
        }

    convo.updated_at = timezone.now()
    convo.save()

    return JsonResponse({
        'success': True,
        'id': msg.id,
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.get_full_name() or msg.sender.email,
        'sender_avatar': msg.sender.profile_picture.url if msg.sender.profile_picture else '',
        'sender_initials': (msg.sender.first_name[:1] + msg.sender.last_name[:1]) if msg.sender.first_name else 'U',
        'content': msg.content,
        'sent_at': msg.sent_at.strftime('%I:%M %p'),
        'is_mine': True,
        'attachment': att_data,
    })


@login_required
def poll_messages_api(request, conversation_id):
    convo = get_object_or_404(Conversation, id=conversation_id, members=request.user)
    after_id = int(request.GET.get('after', 0))

    new_messages = convo.messages.filter(id__gt=after_id).select_related('sender').prefetch_related('attachments').order_by('sent_at')

    # Mark new messages in current active conversation as read
    if new_messages.exists():
        MessageStatus.objects.filter(message__in=new_messages, user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())

    msg_data = []
    max_id = after_id
    for m in new_messages:
        max_id = max(max_id, m.id)
        att_data = None
        first_att = m.attachments.first()
        if first_att:
            att_data = {
                'name': first_att.original_filename,
                'size': f"{first_att.file_size / 1024:.1f} KB" if first_att.file_size < 1024 * 1024 else f"{first_att.file_size / (1024*1024):.1f} MB",
                'type': first_att.file_type,
                'url': first_att.file.url if first_att.file else '#',
            }

        msg_data.append({
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'sender_avatar': m.sender.profile_picture.url if m.sender.profile_picture else '',
            'sender_initials': (m.sender.first_name[:1] + m.sender.last_name[:1]) if m.sender.first_name else 'U',
            'content': m.content,
            'sent_at': m.sent_at.strftime('%I:%M %p'),
            'is_mine': (m.sender.id == request.user.id),
            'attachment': att_data,
        })

    # Return sidebar updates for all conversations so badges and snippets update live
    convo_updates = []
    total_unread = 0
    for c in Conversation.objects.filter(members=request.user):
        last_m = c.messages.order_by('-sent_at').first()
        unread_cnt = c.get_unread_count(request.user)
        total_unread += unread_cnt
        time_str = ''
        if last_m:
            time_str = last_m.sent_at.strftime('%I:%M %p') if last_m.sent_at.date() == timezone.now().date() else last_m.sent_at.strftime('%d %b')
        convo_updates.append({
            'id': c.id,
            'unread_count': unread_cnt,
            'last_message': last_m.content if last_m else 'No messages yet.',
            'last_sender': 'You' if last_m and last_m.sender_id == request.user.id else (last_m.sender.first_name if last_m and last_m.sender else ''),
            'time_str': time_str,
        })

    return JsonResponse({
        'success': True,
        'messages': msg_data,
        'last_id': max_id,
        'count': len(msg_data),
        'convo_updates': convo_updates,
        'total_unread': total_unread,
    })


@login_required
def conversation_detail_api(request, conversation_id):
    convo = get_object_or_404(Conversation, id=conversation_id, members=request.user)
    
    # Mark messages as read for current user
    MessageStatus.objects.filter(message__conversation=convo, user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())

    messages_qs = convo.messages.select_related('sender').prefetch_related('attachments').order_by('sent_at')

    msg_list = []
    for m in messages_qs:
        first_att = m.attachments.first()
        att_data = None
        if first_att:
            att_data = {
                'name': first_att.original_filename,
                'size': f"{first_att.file_size / 1024:.1f} KB" if first_att.file_size < 1024 * 1024 else f"{first_att.file_size / (1024*1024):.1f} MB",
                'type': first_att.file_type,
                'url': first_att.file.url if first_att.file else '#',
            }
        msg_list.append({
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'sender_avatar': m.sender.profile_picture.url if m.sender.profile_picture else '',
            'sender_initials': (m.sender.first_name[:1] + m.sender.last_name[:1]) if m.sender.first_name else 'U',
            'content': m.content,
            'sent_at': m.sent_at.strftime('%I:%M %p'),
            'is_mine': (m.sender.id == request.user.id),
            'attachment': att_data,
        })

    members_list = []
    for m in convo.members.all().order_by('first_name'):
        is_admin = ConversationMember.objects.filter(conversation=convo, user=m, is_admin=True).exists()
        members_list.append({
            'id': m.id,
            'name': m.get_full_name() or m.email,
            'role': m.role.name if m.role else 'Member',
            'is_admin': is_admin,
            'status': 'Online' if m.id == request.user.id else ('Online' if m.is_active else 'Offline'),
            'avatar': m.profile_picture.url if m.profile_picture else '',
            'initials': (m.first_name[:1] + m.last_name[:1]) if m.first_name else 'U',
        })

    shared_files = []
    for msg in messages_qs:
        for att in msg.attachments.all():
            shared_files.append({
                'name': att.original_filename,
                'size': f"{att.file_size / 1024:.1f} KB" if att.file_size < 1024 * 1024 else f"{att.file_size / (1024*1024):.1f} MB",
                'type': att.file_type or 'file',
                'time_str': att.uploaded_at.strftime('%I:%M %p') if att.uploaded_at.date() == timezone.now().date() else att.uploaded_at.strftime('%d %b %Y'),
            })

    meta = get_conversation_meta(convo, request.user)

    return JsonResponse({
        'success': True,
        'conversation': {
            'id': convo.id,
            'name': meta['name'],
            'type': convo.conversation_type,
            'description': convo.description or ('Direct message with ' + meta['name'] if convo.conversation_type == 'direct' else 'Project discussions and development updates.'),
            'members_count': convo.members.count(),
            'created_at': convo.created_at.strftime('%d %b %Y'),
            'meta': meta,
        },
        'messages': msg_list,
        'members': members_list,
        'shared_files': shared_files,
        'last_id': msg_list[-1]['id'] if msg_list else 0
    })


@login_required
def start_direct_message(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user.id == request.user.id:
        return redirect('messaging:inbox')

    convo = Conversation.objects.filter(
        conversation_type='direct',
        members=request.user
    ).filter(members=target_user).first()

    if not convo:
        convo = Conversation.objects.create(
            conversation_type='direct',
            name=f"Direct: {request.user.first_name} & {target_user.first_name}",
            created_by=request.user
        )
        ConversationMember.objects.create(conversation=convo, user=request.user, is_admin=True)
        ConversationMember.objects.create(conversation=convo, user=target_user)

    return redirect(f'/messages/?c={convo.id}')


@login_required
def create_conversation_view(request):
    if request.method == 'POST':
        convo_type = request.POST.get('type', 'group')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        user_ids = request.POST.getlist('members')

        if convo_type == 'direct':
            target_user_id = request.POST.get('target_user')
            if target_user_id and target_user_id.isdigit():
                return start_direct_message(request, int(target_user_id))

        if not name:
            messages.error(request, 'Conversation name is required.')
            return redirect('messaging:inbox')

        convo = Conversation.objects.create(
            name=name,
            description=description,
            conversation_type='group',
            created_by=request.user
        )
        ConversationMember.objects.create(conversation=convo, user=request.user, is_admin=True)

        for uid in user_ids:
            if uid.isdigit():
                u = User.objects.filter(id=int(uid)).first()
                if u and u != request.user:
                    ConversationMember.objects.create(conversation=convo, user=u)

        messages.success(request, f'Conversation "{convo.name}" created!')
        return redirect(f'/messages/?c={convo.id}')

    return redirect('messaging:inbox')
