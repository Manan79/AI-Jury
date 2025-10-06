# views.py
import uuid
import json
import requests
import mimetypes
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from .models import ChatSession, ChatMessage
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from accounts.decorators import verified_required

# try:
#     from pdfminer.high_level import extract_text as pdf_extract_text
# except Exception:
#     pdf_extract_text = None

# try:
#     from PIL import Image
#     import pytesseract
# except Exception:
#     Image = None
#     pytesseract = None


# Your RAG service URL - update this with your AI team's endpoint
# Expected format: {"question": "string"} -> {"answer": "string", "status": "success"}
RAG_SERVICE_URL = "http://127.0.0.1:8000/query"  # Replace with your AI team's actual endpoint




def index(request):
    return render(request, "index.html")    

def services(request):
    return render(request, "services.html")

def about(request):
    return render(request, "about.html")


#@verified_required
def chat(request):
    return render(request, 'chat.html')

@require_http_methods(["GET"])
def get_chat_sessions(request):
    """Get all chat sessions for the sidebar"""
    sessions = ChatSession.objects.all().order_by('-created_at')
    sessions_data = []
    
    for session in sessions:
        sessions_data.append({
            'id': session.id,
            'title': session.title,
            'message_count': session.messages.count(),
            'last_activity': session.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({'sessions': sessions_data})

@require_http_methods(["GET"])
def get_chat_messages(request, session_id):
    """Get messages for a specific chat session"""
    try:
        session = ChatSession.objects.get(id=session_id)
        messages = session.messages.all().order_by('timestamp')
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'is_user': message.is_user,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'thinking_time': message.thinking_time
            })
        
        return JsonResponse({'messages': messages_data})
    
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Chat session not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Send message to RAG service and save response"""
    try:
        files = []
        extracted_texts = []

        if request.content_type and request.content_type.startswith('multipart/form-data'):
            # Multipart with possible attachments
            message_content = request.POST.get('message')
            session_id = request.POST.get('session_id')
            files = request.FILES.getlist('attachments')
        else:
            data = json.loads(request.body)
            message_content = data.get('message')
            session_id = data.get('session_id')
        
        if not message_content:
            return JsonResponse({'error': 'Message content required'}, status=400)
        
        # Get or create chat session
        if session_id:
            chat_session = ChatSession.objects.get(id=session_id)
        else:
            chat_session = ChatSession.objects.create(
                title=message_content[:50] + "..." if len(message_content) > 50 else message_content
            )
        
        # Extract text from attachments, if any
        if files:
            for f in files:
                name = getattr(f, 'name', 'attachment')
                content_type = getattr(f, 'content_type', None) or mimetypes.guess_type(name)[0]
                text_out = ''
                try:
                    if content_type == 'application/pdf' and pdf_extract_text:
                        # Read file into memory and extract
                        text_out = pdf_extract_text(f)
                    elif content_type and content_type.startswith('image/') and Image and pytesseract:
                        image = Image.open(f)
                        text_out = pytesseract.image_to_string(image)
                    else:
                        # Unsupported type or missing libs
                        text_out = ''
                except Exception as _e:
                    text_out = ''
                if text_out:
                    extracted_texts.append(f"\n\n[Extracted from {name}]\n{text_out.strip()}")

        # Augment message with extracted text
        if extracted_texts:
            message_content = (message_content or '').strip()
            attachments_blob = "\n".join(extracted_texts)
            if message_content:
                message_content = f"{message_content}\n\n[Attachments]\n{attachments_blob}"
            else:
                message_content = f"[Attachments]\n{attachments_blob}"

        # Save user message
        user_message = ChatMessage.objects.create(
            session=chat_session,
            content=message_content,
            is_user=True
        )
        
        # Call RAG service
        # Build brief chat history (last 10 messages before the current one)
        prior_messages = list(
            ChatMessage.objects.filter(session=chat_session)
            .exclude(id=user_message.id)
            .order_by('timestamp')
        )
        # Keep only the most recent 10
        prior_messages = prior_messages[-10:]

        history = [
            {
                'role': 'user' if m.is_user else 'assistant',
                'content': m.content,
            }
            for m in prior_messages
        ]

        # Simple payload format that matches your AI team's expected format
        rag_payload = {
            'question': message_content
        }
        
        try:
            # Make request to your RAG service
            response = requests.post(
                RAG_SERVICE_URL,
                json=rag_payload,
                timeout=30
            )
            response.raise_for_status()
            
            rag_response = response.json()
            # Handle your AI team's response format
            if rag_response.get('status') == 'success':
                ai_message_content = rag_response.get('answer', 'No response from AI service')
            else:
                ai_message_content = rag_response.get('error', 'No response from AI service')
            thinking_time = 0  # Your AI team doesn't provide thinking_time
            
        except requests.RequestException as e:
            ai_message_content = "Sorry, I'm having trouble connecting to the AI service. Please try again later."
            thinking_time = 0
            print(f"RAG service error: {e}")
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            session=chat_session,
            content=ai_message_content,
            is_user=False,
            thinking_time=thinking_time
        )
        
        return JsonResponse({
            'session_id': chat_session.id,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.strftime('%H:%M')
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.strftime('%H:%M'),
                'thinking_time': thinking_time
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_chat_session(request):
    """Create a new chat session"""
    chat_session = ChatSession.objects.create(title="New chat")
    
    return JsonResponse({
        'session_id': chat_session.id,
        'title': chat_session.title
    })

# Additional admin views for analytics

@staff_member_required
def chat_admin_dashboard(request):
    # Basic statistics
    total_sessions = ChatSession.objects.count()
    total_messages = ChatMessage.objects.count()
    user_messages = ChatMessage.objects.filter(is_user=True).count()
    ai_messages = ChatMessage.objects.filter(is_user=False).count()
    
    # Recent activity
    recent_sessions = ChatSession.objects.select_related().annotate(
        message_count=Count('messages')
    ).order_by('-updated_at')[:10]
    
    # Daily statistics for the last 7 days
    today = timezone.now().date()
    date_range = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    daily_stats = []
    for date in date_range:
        sessions_count = ChatSession.objects.filter(
            created_at__date=date
        ).count()
        messages_count = ChatMessage.objects.filter(
            timestamp__date=date
        ).count()
        daily_stats.append({
            'date': date,
            'sessions': sessions_count,
            'messages': messages_count
        })
    
    # Most active sessions
    most_active_sessions = ChatSession.objects.annotate(
        message_count=Count('messages')
    ).order_by('-message_count')[:10]
    
    # Average thinking time
    avg_thinking_time = ChatMessage.objects.filter(
        is_user=False, 
        thinking_time__isnull=False
    ).aggregate(avg_time=Avg('thinking_time'))['avg_time']
    
    context = {
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'user_messages': user_messages,
        'ai_messages': ai_messages,
        'recent_sessions': recent_sessions,
        'daily_stats': daily_stats,
        'most_active_sessions': most_active_sessions,
        'avg_thinking_time': round(avg_thinking_time, 2) if avg_thinking_time else 0,
    }
    
    return render(request, 'admin/chat_dashboard.html', context)

@staff_member_required
def session_analytics(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        # Session statistics
        total_messages = messages.count()
        user_messages = messages.filter(is_user=True).count()
        ai_messages = messages.filter(is_user=False).count()
        
        # Thinking time analysis
        ai_messages_with_time = messages.filter(is_user=False, thinking_time__isnull=False)
        avg_thinking_time = ai_messages_with_time.aggregate(avg=Avg('thinking_time'))['avg']
        
        # Message length analysis
        user_message_lengths = [len(msg.content) for msg in messages.filter(is_user=True)]
        ai_message_lengths = [len(msg.content) for msg in messages.filter(is_user=False)]
        
        context = {
            'session': session,
            'messages': messages,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'avg_thinking_time': round(avg_thinking_time, 2) if avg_thinking_time else 0,
            'avg_user_message_length': round(sum(user_message_lengths) / len(user_message_lengths)) if user_message_lengths else 0,
            'avg_ai_message_length': round(sum(ai_message_lengths) / len(ai_message_lengths)) if ai_message_lengths else 0,
        }
        
        return render(request, 'admin/session_analytics.html', context)
        
    except ChatSession.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Session not found')
        return redirect('chat_admin_dashboard')