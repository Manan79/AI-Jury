from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['id', 'timestamp', 'thinking_time']
    fields = ['content', 'is_user', 'timestamp', 'thinking_time']
    ordering = ['timestamp']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 
        'title', 
        'message_count', 
        'created_at', 
        'updated_at', 
        'session_actions'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'message_count_display']
    inlines = [ChatMessageInline]
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'title', 'created_at', 'updated_at', 'message_count_display')
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'Session ID'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def message_count_display(self, obj):
        return obj.messages.count()
    message_count_display.short_description = 'Total Messages'

    def session_actions(self, obj):
        return format_html(
            '<a href="/admin/search_app/chatsession/{}/change/" class="button">View</a> '
            '<a href="/admin/search_app/chatsession/{}/delete/" class="button" style="color: red; margin-left: 10px;">Delete</a>',
            obj.id, obj.id
        )
    session_actions.short_description = 'Actions'
    session_actions.allow_tags = True

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id_short',
        'session_short',
        'content_preview',
        'is_user_display',
        'thinking_time',
        'timestamp'
    ]
    list_filter = ['is_user', 'timestamp', 'session']
    search_fields = ['content', 'session__title', 'session__id']
    readonly_fields = ['id', 'timestamp', 'session_link']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('id', 'session_link', 'content', 'is_user', 'thinking_time', 'timestamp')
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'Message ID'

    def session_short(self, obj):
        return f"{obj.session.title[:20]}..." if len(obj.session.title) > 20 else obj.session.title
    session_short.short_description = 'Session'

    def content_preview(self, obj):
        preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = 'Content'

    def is_user_display(self, obj):
        if obj.is_user:
            return format_html('<span style="color: green;">👤 User</span>')
        else:
            return format_html('<span style="color: blue;">🤖 AI</span>')
    is_user_display.short_description = 'Sender'

    def session_link(self, obj):
        return format_html(
            '<a href="/admin/search_app/chatsession/{}/change/">{}</a>',
            obj.session.id, obj.session.title
        )
    session_link.short_description = 'Session'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False