from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from accounts.models import Role
from accounts.utils import get_role_based_redirect_url

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    if request.user.is_superuser:
        return redirect('admin:index')
    
    # Use the role-based redirect function
    redirect_url = get_role_based_redirect_url(request.user)
    return redirect(redirect_url)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('allauth.urls')),
    path('', include('dashboard.urls')),
]