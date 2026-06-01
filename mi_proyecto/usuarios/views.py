from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from .forms import PerfilUsuarioForm


class UsuarioLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'usuarios/register.html', {'form': form})


class perfil_usuario(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'usuarios/perfil.html'

    def get(self, request):
        form = PerfilUsuarioForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado exitosamente!')
            return redirect('perfil')
        return render(request, self.template_name, {'form': form})
