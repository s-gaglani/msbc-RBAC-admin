from CommonAdminService.logger import get_logger
import time

class HTTPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger(__name__)

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        log_message = f"{request.method} {request.get_full_path()} - Status: {response.status_code} - Duration: {duration:.3f}s - IP: {request.META.get('REMOTE_ADDR', 'Unknown')}"
        
        self.logger.info(log_message)
        
        return response