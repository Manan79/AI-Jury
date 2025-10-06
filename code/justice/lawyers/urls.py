from django.urls import path
from . import views

urlpatterns = [
    path('', views.lawyers_dashboard, name='lawyers_dashboard'),
    path('legal-letters/', views.legal_letters, name='legal_letters'),
    path('generate-letter/', views.generate_legal_letter, name='generate_legal_letter'),
    path('document-templates/', views.document_templates, name='document_templates'),
]