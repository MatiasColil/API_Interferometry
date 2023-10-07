from django.core.management import call_command
from django.conf import settings

class CheckSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        if not hasattr(settings, 'SESSION_CHECK_DONE'):
            call_command('check_session')
            settings.SESSION_CHECK_DONE = True

    def __call__(self, request):
        response = self.get_response(request)
        return response