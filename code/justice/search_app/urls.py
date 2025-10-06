from django.contrib import admin
from django.urls import path
from search_app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    # Main pages
    path('', views.index, name='index'),
    path('services', views.services, name='services'),
    path('about', views.about, name='about'),
    path('chat', views.chat, name='chat'),
    path('chat/', views.chat),
    path('api/chat/sessions/', views.get_chat_sessions, name='get_chat_sessions'),
    path('api/chat/sessions/create/', views.create_chat_session, name='create_chat_session'),
    path('api/chat/sessions/<uuid:session_id>/messages/', views.get_chat_messages, name='get_chat_messages'),
    path('api/chat/send/', views.send_message, name='send_message'),
    path('admin/chat/dashboard/', views.chat_admin_dashboard, name='chat_admin_dashboard'),
    path('admin/chat/session/<uuid:session_id>/analytics/', views.session_analytics, name='session_analytics'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)