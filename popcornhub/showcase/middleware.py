from django.utils.deprecation import MiddlewareMixin
from .models import UserVisit

class UserVisitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip logging for static and media files
        if any(path in request.path for path in ['/static/', '/media/', '/admin/static/']):
            return None

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Create visit log
        UserVisit.objects.create(
            user=request.user if request.user.is_authenticated else None,
            path=request.path,
            method=request.method,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        ) 