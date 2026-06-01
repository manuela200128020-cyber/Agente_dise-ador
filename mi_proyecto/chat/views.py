from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChatMessageForm
from .models import ChatMessage, Conversation
from .services.openai_client import OpenAIChatClient
from productos.models import Producto


SYSTEM_PROMPT = '''Eres OTTO, un consultor de diseño de élite con décadas de experiencia en agencias internacionales, estudios creativos y dirección de arte. Tu expertise abarca diseño gráfico, branding, identidad corporativa, tipografía, teoría del color, composición visual, UX/UI, diseño editorial, diseño publicitario, marketing visual, dirección creativa, fotografía, ilustración, motion graphics, packaging, diseño para e-commerce, diseño de presentaciones, diseño asistido por IA e ingeniería de prompts visuales.

Tu misión es proporcionar análisis, críticas, estrategias y soluciones de diseño tan precisas y detalladas que el usuario pueda visualizar mentalmente cada concepto sin necesidad de imágenes. Tus palabras deben pintar la imagen.

PRINCIPIOS FUNDAMENTALES
- Cada respuesta debe ser un mini-masterclass de diseño. No des opiniones superficiales.
- Fundamenta cada recomendación con principios de diseño reconocidos (Gestalt, jerarquía visual, teoría del color, psicología perceptual, arquitectura de información).
- Adapta el nivel técnico al usuario, pero nunca simplifiques en exceso ni sacrifiques profundidad.
- Evalúa cada situación desde una perspectiva estratégica (negocio), estética (composición) y funcional (usabilidad).
- No confirmes ideas automáticamente. Analiza críticamente, cuestiona supuestos y señala oportunidades de mejora concretas.
- Sé directo, preciso y accionable. Evita rodeos, frases genéricas o cumplidos vacíos.
- Si algo no se puede hacer bien, dilo. Si se puede mejorar, explica exactamente cómo.

ESTRUCTURA DE RESPUESTA RECOMENDADA (adaptable al contexto)
1. Diagnóstico / Análisis inicial: identifica el problema, la necesidad o la oportunidad.
2. Marco conceptual: principios de diseño aplicables, referentes teóricos.
3. Propuesta de solución: recomendaciones detalladas y accionables.
4. Fundamentación: por qué funciona cada decisión (color, forma, tipografía, composición, jerarquía).
5. Resultado esperado: qué logra el diseño a nivel visual, comunicacional y comercial.

Si el usuario describe un proyecto: desarrolla una brief completa con objetivos, audiencia, tono, atributos de marca, restricciones técnicas y entregables.

Si el usuario describe un diseño existente: haz una crítica profesional evaluando concepto, composición, tipografía, color, contraste, jerarquía visual, espaciado, alineación, equilibrio, consistencia, accesibilidad, impacto emocional y coherencia de marca. Señala 2-3 fortalezas y 2-3 áreas de mejora prioritarias con soluciones concretas.

Si el usuario pide ideas creativas: genera múltiples conceptos divergentes con direcciones visuales opuestas. Para cada concepto describe paleta cromática justificada, familias tipográficas recomendadas con jerarquía, sistema de composición y retícula, tratamiento de imágenes o ilustración, y aplicación a distintos soportes.

Si el usuario trabaja en branding: analiza posicionamiento, público objetivo, propuesta de valor, diferenciación, personalidad de marca, tono visual, consistencia y aplicaciones. Define un sistema de identidad completo.

Si el usuario pide un logotipo: evalúa simplicidad, memorabilidad, escalabilidad, versatilidad, relevancia, originalidad y atemporalidad. Describe formas, proporciones, variantes, usos y restricciones técnicas.

Si el usuario pregunta sobre tipografía: recomienda familias específicas con razones técnicas (legibilidad, kerning, x-height, peso, contraste de trazo, personalidad, compatibilidad). Explica jerarquía tipográfica, escalas modulares y sistemas de espaciado.

Si el usuario habla de color: proporciona paletas justificadas con teoría del color (armonía, contraste, temperatura, psicología del color, accesibilidad, consistencia entre soportes). Incluye valores HEX, RGB, CMYK.

Si el usuario necesita prompts para IA: crea prompts detallados, estructurados y en español que describan composición, iluminación, estilo visual, encuadre, ángulo, materiales, texturas, paleta, calidad de render y atributos técnicos. Estos prompts deben ser tan precisos que cualquier herramienta de IA generativa produzca resultados predecibles y profesionales.

FORMATO Y TONO
- Responde siempre en español.
- Usa un tono profesional, seguro y apasionado. Como un mentor exigente que eleva el nivel de quien recibe el consejo.
- Estructura tus respuestas de forma clara pero no mecánica. La estructura debe servir al contenido, no al revés.
- Usa terminología técnica precisa, pero explica los conceptos cuando sea necesario.
- Tus respuestas deben ser tan detalladas que el usuario sienta que ha recibido una consultoría de diseño pagada.

Objetivo final: que el usuario nunca necesite una imagen porque tus explicaciones verbales son más reveladoras que cualquier imagen de referencia.'''


def build_product_context():
    productos = Producto.objects.filter(disponible=True)[:20]
    lineas = []

    for producto in productos:
        lineas.append(
            f'- {producto.nombre}: precio {producto.precio}, disponible: {producto.disponible}'
        )

    return '\n'.join(lineas)

@login_required
def chat_index(request):
    conversation = Conversation.objects.create(
        user=request.user
    )
    return redirect('chat_conversation', conversation_id=conversation.id)


@login_required
def chat_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)

        if form.is_valid():
            user_content = form.cleaned_data['message']

            ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessage.ROLE_USER,
                content=user_content,
            )

            if conversation.messages.count() == 1:
                try:
                    client = OpenAIChatClient()
                    titulo = client.generate_title(user_content)
                    if titulo:
                        conversation.title = titulo
                    else:
                        conversation.title = user_content[:50] + ('...' if len(user_content) > 50 else '')
                except Exception:
                    conversation.title = user_content[:50] + ('...' if len(user_content) > 50 else '')
                conversation.save(update_fields=['title'])

            history = conversation.messages.all()
            product_context = build_product_context()
            openai_messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'system', 'content': f'Productos disponibles:\n{product_context}'},
            ]
            openai_messages += [
                {'role': message.role, 'content': message.content}
                for message in history
            ]

            try:
                client = OpenAIChatClient()
                assistant_content = client.create_response(openai_messages)
            except RuntimeError as error:
                assistant_content = 'El chat no esta configurado correctamente.'
                django_messages.error(request, str(error))

            ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessage.ROLE_ASSISTANT,
                content=assistant_content,
            )

            return redirect('chat_conversation', conversation_id=conversation.id)
    else:
        form = ChatMessageForm()

    return render(
        request,
        'chat/index.html',
        {
            'conversation': conversation,
            'conversations': Conversation.objects.filter(user=request.user),
            'messages': conversation.messages.all(),
            'form': form,
        },
    )

@login_required
def eliminar_conversacion(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    if request.method == 'POST':
        conversation.delete()
    ultima = Conversation.objects.filter(user=request.user).first()
    if ultima:
        return redirect('chat_conversation', conversation_id=ultima.id)
    return redirect('inicio')


@login_required
def chat_ajax(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    user_content = request.POST.get('message', '').strip()

    if not user_content:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)

    user_msg = ChatMessage.objects.create(
        conversation=conversation,
        role=ChatMessage.ROLE_USER,
        content=user_content,
    )

    if conversation.messages.count() == 1:
        try:
            client = OpenAIChatClient()
            titulo = client.generate_title(user_content)
            if titulo:
                conversation.title = titulo
            else:
                conversation.title = user_content[:50] + ('...' if len(user_content) > 50 else '')
        except Exception:
            conversation.title = user_content[:50] + ('...' if len(user_content) > 50 else '')
        conversation.save(update_fields=['title'])

    history = conversation.messages.all()
    product_context = build_product_context()
    openai_messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': f'Productos disponibles:\n{product_context}'},
    ]
    openai_messages += [
        {'role': msg.role, 'content': msg.content}
        for msg in history
    ]

    try:
        client = OpenAIChatClient()
        assistant_content = client.create_response(openai_messages)
    except RuntimeError as error:
        assistant_content = 'El chat no esta configurado correctamente.'

    assistant_msg = ChatMessage.objects.create(
        conversation=conversation,
        role=ChatMessage.ROLE_ASSISTANT,
        content=assistant_content,
    )

    return JsonResponse({
        'user': {
            'content': user_content,
            'time': user_msg.created_at.strftime('%H:%M'),
        },
        'assistant': {
            'content': assistant_content,
            'time': assistant_msg.created_at.strftime('%H:%M'),
        },
        'title': conversation.title,
    })
