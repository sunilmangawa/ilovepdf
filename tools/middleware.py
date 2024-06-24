# tools/middleware.py
import os
from django.conf import settings

class CleanupFilesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cleanup_files = []

    def __call__(self, request):
        response = self.get_response(request)
        
        # Perform the cleanup after the response has been sent
        if hasattr(response, 'cleanup_files'):
            for file_path in response.cleanup_files:
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        return response

    def process_template_response(self, request, response):
        return response
