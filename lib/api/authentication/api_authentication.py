from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
import jwt

class WebToken:
    def __init__(self, user_id, course):
        self.user_id = user_id
        self.course = course

    def verify_user(self, user):
        return self.user_id == user.id

class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason

class SessionAuthentication:
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """
        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active:
            return None

        self.enforce_csrf(request)
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
            payload = jwt.decode(token, settings.SECRET_KEY) #TODO check if valid and handle bad signature
            web_token = WebToken(payload['uid'], payload['course'])
            if web_token.verify_user(user):
                return (user, web_token)
        
        # CSRF passed with authenticated user
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        check = CSRFCheck()
        # populates request.META['CSRF_COOKIE'], which is used in process_view()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)