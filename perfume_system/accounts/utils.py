from django.shortcuts import redirect
from django.urls import reverse

def get_role_based_redirect_url(user):
    """
    Determine the appropriate landing page based on user role.
    Returns the URL name for redirection.
    """
    user_roles = user.roles.all()
    
    # Check roles in order of priority
    if user_roles.filter(name='manager').exists():
        return 'dashboard:dashboard'
    elif user_roles.filter(name='rd').exists():
        return 'dashboard:formulations'
    elif user_roles.filter(name='qa').exists():
        return 'dashboard:formulations'
    else:
        # Fallback for users with no specific role
        return 'dashboard:dashboard'

def role_based_redirect(request):
    """
    Redirect to the appropriate page based on user role.
    Can be used as a view or within other views.
    """
    redirect_url = get_role_based_redirect_url(request.user)
    return redirect(reverse(redirect_url))

# Custom login required decorator that includes role-based redirection
from functools import wraps
from django.contrib.auth.decorators import login_required

def login_required_with_role(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is logged in
        if not request.user.is_authenticated:
            return login_required(view_func)(request, *args, **kwargs)
            
        # For dashboard view, redirect non-managers to their appropriate page
        if view_func.__name__ == 'dashboard_view' and not request.user.roles.filter(name='manager').exists():
            return role_based_redirect(request)
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view