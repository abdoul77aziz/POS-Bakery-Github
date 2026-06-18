from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    """
    Décorateur personnalisé pour restreindre l'accès aux vues selon le rôle.
    Exemple d'utilisation : @role_required(allowed_roles=['admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied  # Renvoie une erreur 403 standard Django
        return _wrapped_view
    return decorator