from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_verification_email(user, verification_token, request):
    """
    Send email verification link to user
    """
    verification_url = request.build_absolute_uri(
        f'/accounts/verify-email/{verification_token.token}/'
    )
    
    subject = 'Verify your email address'
    
    # HTML email content
    html_message = render_to_string('accounts/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_welcome_email(user):
    """
    Send welcome email after successful verification
    """
    subject = 'Welcome to Our Site!'
    
    html_message = render_to_string('accounts/welcome_email.html', {
        'user': user,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )