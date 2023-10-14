from django.core.management import call_command
from django.conf import settings

class CheckUserAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        if not hasattr(settings, 'ADMIN_CHECK_DONE'):
            call_command('check_admin')
            settings.ADMIN_CHECK_DONE = True

    def __call__(self, request):
        response = self.get_response(request)
        return response