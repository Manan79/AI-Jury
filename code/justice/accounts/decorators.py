from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import EmailVerification

def email_verification_required(view_func):
    """
    Decorator that checks if user has verified their email.
    Redirects to verification page if not verified.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                verification = EmailVerification.objects.get(user=request.user)
                if not verification.is_verified:
                    messages.warning(
                        request, 
                        'Please verify your email address to access this feature.'
                    )
                    return redirect('profile')  # Redirect to profile where they can see verification status
            except EmailVerification.DoesNotExist:
                # If no verification record exists, create one and redirect
                EmailVerification.objects.create(user=request.user)
                messages.warning(
                    request, 
                    'Please verify your email address to access this feature.'
                )
                return redirect('profile')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def verified_required(view_func):
    """
    Combined decorator for login and email verification
    """
    return login_required(email_verification_required(view_func))