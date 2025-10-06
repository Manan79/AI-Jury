from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from .models import EmailVerification
from .utils import send_verification_email, send_welcome_email

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create email verification token
            verification_token = EmailVerification.objects.create(user=user)
            
            # Send verification email
            send_verification_email(user, verification_token, request)
            
            messages.success(
                request, 
                'Account created successfully! Please check your email to verify your account.'
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def verify_email(request, token):
    """
    Verify user's email address using the token
    """
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if verification.is_token_expired():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('resend_verification')
        
        if not verification.is_verified:
            verification.is_verified = True
            verification.save()
            
            # Activate the user account
            user = verification.user
            user.is_active = True
            user.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.info(request, 'Email is already verified.')
        
        return redirect('login')
    
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('signup')

def resend_verification(request):
    """
    Resend verification email
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            verification, created = EmailVerification.objects.get_or_create(user=user)
            
            if verification.is_verified:
                messages.info(request, 'Email is already verified.')
                return redirect('login')
            
            # Update token if expired
            if verification.is_token_expired():
                verification.delete()
                verification = EmailVerification.objects.create(user=user)
            
            send_verification_email(user, verification, request)
            messages.success(request, 'Verification email sent! Please check your inbox.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/resend_verification.html')

@login_required
def profile(request):
    try:
        email_verification = EmailVerification.objects.get(user=request.user)
        is_verified = email_verification.is_verified
    except EmailVerification.DoesNotExist:
        is_verified = False
        # Create verification record if it doesn't exist
        EmailVerification.objects.create(user=request.user)
    
    return render(request, 'accounts/profile.html', {
        'is_verified': is_verified,
        'verification': email_verification
    })