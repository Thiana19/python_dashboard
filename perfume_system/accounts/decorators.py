from functools import wraps
from django.shortcuts import redirect
from rolepermissions.checkers import has_permission

def role_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            if has_permission(request.user, permission):
                return view_func(request, *args, **kwargs)
            return redirect('dashboard')
        return _wrapped_view
    return decorator