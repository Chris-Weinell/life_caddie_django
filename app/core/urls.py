"""
URLs for core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('account/', views.AccountUpdateView, name='account'),
]
