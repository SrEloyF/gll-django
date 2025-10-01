import re
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login

class LoginRequiredMiddleware:
    """Middleware que obliga a login salvo las rutas en LOGIN_EXEMPT_URLS."""
    def __init__(self, get_response):
        self.get_response = get_response
        # compila los patrones
        exempt = getattr(settings, 'LOGIN_EXEMPT_URLS', [])
        # asegúrate de incluir la url de login
        login_url = settings.LOGIN_URL.lstrip('/')
        self.exempt_urls = [re.compile(pattern) for pattern in exempt]
        # incluir login_url si no está
        self.exempt_urls.append(re.compile(login_url))

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # `request.user` debe existir (AuthenticationMiddleware debe estar activado)
        if not hasattr(request, 'user'):
            return None

        path = request.path_info.lstrip('/')
        # si no autenticado y no está en la lista exenta -> redirige a login
        if not request.user.is_authenticated:
            if not any(m.match(path) for m in self.exempt_urls):
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        return None