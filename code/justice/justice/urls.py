
from django.contrib import admin
from django.urls import path,include
from search_app import views
from django.conf import settings
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('search_app.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')), 
     path('lawyers/', include('lawyers.urls')),
]
