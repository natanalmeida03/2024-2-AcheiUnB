from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class BlockBannedUsersMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user

        if user.is_authenticated:
            profile = getattr(user, "profile", None)
            if profile and profile.is_banned:
                return JsonResponse({"error": "Usuário banido. Acesso negado."}, status=403)

        return None
