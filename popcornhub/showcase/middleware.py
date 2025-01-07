from .models import UserVisit

import logging


logger = logging.getLogger(__name__)


class UserVisitMiddleware:
    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)
        # Записываем информацию о посещении
        try:
            UserVisit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                path=request.path,
                method=request.method,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            # Логируем в файл
            log_message = (
                f'User: {request.user if request.user.is_authenticated else "Anonymous"} | '
                f'Path: {request.path} | '
                f'Method: {request.method} | '
                f'IP: {self.get_client_ip(request)} | '
                f'User Agent: {request.META.get("HTTP_USER_AGENT", "")}'
            )
            logger.info(log_message)
        except Exception as e:
            logger.error(f'Error logging user visit: {str(e)}')
        return response

    def get_client_ip(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
