from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .utils import get_role_based_redirect_url

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'  # Adjust this to your login template path
    
    def get_success_url(self):
        # Use the role-based redirect function
        return reverse_lazy(get_role_based_redirect_url(self.request.user))