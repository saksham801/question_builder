import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class SupabaseJWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_token = request.COOKIES.get('sb:token')
        if not auth_token:
            auth_token = request.COOKIES.get('supabase-auth-token')
        if not auth_token:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]

        request.user_email = ''
        if auth_token and settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    auth_token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=['HS256'],
                    options={'verify_aud': False},
                )
                request.user_email = payload.get('email', '') or payload.get('user_email', '')
            except jwt.PyJWTError:
                request.user_email = ''
