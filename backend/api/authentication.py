from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF enforcement for REST API endpoints.
    Allows stateless API requests (from Vite frontend, curl, DRF browsable UI)
    to succeed without requiring Django session CSRF cookies.
    """
    def enforce_csrf(self, request):
        return
