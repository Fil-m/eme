import traceback
import sys

class ExceptionLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        print(f"DEBUG MIDDLEWARE CAUGHT: {type(exception).__name__}: {str(exception)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None
