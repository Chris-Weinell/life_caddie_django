"""
Views for core app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from core.admin import UserCreationForm


class SignUpView(CreateView):
    """Sign Up View for New Users."""
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'core/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sign Up'
        return context


@login_required
def AccountUpdateView(request):
    """User Account View with Reset Password Link."""

    context = {
        'title': 'User Account'
    }

    return render(request, 'core/account.html', context=context)


@login_required
def dashboard(request):
    """Life Caddie complete application Dashboard"""
    # This page is currently not used in v1.
    return render(request, 'core/dashboard.html')
