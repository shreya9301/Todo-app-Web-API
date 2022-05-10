import threading


GLOBAL_REQUEST_STORAGE = threading.local()


class GlobalRequestMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        GLOBAL_REQUEST_STORAGE.request = request
        try:
            return self.get_response(request)
        finally:
            del GLOBAL_REQUEST_STORAGE.request

def get_request():
    try:
        return GLOBAL_REQUEST_STORAGE.request
    except AttributeError:
        return None
