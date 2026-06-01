from django.shortcuts import render
from django.http import HttpResponse


def inicio(request):
    context = {
        'agente_ia': 'OTTO',
    }
    return render(request, 'productos/inicio.html', context)