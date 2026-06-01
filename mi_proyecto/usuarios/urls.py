from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import UsuarioLoginView, register, perfil_usuario


urlpatterns = [
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),
    path('perfil/', perfil_usuario.as_view(), name='perfil'),
    path('register/', register, name='register'),
]
